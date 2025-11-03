"""
Tests for google-search-scraper package
"""

import pytest
from google_search_scraper import search, GoogleSearchScraper, SearchResult
from google_search_scraper.exceptions import (
    GoogleSearchError,
    RateLimitError,
    BrowserError,
    SearchTimeoutError
)


def test_basic_search():
    """Test basic search functionality"""
    results = search("python", max_results=5)
    
    assert isinstance(results, SearchResult)
    assert results.query == "python"
    assert len(results.urls) <= 5
    assert results.search_time > 0
    assert results.timestamp > 0


def test_search_with_answer():
    """Test search with answer extraction"""
    results = search("what is python", extract_answer=True)
    
    assert isinstance(results, SearchResult)
    # Answer might not always be available
    if results.answer:
        assert isinstance(results.answer, str)
        assert len(results.answer) > 0


def test_search_without_answer():
    """Test search without answer extraction"""
    results = search("python tutorial", extract_answer=False, max_results=3)
    
    assert isinstance(results, SearchResult)
    assert results.answer is None
    assert len(results.urls) <= 3


def test_custom_scraper():
    """Test custom scraper configuration"""
    scraper = GoogleSearchScraper(
        max_results=3,
        timeout=20000,
        headless=True,
        stealth_mode=True
    )
    
    results = scraper.search("test query")
    
    assert isinstance(results, SearchResult)
    assert len(results.urls) <= 3


def test_result_to_dict():
    """Test SearchResult to dictionary conversion"""
    results = search("test", max_results=2)
    result_dict = results.to_dict()
    
    assert isinstance(result_dict, dict)
    assert 'query' in result_dict
    assert 'urls' in result_dict
    assert 'answer' in result_dict
    assert 'total_results' in result_dict
    assert 'search_time' in result_dict
    assert 'timestamp' in result_dict


def test_search_result_repr():
    """Test SearchResult string representation"""
    results = search("test", max_results=1)
    repr_str = repr(results)
    
    assert "SearchResult" in repr_str
    assert "test" in repr_str
    assert "urls=" in repr_str


def test_empty_query():
    """Test that empty query raises appropriate error"""
    with pytest.raises(Exception):
        search("")


def test_timeout_error():
    """Test that very short timeout raises SearchTimeoutError"""
    with pytest.raises((SearchTimeoutError, GoogleSearchError)):
        search("test query", timeout=100)  # Very short timeout


def test_max_results_limit():
    """Test that max_results is respected"""
    results = search("python tutorial", max_results=7)
    
    # Should not exceed max_results
    assert len(results.urls) <= 7


@pytest.mark.parametrize("query,expected_min_results", [
    ("python", 1),
    ("javascript", 1),
    ("machine learning", 1),
])
def test_multiple_queries(query, expected_min_results):
    """Test multiple different queries"""
    results = search(query, max_results=5)
    
    assert isinstance(results, SearchResult)
    assert results.query == query
    # Should get at least some results for common queries
    assert len(results.urls) >= expected_min_results


def test_url_format():
    """Test that returned URLs are valid"""
    results = search("test", max_results=3)
    
    for url in results.urls:
        assert isinstance(url, str)
        assert url.startswith('http')
        assert 'google.com/search' not in url  # Should not include Google search URLs


def test_scraper_reusability():
    """Test that scraper can be reused for multiple searches"""
    scraper = GoogleSearchScraper(max_results=2)
    
    results1 = scraper.search("python")
    results2 = scraper.search("javascript")
    
    assert results1.query == "python"
    assert results2.query == "javascript"
    assert results1.urls != results2.urls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])