"""Web scraper modules package."""
from .config import load_config, ScraperConfig
from .crawler import scrape_priority_paths, CrawlResults
from .link_extractor import extract_links
from .schema_extractor import extract_json_ld_schemas, search_variables
from .url_utils import normalize_url, get_domain, create_safe_filename
from .file_handler import save_page_with_schema

__all__ = [
    "load_config",
    "ScraperConfig",
    "scrape_priority_paths",
    "CrawlResults",
    "extract_links",
    "extract_json_ld_schemas",
    "search_variables",
    "normalize_url",
    "get_domain",
    "create_safe_filename",
    "save_page_with_schema",
]