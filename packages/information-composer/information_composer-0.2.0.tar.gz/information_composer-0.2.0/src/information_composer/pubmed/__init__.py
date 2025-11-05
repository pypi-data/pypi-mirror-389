"""PubMed module for querying and processing PubMed database data.

This module provides comprehensive functionality for:
- Querying PubMed database with various search options
- Fetching detailed article information
- Processing Medline format data
- Baseline data processing with filtering
- Caching and batch processing
"""

from typing import TYPE_CHECKING

from .baseline import load_baseline
from .pubmed import (
    clean_pubmed_cache,
    fetch_pubmed_details,
    fetch_pubmed_details_batch,
    fetch_pubmed_details_batch_sync,
    load_pubmed_file,
    query_pmid,
    query_pmid_by_date,
)


if TYPE_CHECKING:
    from .cli.main import main as pubmed_cli
    from .core.search import PubMedSearcher

__all__ = [
    # Classes
    "PubMedSearcher",
    # Core functions
    "clean_pubmed_cache",
    "fetch_pubmed_details",
    "fetch_pubmed_details_batch",
    "fetch_pubmed_details_batch_sync",
    "load_baseline",
    "load_pubmed_file",
    # CLI
    "pubmed_cli",
    "query_pmid",
    "query_pmid_by_date",
]
