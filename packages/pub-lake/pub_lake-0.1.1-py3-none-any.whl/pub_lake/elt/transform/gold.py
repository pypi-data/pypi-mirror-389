"""
Transform data from silver -> gold layer.

The gold layer holds a single canonical record per preprint:
1) bioRxiv is used as the canonical source - no bioRxiv preprint, no gold preprint.
2) all common fields are taken from the bioRxiv silver preprint: doi, title, abstract, ...
3) OpenAlex is used as a secondary source for topics.
"""

from logging import getLogger

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from tqdm import tqdm, trange

from pub_lake.models.schema import (
    Category,
    Preprint,
    SilverPreprint,
    Source,
    Topic,
    preprint_topic,
)

logger = getLogger(__name__)


def preprints_silver_to_gold(db: Session) -> None:
    logger.info("silver → gold")
    _silver_preprints_to_gold_preprints(db)


def _silver_preprints_to_gold_preprints(db: Session) -> None:
    # grab DOIs for all new silver preprints - those not linked to a gold preprint and not skipped
    new_dois = db.scalars(
        select(SilverPreprint.doi.distinct()).where(
            SilverPreprint.preprint_id.is_(None),
            SilverPreprint.skipped.is_(False),
        )
    ).all()

    logger.info("Found %d new DOIs in silver to process into gold", len(new_dois))

    # go through all new DOIs and create gold preprints
    batch_size = 1000
    for i in trange(0, len(new_dois), batch_size, desc="silver ➜ gold"):
        batch = new_dois[i : i + batch_size]

        # delete the existing gold preprint for these DOIs
        db.execute(delete(Preprint).where(Preprint.canonical_doi.in_(batch)))

        for doi in tqdm(batch, desc="silver ➜ gold batch", disable=True):
            silver_preprints = db.scalars(select(SilverPreprint).where(SilverPreprint.doi == doi)).all()

            sp_by_source = {}
            for sp in silver_preprints:
                sp_by_source.setdefault(sp.source, []).append(sp)

            # bioRxiv is the canonical source; skip if not present
            sps_bx = sp_by_source.get(Source.BIORXIV, [])
            if not sps_bx:
                for sp in silver_preprints:
                    sp.skipped = True
                continue

            assert len(sps_bx) == 1, f"Expected exactly one silver preprint from biorxiv per DOI: {doi}"
            sp_bx = sps_bx[0]
            category = _get_or_create_category(db, sp_bx.biorxiv_category)

            gp = Preprint(
                canonical_doi=sp_bx.doi,
                canonical_version=sp_bx.version,
                canonical_title=sp_bx.title,
                canonical_abstract=sp_bx.abstract,
                canonical_publish_date=sp_bx.publish_date,
                category=category,
            )
            db.add(gp)
            sp_bx.preprint = gp

            # use the OpenAlex silver preprint as secondary source for OpenAlex data
            sps_oa = sp_by_source.get(Source.OPENALEX, [])
            if len(sps_oa) == 0:
                sp_oa = None
            elif len(sps_oa) == 1:
                sp_oa = sps_oa[0]
            else:
                logger.warning(
                    "Multiple OpenAlex silver preprints for DOI %s; using the latest by update_ts with topic metadata",
                    doi,
                )
                sp_oa = max(
                    filter(lambda sp: sp.openalex_topics, sps_oa), key=lambda sp: sp.update_ts or sp.publish_date
                )

            if sp_oa:
                # OpenAlex topics (many-to-many, with 1 primary)
                for idx, t in enumerate(sp_oa.openalex_topics or []):
                    topic = _get_or_create_topic(db, t)
                    # insert or update bridge row with score & primary flag
                    stmt = (
                        preprint_topic.insert()
                        .prefix_with("OR IGNORE")
                        .values(
                            preprint_id=gp.id,
                            topic_id=topic.id,
                            is_primary=(idx == 0),
                            score=t.get("score"),
                        )
                    )
                    db.execute(stmt)
                sp_oa.preprint = gp

        db.commit()


def _get_or_create_category(db: Session, name: str) -> Category:
    cat = db.scalar(select(Category).where(Category.name == name))
    if cat:
        return cat
    cat = Category(name=name)
    db.add(cat)
    db.flush([cat])
    return cat


def _get_topic_by_oa_id(db: Session, oa_topic_id: str) -> Topic | None:
    return db.scalar(select(Topic).where(Topic.oa_topic_id == oa_topic_id))


def _get_or_create_topic(db: Session, t: dict) -> Topic:
    """t is the topic object straight from OpenAlex"""
    topic = _get_topic_by_oa_id(db, t["id"])
    if topic:
        return topic

    topic = Topic(
        oa_topic_id=t["id"],
        display_name=t["display_name"],
        oa_subfield_id=t["subfield"]["id"],
        subfield_display_name=t["subfield"]["display_name"],
        oa_field_id=t["field"]["id"],
        field_display_name=t["field"]["display_name"],
        oa_domain_id=t["domain"]["id"],
        domain_display_name=t["domain"]["display_name"],
    )
    db.add(topic)
    db.flush([topic])
    return topic
