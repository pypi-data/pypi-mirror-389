"""Unit tests for src/pub_lake/elt/load/bronze.py."""

from datetime import date

from pytest import mark

from pub_lake.elt.load.bronze import find_missing_intervals
from pub_lake.models.preprints import DateInterval


@mark.parametrize(
    "target,existing,expected,description",
    [
        (
            (date(2023, 1, 1), date(2023, 1, 10)),
            [(date(2023, 1, 3), date(2023, 1, 5))],
            [(date(2023, 1, 1), date(2023, 1, 2)), (date(2023, 1, 6), date(2023, 1, 10))],
            "Single existing interval within target",
        ),
        (
            (date(2023, 1, 1), date(2023, 1, 10)),
            [
                (date(2023, 1, 1), date(2023, 1, 2)),
                (date(2023, 1, 5), date(2023, 1, 7)),
            ],
            [(date(2023, 1, 3), date(2023, 1, 4)), (date(2023, 1, 8), date(2023, 1, 10))],
            "Multiple existing intervals within target",
        ),
        (
            (date(2023, 1, 1), date(2023, 1, 10)),
            [
                (date(2022, 12, 25), date(2022, 12, 31)),
                (date(2023, 1, 11), date(2023, 1, 15)),
            ],
            [(date(2023, 1, 1), date(2023, 1, 10))],
            "Existing intervals outside target",
        ),
        (
            (date(2023, 1, 1), date(2023, 1, 10)),
            [
                (date(2023, 1, 1), date(2023, 1, 10)),
            ],
            [],
            "Existing interval exactly matches target",
        ),
        (
            (date(2023, 1, 1), date(2023, 1, 10)),
            [],
            [(date(2023, 1, 1), date(2023, 1, 10))],
            "No existing intervals",
        ),
    ],
)
def test_find_missing_intervals(target, existing, expected, description):
    # Act
    target_interval = DateInterval(start=target[0], end=target[1])
    existing_intervals = [DateInterval(start=start, end=end) for start, end in existing]
    missing_intervals = find_missing_intervals(target_interval, existing_intervals)

    # Assert
    expected_intervals = [DateInterval(start=start, end=end) for start, end in expected]
    assert missing_intervals == expected_intervals, f"{description}: {missing_intervals} != {expected_intervals}"
