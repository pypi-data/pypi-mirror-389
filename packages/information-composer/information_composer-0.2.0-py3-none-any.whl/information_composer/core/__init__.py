"""
Core module for Information Composer.

This module provides base functionality for downloading and processing
academic papers and other content.
"""

from typing import TYPE_CHECKING

from .doi_downloader import DOIDownloader
from .downloader import BaseDownloader


if TYPE_CHECKING:
    from .doi_downloader import BatchDownloadStats, DownloadResult

__all__ = [
    "BaseDownloader",
    "BatchDownloadStats",
    "DOIDownloader",
    # Type hints
    "DownloadResult",
]
