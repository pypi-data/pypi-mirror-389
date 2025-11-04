#to get up to paper_lib path:
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import TYPE_CHECKING, List, Dict, Any, Optional
from papex.fetch_strategies import FETCH_STRATEGIES
import xml.etree.ElementTree as ET
from papex.paperObj import Paper


class GenericAdapter:
    """A fully generic adapter for any provider."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.field_mapping = config["field_mapping"]
        self.provider_name = config["provider"]["name"]
        self.provider_prefix= config["provider"]["doi_prefix"]
        self.strategy = FETCH_STRATEGIES[config["fetch_strategy"]]

    def fetch_data(self, query: str, **kwargs) -> Any:
        """Fetch raw data using the provider's strategy."""
        fetch_func = self.strategy["fetch"]
        if self.config["fetch_strategy"] == "rest":
            params = {**self.config.get("params", {}), **kwargs}
            return fetch_func(self.config["base_url"], params)
        elif self.config["fetch_strategy"] == "arxiv":
            return fetch_func(query, kwargs.get("max_results", 10))
        elif self.config["fetch_strategy"] == "xml":
            return fetch_func(kwargs.get("xml_response"), None)
        else:
            raise ValueError(f"Unsupported fetch strategy: {self.config['fetch_strategy']}")
            pass
    def parse_item(self, item: Dict[str, Any] | ET.Element) -> Dict[str, Any]:
        """Parse a single item (JSON dict or XML element)."""
        parsed_item = {}
        for paper_field, api_field in self.field_mapping.items():
            if isinstance(api_field, dict):
                parsed_item[paper_field] = self._parse_field(item, api_field)
            else:
                if self.config["fetch_strategy"] == "xml":
                    element = item.find(api_field, namespaces=self.config.get("namespaces", {}))
                    parsed_item[paper_field] = element.text if element is not None else None
                elif self.config["fetch_strategy"] == "arxiv":
                    # Handle arXiv Result objects
                    if hasattr(item, api_field):
                        attr = getattr(item, api_field)
                        parsed_item[paper_field] = attr
                    elif api_field == "authors":
                        parsed_item[paper_field] = [author.name for author in item.authors]
                    else:
                        parsed_item[paper_field] = None
                else:
                     # Handle JSON dictionaries
                    parsed_item[paper_field] = item.get(api_field)
        return parsed_item

    def _parse_field(self, item: Dict[str, Any] | ET.Element, field_config: Dict[str, Any]) -> Any:
        """Parse nested or custom fields."""
        if field_config["type"] == "nested" :
            if isinstance(item, dict):
               # Handle JSON dictionaries
                nested_item = item
                for key in field_config["path"].split("."):
                   nested_item = nested_item.get(key, {})
                return nested_item
            else:
            # Handle XML elements
                nested_item = item
                for key in field_config["path"].split("."):
                    nested_item = nested_item.find(key, namespaces=self.config.get("namespaces", {}))
                    if nested_item is not None:
                         nested_item = nested_item.text
                    else:
                         return None
                return nested_item

        elif field_config["type"] == "list":
            if isinstance(item, dict):
            # Handle JSON dictionaries
                return [sub_item[field_config["key"]] for sub_item in item.get(field_config["path"], [])]
            else:
                # Handle XML elements
                elements = item.findall(field_config["path"], namespaces=self.config.get("namespaces", {}))
                return [element.text for element in elements]

        elif field_config["type"] == "custom":
            return field_config["func"](item)

        elif field_config["type"] == "xml":
            element = item.find(field_config["path"], namespaces=self.config.get("namespaces", {}))
            return element.text if element is not None else None

        else:
            if isinstance(item, dict):
             # Handle JSON dictionaries
                 return item.get(field_config["path"])
            else:
                # Handle XML elements
                element = item.find(field_config["path"], namespaces=self.config.get("namespaces", {}))
                return element.text if element is not None else None

    def fetch_papers(self, query: str, **kwargs) -> List[Paper]:
        """Fetch and parse papers."""
        raw_data = self.fetch_data(query, **kwargs)
        items = self.strategy["extract_items"](raw_data, self.config.get("items_path"))
        papers = []
        for item in items:
            parsed_item = self.parse_item(item)
            papers.append(Paper(**parsed_item))
        return papers
