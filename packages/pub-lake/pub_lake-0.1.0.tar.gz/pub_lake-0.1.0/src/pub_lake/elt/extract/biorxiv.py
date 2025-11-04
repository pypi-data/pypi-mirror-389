"""Fetch preprints from the bioRxiv API."""

from collections.abc import Iterator
from datetime import date
from logging import getLogger

from requests import RequestException, get
from tenacity import retry, stop_after_attempt, wait_exponential

logger = getLogger(__name__)

BIORXIV_API_URL = "https://api.biorxiv.org/details/biorxiv"
BIORXIV_DATE_FORMAT = "%Y-%m-%d"

BIORXIV_MAX_RETRIES = 15
BIORXIV_RETRY_BACKOFF_MAX = 30  # seconds
BIORXIV_RETRY_BACKOFF_MIN = 1  # seconds
BIORXIV_RETRY_BACKOFF_MULTIPLIER = 1  # seconds


@retry(
    stop=stop_after_attempt(BIORXIV_MAX_RETRIES),
    wait=wait_exponential(
        multiplier=BIORXIV_RETRY_BACKOFF_MULTIPLIER, min=BIORXIV_RETRY_BACKOFF_MIN, max=BIORXIV_RETRY_BACKOFF_MAX
    ),
)
def fetch_page(url: str) -> dict:
    """Fetch a single page from the bioRxiv API with retries."""
    response = get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def fetch_biorxiv_preprints(start: date, end: date) -> Iterator[dict]:
    """
    Fetch bioRxiv preprints from the bioRxiv API.

    Parameters
    ----------
    start : datetime.date
        Interval start date. Must be before or equal to `end`.
    end : datetime.date
        Interval end date. Must be after or equal to `start`.

    Yields
    ------
    dict
        Preprint records from bioRxiv.
    """
    assert start <= end, f"Start date must be before or equal to end date, got start='{start}', end='{end}'"

    start_str = start.strftime(BIORXIV_DATE_FORMAT)
    end_str = end.strftime(BIORXIV_DATE_FORMAT)
    logger.info("Fetching bioRxiv preprints between %s and %s", start_str, end_str)
    logger.debug("  max retries: %s", BIORXIV_MAX_RETRIES)

    cursor = 0
    while True:
        url = f"{BIORXIV_API_URL}/{start_str}/{end_str}/{cursor}"
        try:
            data = fetch_page(url)
        except RequestException as e:
            logger.error("Failed to fetch data from %s after %s retries: %s", url, BIORXIV_MAX_RETRIES, e)
            raise

        preprints = data.get("collection", [])
        if not preprints:
            break

        yield from preprints

        messages = data.get("messages", [])
        if not messages or "cursor" not in messages[0]:
            break
        cursor = int(messages[0]["cursor"]) + int(messages[0]["count"])
