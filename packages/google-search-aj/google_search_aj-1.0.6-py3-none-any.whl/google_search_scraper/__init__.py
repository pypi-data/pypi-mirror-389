"""
Google Search Scraper
~~~~~~~~~~~~~~~~~~~~~

A fast, lightweight Google search scraper with stealth mode.

Basic usage:

   >>> from google_search_scraper import search
   >>> results = search("python tutorial")
   >>> print(results.urls)
   ['https://docs.python.org/3/tutorial/', ...]

:copyright: (c) 2024 by Aditya Jangam.
:license: MIT, see LICENSE for more details.
"""

__version__ = "1.0.0"
__author__ = "Aditya Jangam"
__license__ = "MIT"

from .scraper import search, SearchResult, GoogleSearchScraper
from .exceptions import GoogleSearchError, RateLimitError, BrowserError, SearchTimeoutError, NoResultsError

__all__ = [
    "search",
    "SearchResult",
    "GoogleSearchScraper",
    "GoogleSearchError",
    "RateLimitError",
    "BrowserError",
    "SearchTimeoutError",
    "NoResultsError",
    "__version__",
]

