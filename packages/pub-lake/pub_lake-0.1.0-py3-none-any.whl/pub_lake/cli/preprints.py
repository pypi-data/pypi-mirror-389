"""Console script for pub_lake."""

from datetime import datetime
from logging import basicConfig
from typing import Annotated

from typer import Option, Typer, echo

from pub_lake import config
from pub_lake.elt.pipeline import ingest_preprints
from pub_lake.interface.preprints import get_preprints
from pub_lake.models.preprints import DateInterval
from pub_lake.models.schema import bootstrap

basicConfig(level="INFO")
app = Typer()


start_date_option = Option(..., help="Start date in YYYY-MM-DD format. Inclusive. Must be before or equal to END.")
end_date_option = Option(..., help="End date in YYYY-MM-DD format. Inclusive. Must be after or equal to START.")
polite_option = Option(..., help="Email address for polite web scraping.")


def echo_preprints(interval: DateInterval | None):
    preprints_df = get_preprints(interval=interval).df
    echo(
        preprints_df.to_string(
            columns=["doi", "version", "title", "publish_date", "category", "topic"],
            max_colwidth=25,
            max_rows=20,
            show_dimensions=True,
        )
    )


@app.command()
def fetch(
    start: Annotated[datetime, start_date_option],
    end: Annotated[datetime, end_date_option],
    polite: Annotated[str, polite_option],
):
    """Ingest preprints from START to END."""
    config.POLITE_EMAIL = polite
    interval = DateInterval(start=start.date(), end=end.date())
    bootstrap()
    ingest_preprints(interval)
    echo_preprints(interval)


@app.command()
def list(
    start: Annotated[datetime | None, start_date_option] = None,
    end: Annotated[datetime | None, end_date_option] = None,
):
    """List available preprints from START to END."""
    if start is None:
        start = datetime.min
    if end is None:
        end = datetime.max
    interval = DateInterval(start=start.date(), end=end.date())
    bootstrap()
    echo_preprints(interval)


if __name__ == "__main__":
    app()
