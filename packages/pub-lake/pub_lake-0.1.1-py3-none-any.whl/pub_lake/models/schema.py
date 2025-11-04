"""
SQLAlchemy ORM schema definitions for the pub-lake project.

Uses the medallion model for data ingestion: Bronze (raw) → Silver (cleaned, per-source) → Gold (canonical).
"""

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Engine,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
)
from sqlalchemy_utc import utcnow

from pub_lake import config

Base = declarative_base()


# ----------------------------------------------------------------------
# Bronze – raw payloads
# ----------------------------------------------------------------------
class Source(enum.Enum):
    OPENALEX = "openalex"
    BIORXIV = "biorxiv"
    OTHER = "other"


class BronzeOpenAlexPreprint(Base):
    __tablename__ = "bronze_openalex_preprint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingest_ts: Mapped[datetime] = mapped_column(DateTime, server_default=utcnow())
    source_id: Mapped[str] = mapped_column(String, index=True)  # OpenAlex Work ID
    raw_json: Mapped[dict] = mapped_column(JSON)

    skipped: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    silver_preprint_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("silver_preprint.id"))
    silver_preprint: Mapped[Optional["SilverPreprint"]] = relationship(
        "SilverPreprint", back_populates="bronze_openalex_preprints"
    )


class BronzeBiorxivPreprint(Base):
    __tablename__ = "bronze_biorxiv_preprint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingest_ts: Mapped[datetime] = mapped_column(DateTime, server_default=utcnow())
    source_id: Mapped[str] = mapped_column(String, index=True)  # DOI, OpenAlex ID, ...
    raw_json: Mapped[dict] = mapped_column(JSON)

    skipped: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    silver_preprint_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("silver_preprint.id"))
    silver_preprint: Mapped[Optional["SilverPreprint"]] = relationship(
        "SilverPreprint", back_populates="bronze_biorxiv_preprints"
    )


class IntervalIngest(Base):
    """
    Tracks which [start, end] date intervals have been successfully loaded
    for each source *at the bronze layer*.
    """

    __tablename__ = "interval_ingest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[Source] = mapped_column(Enum(Source))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    loaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=utcnow())

    __table_args__ = (UniqueConstraint("source", "start_date", "end_date", name="uq_ingest_interval"),)


# ----------------------------------------------------------------------
# Silver – cleaned, per-source
# ----------------------------------------------------------------------
class SilverPreprint(Base):
    """
    One row per record per source after normalisation.
    """

    __tablename__ = "silver_preprint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Source identification
    source: Mapped[Source] = mapped_column(Enum(Source))
    source_id: Mapped[str] = mapped_column(String)

    skipped: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Fields common across sources
    doi: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str] = mapped_column(Text)
    publish_date: Mapped[date] = mapped_column(Date)

    # bioRxiv-specific fields
    version: Mapped[str | None] = mapped_column(Integer, index=True)
    biorxiv_category: Mapped[str | None] = mapped_column(String)

    # OpenAlex-specific fields
    openalex_topics: Mapped[dict | None] = mapped_column(JSON)
    update_ts: Mapped[datetime | None] = mapped_column(DateTime, index=True)

    preprint_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("preprint.id"))
    preprint: Mapped[Optional["Preprint"]] = relationship("Preprint", back_populates="silver_preprints")

    # Relationships to bronze records
    bronze_biorxiv_preprints: Mapped[list[BronzeBiorxivPreprint]] = relationship(
        "BronzeBiorxivPreprint", back_populates="silver_preprint"
    )
    bronze_openalex_preprints: Mapped[list[BronzeOpenAlexPreprint]] = relationship(
        "BronzeOpenAlexPreprint", back_populates="silver_preprint"
    )

    __table_args__ = (
        # one silver preprint per source/source_id: e.g. one silver preprint for all versions of a bioRxiv preprint
        UniqueConstraint("source", "source_id", name="uq_source_sourceid"),
    )


# ----------------------------------------------------------------------
# Gold – canonical layer
# ----------------------------------------------------------------------


# OpenAlex topic hierarchy
# ───────────────────────── topic dimension ───────────────────────────
class Topic(Base):
    __tablename__ = "topic"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oa_topic_id: Mapped[str] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)

    oa_subfield_id: Mapped[str] = mapped_column(String)
    subfield_display_name: Mapped[str] = mapped_column(String)

    oa_field_id: Mapped[str] = mapped_column(String)
    field_display_name: Mapped[str] = mapped_column(String)

    oa_domain_id: Mapped[str] = mapped_column(String)
    domain_display_name: Mapped[str] = mapped_column(String)

    preprints: Mapped[list["Preprint"]] = relationship("Preprint", secondary="preprint_topic", back_populates="topics")


# ────────────────── bridge table gets score & primary flag ───────────
preprint_topic = Table(
    "preprint_topic",
    Base.metadata,
    Column("preprint_id", ForeignKey("preprint.id"), primary_key=True),
    Column("topic_id", ForeignKey("topic.id"), primary_key=True),
    Column("is_primary", Boolean, default=False),
    Column("score", Float),  # OpenAlex relevance score 0-1
)


# bioRxiv category dictionary
class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    preprints: Mapped[list["Preprint"]] = relationship("Preprint", back_populates="category")


# Canonical preprint
class Preprint(Base):
    __tablename__ = "preprint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_doi: Mapped[str] = mapped_column(String, unique=True)
    canonical_version: Mapped[str] = mapped_column(String)
    canonical_title: Mapped[str] = mapped_column(Text)
    canonical_abstract: Mapped[str] = mapped_column(Text)
    canonical_publish_date: Mapped[date] = mapped_column(Date)

    # FK to bioRxiv category (single-valued)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("category.id"))
    category: Mapped[Category] = relationship("Category", back_populates="preprints")

    topics: Mapped[list[Topic]] = relationship("Topic", secondary=preprint_topic, back_populates="preprints")

    silver_preprints: Mapped[list[SilverPreprint]] = relationship("SilverPreprint", back_populates="preprint")


# ----------------------------------------------------------------------
# Bootstrap helper
# ----------------------------------------------------------------------
def bootstrap(db_url: str = config.DATABASE_URL) -> Engine:
    engine = create_engine(db_url, echo=False, future=True)
    Base.metadata.create_all(engine)
    return engine


if __name__ == "__main__":
    bootstrap()
