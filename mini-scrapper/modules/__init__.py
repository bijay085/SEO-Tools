"""Web scraper modules package."""
from .config import load_config, ScraperConfig
from .crawler import scrape_priority_paths, scrape_business, CrawlResults
from .link_extractor import extract_links
from .schema_extractor import extract_json_ld_schemas, search_variables
from .url_utils import normalize_url, get_domain, create_safe_filename
from .file_handler import save_page_with_schema
from .exporter import export_json, export_csv, export_excel, export_crawl_results, export_batch_results
from .logger import setup_logger, default_logger
from .error_handler import (
    ScraperError, NetworkError, ParsingError, ConfigurationError,
    retry_with_backoff, safe_execute
)

__all__ = [
    "load_config",
    "ScraperConfig",
    "scrape_priority_paths",
    "scrape_business",
    "CrawlResults",
    "extract_links",
    "extract_json_ld_schemas",
    "search_variables",
    "normalize_url",
    "get_domain",
    "create_safe_filename",
    "save_page_with_schema",
    "export_json",
    "export_csv",
    "export_excel",
    "export_crawl_results",
    "export_batch_results",
    "setup_logger",
    "default_logger",
    "ScraperError",
    "NetworkError",
    "ParsingError",
    "ConfigurationError",
    "retry_with_backoff",
    "safe_execute",
]