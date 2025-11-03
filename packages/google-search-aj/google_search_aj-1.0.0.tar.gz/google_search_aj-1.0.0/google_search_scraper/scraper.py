"""
Core scraper functionality for google-search-scraper
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import random
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict

from .exceptions import GoogleSearchError, RateLimitError, BrowserError, SearchTimeoutError


@dataclass
class SearchResult:
    """Container for search results"""
    query: str
    answer: Optional[str]
    urls: List[str]
    total_results: int
    search_time: float
    timestamp: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def __repr__(self) -> str:
        return f"SearchResult(query='{self.query}', urls={len(self.urls)}, time={self.search_time:.2f}s)"


class GoogleSearchScraper:
    """Main scraper class with configurable options"""
    
    def __init__(
        self,
        max_results: int = 10,
        timeout: int = 30000,
        headless: bool = True,
        stealth_mode: bool = True,
        user_agent: Optional[str] = None
    ):
        """
        Initialize the scraper
        
        Args:
            max_results: Maximum number of URLs to return (default: 10)
            timeout: Page load timeout in milliseconds (default: 30000)
            headless: Run browser in headless mode (default: True)
            stealth_mode: Enable stealth features to avoid detection (default: True)
            user_agent: Custom user agent string (default: None, uses realistic UA)
        """
        self.max_results = max_results
        self.timeout = timeout
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
    
    def _setup_browser(self, playwright):
        """Setup browser with stealth options"""
        try:
            browser = playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
            return browser
        except Exception as e:
            raise BrowserError(f"Failed to launch browser: {e}")
    
    def _setup_context(self, browser):
        """Setup browser context with realistic fingerprint"""
        context = browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        )
        
        if self.stealth_mode:
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [{
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        name: "Chrome PDF Plugin"
                    }]
                });
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """)
        
        return context
    
    def _handle_cookies(self, page):
        """Handle cookie consent banners"""
        try:
            cookie_buttons = [
                "#L2AGLb",
                "button:has-text('Reject all')",
                "button:has-text('Accept all')"
            ]
            for selector in cookie_buttons:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click(timeout=2000)
                    break
        except:
            pass
    
    def _extract_answer(self, page) -> Optional[str]:
        """Extract Google's direct answer if available"""
        answer_selectors = [
            "div.IZ6rdc",
            "span.hgKElc",
            "div.LGOjhe",
            "div.ayRjaf",
            "span#cwos",
            "div.VwiC3b"
        ]
        
        for selector in answer_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text and len(text) >= 10:
                        return text
            except:
                continue
        
        return None
    
    def _extract_urls(self, page) -> List[str]:
        """Extract search result URLs"""
        url_selectors = [
            "div#rso a[href^='http']",
            "div.g a[href^='http']",
            "div#search a[href^='http']"
        ]
        
        all_links = []
        for selector in url_selectors:
            try:
                links = page.locator(selector).all()
                all_links.extend(links)
                if len(all_links) >= self.max_results * 3:
                    break
            except:
                continue
        
        # Filter excluded domains
        excluded = [
            'google.com/search',
            'google.com/url',
            'accounts.google.com',
            'webcache.googleusercontent.com',
            'maps.google.com',
            'support.google.com'
        ]
        
        urls = []
        seen = set()
        
        for link in all_links:
            if len(urls) >= self.max_results:
                break
            
            try:
                href = link.get_attribute("href")
                if not href or not href.startswith('http'):
                    continue
                
                if any(ex in href for ex in excluded):
                    continue
                
                if href not in seen:
                    seen.add(href)
                    urls.append(href)
            except:
                continue
        
        return urls
    
    def search(self, query: str, extract_answer: bool = True) -> SearchResult:
        """
        Perform a Google search
        
        Args:
            query: Search query string
            extract_answer: Whether to extract Google's direct answer (default: True)
        
        Returns:
            SearchResult object containing answer and URLs
        
        Raises:
            GoogleSearchError: Base exception for all errors
            RateLimitError: When rate limited by Google
            BrowserError: When browser fails
            SearchTimeoutError: When search times out
        """
        start_time = time.time()
        
        with sync_playwright() as p:
            browser = self._setup_browser(p)
            context = self._setup_context(browser)
            page = context.new_page()
            
            try:
                # Navigate to Google
                page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=self.timeout)
                time.sleep(0.8)
                
                # Handle cookies
                self._handle_cookies(page)
                time.sleep(0.3)
                
                # Find and fill search box
                try:
                    search_box = page.locator("textarea[name='q'], input[name='q']").first
                except:
                    raise GoogleSearchError("Could not find search box")
                
                search_box.click()
                time.sleep(0.2)
                
                # Type query with human-like delays
                for char in query:
                    search_box.type(char, delay=random.randint(50, 100))
                
                time.sleep(0.3)
                search_box.press("Enter")
                
                # Wait for results
                try:
                    page.wait_for_selector("div#search, div#rso", timeout=self.timeout)
                except PlaywrightTimeoutError:
                    raise SearchTimeoutError(f"Search timed out after {self.timeout}ms")
                
                time.sleep(1.2)
                
                # Check if we're being blocked
                page_content = page.content().lower()
                if 'unusual traffic' in page_content or 'captcha' in page_content:
                    raise RateLimitError("Google is blocking automated requests. Try again later or use visible mode.")
                
                # Extract results
                answer = self._extract_answer(page) if extract_answer else None
                urls = self._extract_urls(page)
                
                search_time = time.time() - start_time
                
                return SearchResult(
                    query=query,
                    answer=answer,
                    urls=urls,
                    total_results=len(urls),
                    search_time=search_time,
                    timestamp=time.time()
                )
                
            except PlaywrightTimeoutError as e:
                raise SearchTimeoutError(f"Operation timed out: {e}")
            except (RateLimitError, SearchTimeoutError, BrowserError):
                raise
            except Exception as e:
                raise GoogleSearchError(f"Search failed: {e}")
            finally:
                context.close()
                browser.close()


def search(
    query: str,
    max_results: int = 10,
    extract_answer: bool = True,
    headless: bool = True,
    timeout: int = 30000
) -> SearchResult:
    """
    Convenience function to perform a quick Google search
    
    Args:
        query: Search query string
        max_results: Maximum number of URLs to return (default: 10)
        extract_answer: Whether to extract Google's direct answer (default: True)
        headless: Run browser in headless mode (default: True)
        timeout: Page load timeout in milliseconds (default: 30000)
    
    Returns:
        SearchResult object
    
    Example:
        >>> from google_search_scraper import search
        >>> results = search("python tutorial", max_results=5)
        >>> print(results.urls)
        ['https://docs.python.org/3/tutorial/', ...]
    """
    scraper = GoogleSearchScraper(
        max_results=max_results,
        timeout=timeout,
        headless=headless,
        stealth_mode=True
    )
    return scraper.search(query, extract_answer=extract_answer)

