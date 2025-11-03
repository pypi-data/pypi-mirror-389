"""
Custom exceptions for google-search-scraper
"""


class GoogleSearchError(Exception):
    """Base exception for all google-search-scraper errors"""
    pass


class RateLimitError(GoogleSearchError):
    """Raised when Google rate limits or blocks the request"""
    pass


class BrowserError(GoogleSearchError):
    """Raised when browser fails to launch or navigate"""
    pass


class SearchTimeoutError(GoogleSearchError):
    """Raised when search operation times out"""
    pass


class NoResultsError(GoogleSearchError):
    """Raised when no search results are found"""
    pass

