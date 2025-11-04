"""ELT pipeline from raw data ingestion to transformed data."""

from logging import getLogger

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from pub_lake import config
from pub_lake.elt.load.bronze import ingest_preprints_bronze
from pub_lake.elt.transform.gold import preprints_silver_to_gold
from pub_lake.elt.transform.silver import preprints_bronze_to_silver
from pub_lake.models.preprints import DateInterval
from pub_lake.models.schema import Source

logger = getLogger(__name__)


def ingest_preprints(interval: DateInterval) -> None:
    """Run the full pipeline to ingest preprints for the given date interval."""
    logger.info("Running ETL pipeline from %s to %s", interval.start, interval.end)
    eng = create_engine(config.DATABASE_URL)
    with Session(eng) as db:
        ingest_preprints_bronze(interval, Source.BIORXIV, db)
        ingest_preprints_bronze(interval, Source.OPENALEX, db)
        preprints_bronze_to_silver(db)
        preprints_silver_to_gold(db)
