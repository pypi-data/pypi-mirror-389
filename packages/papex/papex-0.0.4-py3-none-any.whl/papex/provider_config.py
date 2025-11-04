
# In a new file, e.g., doi_provider_mapping.py
DOI_PREFIX_TO_PROVIDER = {
    "10.1016": "Elsevier",  # Elsevier DOIs
    "10.1109": "IEEE",      # IEEE DOIs
    "10.1007": "Springer",  # Springer DOIs
    "10.1038": "Nature",    # Nature DOIs
    "10.1126": "Science",   # Science DOIs
    "10.1093": "Oxford",    # Oxford Academic DOIs
    "10.1073": "PNAS",      # PNAS DOIs
    "10.1145": "ACM",       # ACM DOIs
    "10.1021": "ACS",       # American Chemical Society DOIs
    "10.1088": "IOP",       # Institute of Physics DOIs
    "10.1210": "Endocrine", # Endocrine Society DOIs
    "10.48550": "arXiv",    # arXiv DOIs
}
# Elsevier (REST API)
ELSEVIER_CONFIG = {
    "provider":{"name":"Elsevier", "doi_prefix":"10.1016"},
    "fetch_strategy": "rest",
    "base_url": "https://api.elsevier.com/content/search/scopus",
    "params": {"apiKey": "YOUR_ELSEVIER_API_KEY"},
    "items_path": ["search-results", "entry"],
    "field_mapping": {
        "title": "title",
        "authors": {
            "type": "list",
            "path": "authors.author",
            "key": "preferred-name.surname"
        },
        "abstract": "abstract",
        "doi": "doi",
        "publication_date": "publicationDate",
        "provider_id": "scopus_id",
        "url": "link",
        "journal": "publicationName",
    }
}

# arXiv
ARXIV_CONFIG = {
    "provider": {"name":"arXiv", "doi_prefix":"10.48550"},
    "fetch_strategy": "arxiv",
    "field_mapping": {
        "title": "title",
        "authors": {
            "type": "custom",
            "func": lambda item: [author.name for author in item.authors]
        },
        "abstract": "summary",
        "doi": "doi",
        "publication_date": {
            "type": "custom",
            "func": lambda item: str(item.published)
        },
        "provider_id": "entry_id",
        "url": "pdf_url",
    }
}

# PRISM (XML)
PRISM_CONFIG = {
    "provider_name": "PRISM",
    "fetch_strategy": "xml",
    "items_path": ".//record",
    "namespaces": {
        "prism": "http://prismstandard.org/namespaces/basic/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/"
    },
    "field_mapping": {
        "title": {"type": "xml", "path": "dc:title"},
        "authors": {"type": "xml", "path": "dc:creator"},
        "abstract": {"type": "xml", "path": "prism:abstract"},
        "doi": {"type": "xml", "path": "prism:doi"},
        "publication_date": {"type": "xml", "path": "prism:publicationDate"},
        "provider_id": {"type": "xml", "path": "prism:aggregationType"},
        "url": {"type": "xml", "path": "prism:url"},
        "journal": {"type": "xml", "path": "prism:publicationName"},
    }
}

# IEEE (REST API)
IEEE_CONFIG = {
    "provider_name": "IEEE",
    "fetch_strategy": "rest",
    "base_url": "https://ieeexploreapi.ieee.org/api/v1/search",
    "params": {"apiKey": "YOUR_IEEE_API_KEY"},
    "items_path": ["articles"],
    "field_mapping": {
        "title": "title",
        "authors": {
            "type": "list",
            "path": "authors",
            "key": "name"
        },
        "abstract": "abstract",
        "doi": "doi",
        "publication_date": "publication_date",
        "provider_id": "article_number",
        "url": "html_url",
    }
}
