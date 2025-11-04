"""Unit tests for src/pub_lake/elt/extract/biorxiv.py."""

from datetime import date
from unittest.mock import Mock, patch

from pytest import raises

from pub_lake.elt.extract.biorxiv import fetch_biorxiv_preprints


def _setup_mock_get(mock_get, pages):
    mock_response = Mock()
    mock_response.json.side_effect = pages
    mock_get.return_value = mock_response
    return mock_response


def _assert_date_interval_in_get_call(mock_get, start: date, end: date):
    expected_url_part = f"{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
    for call in mock_get.call_args_list:
        actual_url = call.args[0]
        assert expected_url_part in actual_url, (
            f"Expected URL to contain date interval '{expected_url_part}', got '{actual_url}'"
        )


@patch("pub_lake.elt.extract.biorxiv.get")
def test_fetch_biorxiv_preprints_with_pagination(mock_get):
    # Arrange
    pages = [
        {
            "collection": [{"doi": "10.1101/123"}, {"doi": "10.1101/456"}],
            "messages": [{"cursor": "1", "count": 2, "total": 3}],
        },
        {
            "collection": [{"doi": "10.1101/789"}],
            "messages": [{"cursor": "2", "count": 1, "total": 3}],
        },
        {"collection": [], "messages": []},
    ]
    _setup_mock_get(mock_get, pages)

    # Act
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 1)
    preprints = list(fetch_biorxiv_preprints(start_date, end_date))

    # Assert
    _assert_date_interval_in_get_call(mock_get, start_date, end_date)
    assert len(preprints) == sum(len(page["collection"]) for page in pages)
    assert preprints[0]["doi"] == pages[0]["collection"][0]["doi"]
    assert preprints[1]["doi"] == pages[0]["collection"][1]["doi"]
    assert preprints[2]["doi"] == pages[1]["collection"][0]["doi"]
    assert mock_get.call_count == len(pages)


@patch("pub_lake.elt.extract.biorxiv.get")
def test_fetch_biorxiv_preprints_empty_result(mock_get):
    # Arrange
    pages = [{"collection": [], "messages": []}]
    _setup_mock_get(mock_get, pages)

    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 1)

    # Act
    preprints = list(fetch_biorxiv_preprints(start_date, end_date))

    # Assert
    _assert_date_interval_in_get_call(mock_get, start_date, end_date)
    assert len(preprints) == 0
    assert mock_get.call_count == 1


@patch("pub_lake.elt.extract.biorxiv.get")
def test_fetch_biorxiv_preprints_invalid_date_range(mock_get):
    # Arrange
    start_date = date(2023, 1, 2)
    end_date = date(2023, 1, 1)

    # Act & Assert
    with raises(AssertionError):
        list(fetch_biorxiv_preprints(start_date, end_date))
    mock_get.assert_not_called()
