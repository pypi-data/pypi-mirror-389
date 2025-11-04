import pytest
from unittest.mock import patch
from papex import extract_papers, configure_providers

@patch("paper_lib.generic_adapter.requests.get")
def test_extract_papers(mock_get):
    """Test the full extraction workflow."""
    # Mock the API response
    mock_get.return_value.json.return_value = {
        "search-results": {
            "entry": [{
                "title": "Integration Test Paper",
                "authors": {"author": [{"preferred-name": {"surname": "Doe"}}]},
                "doi": "10.1234/integration",
                "publicationDate": "2023-01-01"
            }]
        }
    }

    # Configure the provider (mock API key)
    configure_providers(elsevier_api_key="mock_key")

    # Fetch papers
    papers = extract_papers("Elsevier", "test query", count=1)

    assert len(papers) == 1
    assert papers[0].title == "Integration Test Paper"
    assert papers[0].doi == "10.1234/integration"