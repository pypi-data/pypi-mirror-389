"""
Transform data from the bronze to the silver layer.

The silver layer holds a single record per preprint and source:
1) For each source, the latest version of each preprint is selected from the bronze layer.
2) The relevant fields are extracted and normalized into a common schema: doi, title, ...
3) Invalid records are skipped (e.g., missing DOI).
"""

from collections.abc import Callable
from datetime import date, datetime
from logging import getLogger
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from tqdm import tqdm, trange

from pub_lake.models.schema import (
    BronzeBiorxivPreprint,
    BronzeOpenAlexPreprint,
    SilverPreprint,
    Source,
)

logger = getLogger(__name__)


def preprints_bronze_to_silver(db: Session) -> None:
    """Transform raw data in bronze layer into normalized silver layer."""
    logger.info("bronze → silver")
    _biorxiv_preprints_to_silver_preprints(db)
    _openalex_preprints_to_silver_preprints(db)


class SkipBronzePreprint(Exception):
    """Indicates that a bronze preprint should be skipped during transformation."""

    pass


def _openalex_preprints_to_silver_preprints(db: Session) -> None:
    def latest_bronze_key(rp: BronzeOpenAlexPreprint) -> str:
        return rp.raw_json["updated_date"]

    def update_sp(sp: SilverPreprint, op: BronzeOpenAlexPreprint) -> None:
        w = op.raw_json

        doi_with_scheme = w.get("doi")
        if not doi_with_scheme:
            raise SkipBronzePreprint(f"OpenAlex preprint {op.source_id} has no DOI; skipping")
        doi = doi_with_scheme.removeprefix("https://doi.org/")  # normalize DOI to bare form
        if sp.doi != doi:
            sp.doi = doi

        title = w.get("title") or ""
        if sp.title != title:
            sp.title = title

        inv_index = w.get("abstract_inverted_index")
        abstract = _reverse_inverted_index(inv_index) if inv_index else ""
        if sp.abstract != abstract:
            sp.abstract = abstract

        publish_date = _parse_date(w["publication_date"])
        if sp.publish_date != publish_date:
            sp.publish_date = publish_date

        openalex_topics_json = w.get("topics") or None
        if (pt := w.get("primary_topic")) is not None:
            if openalex_topics_json is None:
                openalex_topics_json = [pt]
            elif pt["id"] not in set(t["id"] for t in openalex_topics_json):
                openalex_topics_json.insert(0, pt)  # first = primary
            else:
                # move primary topic to first position
                openalex_topics_json = list(
                    sorted(
                        openalex_topics_json,
                        key=lambda t: 0 if t["id"] == pt["id"] else 1,
                    )
                )
        if sp.openalex_topics != openalex_topics_json:
            sp.openalex_topics = openalex_topics_json

        update_ts = _parse_datetime(w["updated_date"])
        if sp.update_ts != update_ts:
            sp.update_ts = update_ts

    _bronze_to_silver_preprints(
        db,
        ModelClass=BronzeOpenAlexPreprint,
        source=Source.OPENALEX,
        latest_bronze_key=latest_bronze_key,
        update_sp=update_sp,
    )


def _reverse_inverted_index(inv_idx: dict[str, list[int]]) -> str:
    """Convert an inverted index back into a string."""
    # Create a list to hold the words in their original order
    words = [""] * (max(pos for positions in inv_idx.values() for pos in positions) + 1)
    for word, positions in inv_idx.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)


def _biorxiv_preprints_to_silver_preprints(db: Session) -> None:
    def latest_bronze_key(rp: BronzeBiorxivPreprint) -> str:
        return rp.raw_json["version"]

    def update_sp(sp: SilverPreprint, bp: BronzeBiorxivPreprint) -> None:
        r = bp.raw_json
        if sp.doi != r["doi"]:
            sp.doi = r["doi"]
        if sp.title != r["title"]:
            sp.title = r["title"]
        if sp.abstract != r["abstract"]:
            sp.abstract = r["abstract"]
        publish_date = _parse_date(r["date"])
        if sp.publish_date != publish_date:
            sp.publish_date = publish_date
        if sp.biorxiv_category != r["category"]:
            sp.biorxiv_category = r["category"]
        if sp.version != r["version"]:
            sp.version = r["version"]

    _bronze_to_silver_preprints(
        db,
        ModelClass=BronzeBiorxivPreprint,
        source=Source.BIORXIV,
        latest_bronze_key=latest_bronze_key,
        update_sp=update_sp,
    )


# type to represent either BronzeBiorxivPreprint or BronzeOpenAlexPreprint
BronzePreprint = BronzeBiorxivPreprint | BronzeOpenAlexPreprint


def _bronze_to_silver_preprints(
    db: Session,
    ModelClass: BronzePreprint,
    source: Source,
    latest_bronze_key: Callable[[BronzePreprint], Any],
    update_sp: Callable[[SilverPreprint, BronzePreprint], None],
) -> None:
    # grab the source_ids of all new bronze preprints - existing ones are either linked to a silver preprint or skipped
    new_sids = db.scalars(
        select(ModelClass.source_id.distinct()).where(
            ModelClass.silver_preprint_id.is_(None),
            ModelClass.skipped.is_(False),
        )
    ).all()
    logger.info("Transforming %d %s bronze preprints to silver", len(new_sids), source.value)
    # delete all existing silver preprints for these source_ids to force re-processing of gold preprints

    sids_batch_size = 1000
    for i in trange(0, len(new_sids), sids_batch_size, desc=f"{source.value} ➜ silver"):
        batch = new_sids[i : i + sids_batch_size]

        db.execute(
            delete(SilverPreprint).where(
                SilverPreprint.source == source,
                SilverPreprint.source_id.in_(batch),
            )
        )

        for sid in tqdm(batch, desc=f"{source.value} ➜ silver batch", disable=True):
            bronze_preprints = db.scalars(
                select(ModelClass).where(ModelClass.source_id == sid).order_by(ModelClass.id)
            ).all()
            latest_bronze = sorted(bronze_preprints, key=latest_bronze_key, reverse=True)[0]

            sp = SilverPreprint(
                source=source,
                source_id=sid,
            )
            skipped = False
            try:
                update_sp(sp, latest_bronze)
                db.add(sp)
            except SkipBronzePreprint:
                skipped = True

            # add provenance markers
            for rp in bronze_preprints:
                if skipped:
                    rp.skipped = True
                else:
                    rp.silver_preprint = sp

        db.commit()


def _parse_date(date_str: str, format: str = "%Y-%m-%d") -> date:
    """Parse date string into date object."""
    return _parse_datetime(date_str, format=format).date()


def _parse_datetime(datetime_str: str, format: str = "%Y-%m-%dT%H:%M:%S.%f") -> datetime:
    """Parse datetime string into datetime object."""
    return datetime.strptime(datetime_str, format)
