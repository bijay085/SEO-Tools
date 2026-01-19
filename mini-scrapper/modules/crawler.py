"""Core web crawler module."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any
import requests

from .config import load_config
from .url_utils import get_domain, is_same_domain, is_path_excluded, contains_priority_path
from .link_extractor import extract_links
from .schema_extractor import (
    extract_json_ld_schemas, search_variables,
    extract_business_info, merge_business_info, format_business_report
)
from .file_handler import save_page_with_schema
from . import display

REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Priority pages for business info extraction
BUSINESS_PAGES = ["/", "/about", "/about-us", "/contact", "/contact-us", 
                  "/services", "/locations", "/reviews", "/testimonials"]


@dataclass
class CrawlResults:
    """Container for crawl results."""
    total_pages_crawled: int = 0
    priority_pages_found: int = 0
    priority_pages_with_schema: int = 0
    remaining_pages_found: int = 0
    remaining_pages_with_schema: int = 0
    priority_schemas_found: List[str] = field(default_factory=list)
    remaining_schemas_found: List[str] = field(default_factory=list)
    business_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def priority_pages_without_schema(self) -> int:
        return self.priority_pages_found - self.priority_pages_with_schema

    @property
    def remaining_pages_without_schema(self) -> int:
        return self.remaining_pages_found - self.remaining_pages_with_schema

    def to_dict(self) -> dict:
        return {
            "total_pages_crawled": self.total_pages_crawled,
            "priority_pages_found": self.priority_pages_found,
            "priority_pages_with_schema": self.priority_pages_with_schema,
            "priority_pages_without_schema": self.priority_pages_without_schema,
            "remaining_pages_found": self.remaining_pages_found,
            "remaining_pages_with_schema": self.remaining_pages_with_schema,
            "remaining_pages_without_schema": self.remaining_pages_without_schema,
            "priority_schemas_found": self.priority_schemas_found,
            "remaining_schemas_found": self.remaining_schemas_found,
            "business_info": self.business_info,
        }


def _fetch_page(url: str) -> tuple[requests.Response | None, int | None, Exception | None]:
    """Fetch a page. Returns (response, status_code, error)."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        return resp, resp.status_code, None
    except requests.RequestException as e:
        code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        return None, code, e


def _init_business_info() -> Dict[str, Any]:
    """Initialize empty business info dict."""
    return {
        "rating": None, "review_count": None, "addresses": [], "areas_served": [],
        "hours": "", "phones": [], "quote_url": "", "services": [],
        "has_coupon": False, "has_emergency": False, "is_licensed": False,
        "license_number": "", "business_name": "", "founding_date": "", "founders": [],
    }


def _is_business_info_complete(info: Dict[str, Any]) -> bool:
    """Check if ALL business info fields are found."""
    # All required fields - must have ALL of these
    required_fields = {
        "business_name": lambda v: bool(v),
        "phones": lambda v: len(v) > 0,
        "addresses": lambda v: len(v) > 0,
        "services": lambda v: len(v) > 0,
        "hours": lambda v: bool(v),
    }
    
    # Check if ALL required fields are found
    return all(check(info.get(key, None)) for key, check in required_fields.items())


def scrape_business(start_url: str) -> Dict[str, Any]:
    """
    Scrape business info from key pages (homepage, about, contact, services).
    Returns business info dict.
    """
    domain = get_domain(start_url)
    base_url = f"https://{domain}"
    business_info = _init_business_info()
    scraped = set()
    
    print(f"\n{'=' * 60}")
    print(f"Scraping business info from: {domain}")
    print(f"{'=' * 60}\n")
    
    # Build URLs to scrape
    urls_to_scrape = [start_url]
    for path in BUSINESS_PAGES:
        url = base_url + path
        if url not in urls_to_scrape:
            urls_to_scrape.append(url)
    
    for url in urls_to_scrape:
        if url.rstrip("/") in scraped or url in scraped:
            continue
        
        print(f"[Fetching] {url}")
        response, status, error = _fetch_page(url)
        
        if error or status != 200:
            print(f"  [Status] {status or 'Failed'} - Skipped")
            continue
        
        print(f"  [Status] {status}")
        scraped.add(url)
        scraped.add(url.rstrip("/"))
        
        # Extract schemas
        schemas = extract_json_ld_schemas(response.text)
        if schemas:
            print(f"  [Schema] Found {len(schemas)}")
        
        # Extract business info and merge
        page_info = extract_business_info(schemas, response.text, base_url)
        merge_business_info(business_info, page_info)
    
    print(f"\n[Scraped {len(scraped)} pages]")
    print(format_business_report(business_info))
    
    return business_info


def scrape_priority_paths(start_url: str, max_pages: int = 1000) -> dict:
    """
    Crawl pages, extracting JSON-LD schemas and business info.
    Returns results dictionary.
    """
    config = load_config()
    start_domain = get_domain(start_url)
    base_url = f"https://{start_domain}"
    visited: Set[str] = set()
    
    # Always start from homepage (domain root)
    homepage_url = f"https://{start_domain}/"
    to_visit: deque[str] = deque([homepage_url])
    
    results = CrawlResults(business_info=_init_business_info())

    # Keep crawling until ALL fields found OR all pages crawled
    while results.total_pages_crawled < max_pages:
        # Stop if queue empty AND info complete
        if not to_visit:
            if _is_business_info_complete(results.business_info):
                display.print_success("All required business info found! No more pages to crawl.")
                break
            else:
                display.print_warning(f"Queue empty but missing info. Crawled {results.total_pages_crawled} pages. Stopping.")
                break
        
        url = to_visit.popleft()
        
        if url in visited:
            continue
        
        visited.add(url)
        is_blocked = is_path_excluded(url, config.exclude_paths)
        
        if is_blocked:
            display.print_info("Skipped (blocked)", url)
            continue
        
        response, status_code, error = _fetch_page(url)
        
        display.print_info("Crawler", url)
        display.print_status_code(status_code)

        if error:
            display.print_error(f"Error - {error}")
            display.print_schema_check(False, False)
            display.print_separator()
            continue

        results.total_pages_crawled += 1
        is_priority = contains_priority_path(url, config.priority_paths)
        status = "Priority page" if is_priority else "Other page"
        display.print_crawl_status(status, is_priority=is_priority)

        # Extract schemas
        schemas = extract_json_ld_schemas(response.text)
        has_schema = len(schemas) > 0
        display.print_schema_check(True, has_schema, len(schemas))

        if has_schema:
            save_page_with_schema(url, response.text, schemas)

        # Extract business info from pages with schemas (prioritize priority pages)
        if is_priority:
            results.priority_pages_found += 1
            if has_schema:
                results.priority_pages_with_schema += 1
                results.priority_schemas_found.append(url)
        else:
            results.remaining_pages_found += 1
            if has_schema:
                results.remaining_pages_with_schema += 1
                results.remaining_schemas_found.append(url)
        
        # Extract and merge business info from any page with schemas
        if has_schema:
            page_info = extract_business_info(schemas, response.text, base_url)
            merge_business_info(results.business_info, page_info)
        
        # Check if we have ALL required info - stop only when ALL found OR no more pages to crawl
        info_complete = _is_business_info_complete(results.business_info)
        if info_complete:
            if len(to_visit) == 0:
                display.print_success("All required business info found! Crawl complete.")
                break
            else:
                display.print_info("Info", f"All required business info found! Finishing {len(to_visit)} remaining pages...")

        display.print_separator()

        # Extract and queue links
        links = extract_links(url, response.text)
        new_count, external_count = 0, 0
        
        for link in links:
            if not is_same_domain(link, start_domain):
                external_count += 1
                continue
            if link in visited or link in to_visit:
                continue
            if is_path_excluded(link, config.exclude_paths):
                visited.add(link)
                continue
            to_visit.append(link)
            new_count += 1
        
        if links:
            display.print_link_stats(len(links), new_count, external_count, len(to_visit))

    # Print business report at end
    print(format_business_report(results.business_info))
    
    return results.to_dict()