"""Interface for fetching preprint records from the database."""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from pub_lake.models.preprints import DateInterval, Preprints
from pub_lake.models.preprints import Preprint as PreprintModel
from pub_lake.models.schema import (
    Preprint as PreprintSchema,
)
from pub_lake.models.schema import (
    Topic as TopicSchema,
)
from pub_lake.models.schema import (
    bootstrap,
    preprint_topic,
)


def get_preprints(interval: DateInterval | None) -> Preprints:
    """Fetch preprint records from the database.

    Returns:
        Preprints: A collection of preprint records.
    """
    eng = bootstrap()

    with Session(eng) as db:
        primary_topic_join_condition = and_(
            PreprintSchema.id == preprint_topic.c.preprint_id,
            preprint_topic.c.is_primary,
        )
        query = (
            select(
                PreprintSchema,
                TopicSchema,
            )
            .outerjoin(preprint_topic, primary_topic_join_condition)
            .outerjoin(TopicSchema, TopicSchema.id == preprint_topic.c.topic_id)
            .order_by(PreprintSchema.canonical_publish_date.asc())
        )
        if interval:
            query = query.where(
                and_(
                    PreprintSchema.canonical_publish_date >= interval.start,
                    PreprintSchema.canonical_publish_date <= interval.end,
                )
            )
        results = db.execute(query).all()

        preprints = [
            PreprintModel(
                doi=preprint.canonical_doi,
                version=preprint.canonical_version,
                title=preprint.canonical_title,
                abstract=preprint.canonical_abstract,
                publish_date=preprint.canonical_publish_date,
                category=preprint.category.name,
                topic=primary_topic.display_name if primary_topic else None,
                subfield=primary_topic.subfield_display_name if primary_topic else None,
                field=primary_topic.field_display_name if primary_topic else None,
                domain=primary_topic.domain_display_name if primary_topic else None,
            )
            for (preprint, primary_topic) in results
        ]
    return Preprints(preprints=preprints)
