from datetime import date
from functools import cached_property

from pandas import DataFrame
from pydantic import BaseModel, model_validator
from typing_extensions import Self


class DateInterval(BaseModel):
    """
    A date interval with start and end dates.

    Both dates are inclusive.
    `start` must be before or equal to `end`.
    """

    start: date
    """The start date of the interval. Must be before or equal to `end`."""
    end: date
    """The end date of the interval. Must be after or equal to `start`."""

    @model_validator(mode="after")
    def check_dates_in_order(self: Self) -> Self:
        if self.start > self.end:
            raise ValueError("Start date must be before or equal to end date")
        return self


class Preprint(BaseModel):
    """A preprint record."""

    doi: str
    """The DOI of the preprint."""
    version: str
    """The version of the preprint."""
    title: str
    """The title of the preprint."""
    abstract: str
    """The abstract of the preprint."""
    publish_date: date
    """The publish date of the preprint."""

    category: str
    """The bioRxiv category of the preprint."""

    topic: str | None
    """The OpenAlex topic of the preprint."""
    subfield: str | None
    """The OpenAlex subfield of the preprint."""
    field: str | None
    """The OpenAlex field of the preprint."""
    domain: str | None
    """The OpenAlex domain of the preprint."""


class Preprints(BaseModel):
    """A collection of preprint records."""

    preprints: list[Preprint]

    @cached_property
    def df(self) -> DataFrame:
        """DataFrame containing the papers."""
        return DataFrame(
            [preprint.model_dump() for preprint in self.preprints],
            columns=[
                "doi",
                "version",
                "title",
                "abstract",
                "publish_date",
                "category",
                "topic",
                "subfield",
                "field",
                "domain",
            ],
        )
