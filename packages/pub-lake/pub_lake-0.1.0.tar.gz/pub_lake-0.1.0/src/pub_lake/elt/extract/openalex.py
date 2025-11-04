"""Fetch data from the OpenAlex API."""

from collections.abc import Iterator
from datetime import date
from logging import getLogger

from pyalex import Works
from pyalex import config as pa_config

from pub_lake import config

logger = getLogger(__name__)

pa_config.max_retries = 15
pa_config.retry_backoff_factor = 0.2

OA_PER_PAGE = 200  # OpenAlex max
OA_SOURCE_ID_BIORXIV = "https://openalex.org/S4306402567"  # from https://api.openalex.org/sources?search=biorxiv
OA_DATE_FORMAT = "%Y-%m-%d"


def fetch_biorxiv_preprints(start: date, end: date) -> Iterator[dict]:
    """
    Fetch bioRxiv preprints in an interval from the OpenAlex API.

    Parameters
    ----------
    start : datetime.date
        Interval start date. Must be before or equal to `end`.
    end : datetime.date
        Interval end date. Must be after or equal to `start`.
    Yields
    ------
    dict
        Preprint records from OpenAlex.
    """
    assert start <= end, f"Start date must be before or equal to end date, got start='{start}', end='{end}'"

    start_str = start.strftime(OA_DATE_FORMAT)
    end_str = end.strftime(OA_DATE_FORMAT)

    if config.POLITE_EMAIL is not None:
        pa_config.POLITE_EMAIL = config.POLITE_EMAIL

    logger.info("Fetching bioRxiv preprints from OpenAlex between %s and %s", start_str, end_str)
    logger.debug("  polite email: %s", config.POLITE_EMAIL)
    logger.debug("  max retries: %s", pa_config.max_retries)
    logger.debug("  retry backoff factor: %s", pa_config.retry_backoff_factor)
    logger.debug("  per_page: %s", OA_PER_PAGE)
    logger.debug("  primary_location.source.id: %s", OA_SOURCE_ID_BIORXIV)

    filters = {
        "from_publication_date": start_str,
        "to_publication_date": end_str,
        "primary_location": {
            "source": {
                "id": OA_SOURCE_ID_BIORXIV,
            },
        },
    }
    works_iter = (
        Works()
        .filter(**filters)
        .paginate(
            method="cursor",  # cursor pagination to get more than 10k results
            per_page=OA_PER_PAGE,  # use max per_page to reduce number of requests
            n_max=None,  # unset pyalex default limit of 10k results
        )
    )
    for page in works_iter:
        yield from page
