"""
A library for fetching and normalizing academic papers from various providers (Elsevier, arXiv, PRISM, etc.).

Usage:
     from papex import Paper, extract_papers, configure_providers
     configure_providers(elsevier_api_key="YOUR_KEY", arxiv_max_results=10)
     papers = extract_papers("Elsevier", "machine learning")
    for paper in papers:
    ...     print(paper.title)
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#import paper
from papex.generic_adapter import GenericAdapter
from papex.provider_config import (
   ELSEVIER_CONFIG,
   ARXIV_CONFIG,
   PRISM_CONFIG,
   IEEE_CONFIG,
)
from papex.provider_config import DOI_PREFIX_TO_PROVIDER
from papex.paperObj import Paper
from typing import Dict, List, Optional

# Global storage for provider configs (users can override defaults)

_PROVIDER_CONFIGS = {
    "Elsevier": ELSEVIER_CONFIG,
    "arXiv": ARXIV_CONFIG,
    "PRISM": PRISM_CONFIG,
    "IEEE": IEEE_CONFIG,
}
def prefix_to_name(provider_prefix: str=None) -> str:
    """
    Convert a DOI or other prefix to the provider name.
    Args:
        provider_prefix: The prefix (e.g., "10.1016", "arXiv:").
    Returns:
        str: The provider name (e.g., "Elsevier", "arXiv").
    Raises:
        ValueError: If the prefix is not recognized.
    """
    # Handle arXiv-style prefixes (e.g., "arXiv:")
    if provider_prefix.lower().startswith("arxiv:"):
        return "arXiv"
    # Handle DOI prefixes (e.g., "10.1016")
    for doi_prefix, provider in DOI_PREFIX_TO_PROVIDER.items():
        if provider_prefix.startswith(doi_prefix):
            return provider
    # Handle other custom prefixes here if needed
    raise ValueError(f"Unrecognized prefix: {provider_prefix}")
     

def configure_providers(
    elsevier_api_key: Optional[str] = None,
    arxiv_max_results: Optional[int] = None,
    **kwargs
) -> None:
    """
    Configure API keys and settings for providers.

    Args:
        elsevier_api_key: API key for Elsevier.
        arxiv_max_results: Default max results for arXiv queries.
        **kwargs: Additional provider-specific settings (e.g., `ieee_api_key`).
    """

    if elsevier_api_key:
        _PROVIDER_CONFIGS["Elsevier"]["params"]["apiKey"] = elsevier_api_key
    if arxiv_max_results:
        _PROVIDER_CONFIGS["arXiv"]["max_results"] = arxiv_max_results
    for provider, config in kwargs.items():
        if provider in _PROVIDER_CONFIGS:
            _PROVIDER_CONFIGS[provider].update(config)

def extract_papers(query:str,provider_name:Optional[str]=None,provider_prefix:Optional[str]=None, **kwargs) -> List[Paper]:
    """
    Fetch papers from a provider.

    Args:
        provider_name: Name of the provider (e.g., "Elsevier", "arXiv").
        query: Search query.
        **kwargs: Additional arguments (e.g., `count=5` for Elsevier).

    Returns:
        List[Paper]: Normalized paper objects.
    """
    if provider_name==None:
        # Ensure provider_prefix is not None before passing it to prefix_to_name
        if provider_prefix is not None:
            provider_name = prefix_to_name(provider_prefix)
        else:
            # Handle the case where provider_prefix is None
            raise ValueError("provider_prefix cannot be None")

    if provider_name not in _PROVIDER_CONFIGS:
        if isinstance(provider, dict) and provider:
            # Get the first item from the dictionary
            key, value = next(iter(provider.items()))
            # Now you can use key and value as needed
            # For example, if you want to use the key as provider_name:
            provider_name = key
        else:
            # Handle the case where provider is not a dictionary or is empty
            raise ValueError("Provider must be a non-empty dictionary")
    adapter = GenericAdapter(_PROVIDER_CONFIGS[provider_name])
    return adapter.fetch_papers(query, **kwargs)

# Expose public symbols
__all__ = ["Paper", "extract_papers", "configure_providers"]
