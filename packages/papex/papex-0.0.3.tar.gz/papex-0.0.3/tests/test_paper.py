import pytest
from unittest.mock import patch
from papex import paper

def test_paper_creation():
    """Test creating a Paper object."""
    paper = Paper(
        title="Test Paper",
        authors=["Alice", "Bob"],
        abstract="This is a test.",
        doi="10.1234/test",
        publication_date="2023-01-01"
    )
    assert paper.title == "Test Paper"
    assert paper.authors == ["Alice", "Bob"]
    assert paper.abstract == "This is a test."
    assert paper.doi == "10.1234/test"
    assert paper.publication_date == "2023-01-01"

def test_paper_from_dict():
    """Test creating a Paper from a dictionary."""
    data = {
        "title": "Dict Paper",
        "authors": ["Charlie"],
        "doi": "10.5678/test"
    }
    paper = Paper.from_dict(data)
    assert paper.title == "Dict Paper"
    assert paper.to_dict() == data
