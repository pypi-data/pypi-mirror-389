from typing import Dict, Any, List, Callable
import requests
import arxiv
import xml.etree.ElementTree as ET

# Define fetch strategies for different API types
FETCH_STRATEGIES = {
    "rest": {
        "fetch": lambda url, params: requests.get(url, params=params).json(),
        "extract_items": lambda data, items_path: data[items_path],
    },
    "arxiv": {
        "fetch": lambda query, max_results: list(arxiv.Client().results(arxiv.Search(query=query, max_results=max_results))),
        "extract_items": lambda data, _: data,  # arXiv results are already a list
    },
    "xml": {
        "fetch": lambda xml_response, _: xml_response,  # XML is passed directly
        "extract_items": lambda xml_response, items_path: ET.fromstring(xml_response).findall(items_path),
    },
    # Add more strategies as needed (e.g., GraphQL, SOAP)
}
