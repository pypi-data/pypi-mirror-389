"""
Load data from external sources into the bronze layer.

The bronze layer stores raw JSON data fetched from external sources, exactly as received.
This enables:
1) re-processing of data if extraction logic changes without needing to re-fetch from the sources.
2) tracing of data provenance back to the original source.

The module also tracks which date intervals have been previously ingested for each source to avoid duplicate ingestion.
As of yet there is no mechanism to re-ingest data for intervals that have already been processed.
"""

from datetime import date, timedelta
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tqdm import tqdm

from pub_lake.elt.extract.biorxiv import fetch_biorxiv_preprints as fetch_biorxiv
from pub_lake.elt.extract.openalex import fetch_biorxiv_preprints as fetch_biorxiv_from_oa
from pub_lake.models.preprints import DateInterval
from pub_lake.models.schema import (
    BronzeBiorxivPreprint,
    BronzeOpenAlexPreprint,
    IntervalIngest,
    Source,
)

logger = getLogger(__name__)


def ingest_preprints_bronze(interval: DateInterval, source: Source, db: Session) -> None:
    """
    Ingest preprints in the interval from a specific source into the bronze layer.

    Parameters
    ----------
    interval : DateInterval
        Date interval to ingest.
    source : Source
        Source of the preprints to ingest.
    db : sqlalchemy.orm.Session
        Database connection to store ingested data.
    """
    try:
        config = _ingest_config[source]
    except KeyError as e:
        raise ValueError(f"Unsupported source for ingestion: {source}") from e

    already_loaded = _get_ingested_intervals(db, source)
    missing_intervals = find_missing_intervals(interval, already_loaded)

    logger.debug("Target interval to ingest: %s", interval)
    logger.debug("Already loaded %s intervals: %s", source.value, already_loaded)
    logger.debug("Missing %s intervals to ingest: %s", source.value, missing_intervals)

    if not missing_intervals:
        logger.info("%s %s→%s already in bronze – skipping.", source.value, interval.start, interval.end)
        return

    for missing in missing_intervals:
        _ingest_preprints_from_interval(
            db=db,
            start=missing.start,
            end=missing.end,
            source=source,
            **config,
        )


def find_missing_intervals(target_interval: DateInterval, existing_intervals: list[DateInterval]) -> list[DateInterval]:
    """Find missing sub-intervals within target_interval given existing_intervals."""
    missing_intervals = []
    current_start = target_interval.start

    # Sort existing intervals by start date
    sorted_intervals = sorted(existing_intervals, key=lambda x: x.start)

    for interval in sorted_intervals:
        if interval.start > current_start:
            missing_intervals.append(DateInterval(start=current_start, end=interval.start - timedelta(days=1)))
        current_start = max(current_start, interval.end + timedelta(days=1))

    if current_start <= target_interval.end:
        missing_intervals.append(DateInterval(start=current_start, end=target_interval.end))

    return missing_intervals


def _get_ingested_intervals(db: Session, src: Source) -> list[DateInterval]:
    """Get all existing intervals for a given source."""
    return [
        DateInterval(start=ingest.start_date, end=ingest.end_date)
        for ingest in db.scalars(select(IntervalIngest).where(IntervalIngest.source == src)).all()
    ]


# these parameters are specific to each source
_ingest_config = {
    Source.BIORXIV: {
        "fetch_preprint_data": fetch_biorxiv,
        "source_id_field": "doi",
        "DbModel": BronzeBiorxivPreprint,
    },
    Source.OPENALEX: {
        "fetch_preprint_data": fetch_biorxiv_from_oa,
        "source_id_field": "id",
        "DbModel": BronzeOpenAlexPreprint,
    },
}


def _ingest_preprints_from_interval(
    db: Session,
    start: date,
    end: date,
    source=Source.BIORXIV,
    fetch_preprint_data=fetch_biorxiv,
    source_id_field="doi",
    DbModel=BronzeBiorxivPreprint,
) -> None:
    """Ingest bioRxiv preprints for a specific date interval."""
    logger.info("Ingesting %s preprints between %s and %s", source.value, start, end)
    try:
        ingestion_interval = mark_ingestion_start(db, source, start, end)
    except IntegrityError:
        logger.warning("Unexpected: %s %s→%s already in bronze – skipping.", source.value, start, end)
        return

    ingested = 0
    try:
        for rec in tqdm(fetch_preprint_data(start, end), desc=f"{source.value} bronze"):
            sid = rec[source_id_field]
            db.add(DbModel(source_id=sid, raw_json=rec))
            ingested += 1
        db.commit()
    except Exception as e:
        db.delete(ingestion_interval)
        db.commit()
        logger.error("Failed to ingest %s %s→%s: %s", source.value, start, end, e)
        raise
    logger.info("Ingested %d %s preprints", ingested, source.value)


def mark_ingestion_start(db: Session, src: Source, start: date, end: date) -> IntervalIngest:
    """Check if interval already ingested; if not, record it."""
    interval_ingest = IntervalIngest(source=src, start_date=start, end_date=end)
    try:
        db.add(interval_ingest)
        db.commit()  # succeeds only if interval unseen
        return interval_ingest
    except IntegrityError:
        db.rollback()
        raise
