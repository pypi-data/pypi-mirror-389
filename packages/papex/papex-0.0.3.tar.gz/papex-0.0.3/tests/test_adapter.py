import pytest
from unittest.mock import patch
from papex.generic_adapter import GenericAdapter
from paper_lib.provider_configs import ELSEVIER_CONFIG

@patch("paper_lib.generic_adapter.requests.get")
def test_elsevier_adapter(mock_get):
    """Test the Elsevier adapter with a mocked API response."""
    # Mock the API response
    mock_get.return_value.json.return_value = {
        "search-results": {
            "entry": [{
                "title": "Mocked Paper",
                "authors": {"author": [{"preferred-name": {"surname": "Smith"}}]},
                "doi": "10.1234/mock",
                "publicationDate": "2023-01-01"
            }]
        }
    }

    adapter = GenericAdapter(ELSEVIER_CONFIG)
    papers = adapter.fetch_papers("test query", count=1)

    assert len(papers) == 1
    assert papers[0].title == "Mocked Paper"
    assert papers[0].authors == ["Smith"]
    assert papers[0].doi == "10.1234/mock"