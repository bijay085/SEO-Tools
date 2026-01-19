"""HTML link extraction module."""
from __future__ import annotations
import warnings
from typing import Set
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
from .url_utils import normalize_url

warnings.filterwarnings("ignore", category=UserWarning, module="html.parser")
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def _get_soup(html: str) -> BeautifulSoup:
    """Create BeautifulSoup instance with best available parser."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def extract_links(base_url: str, html: str) -> Set[str]:
    """Extract and normalize all links from HTML content."""
    soup = _get_soup(html)
    links: Set[str] = set()

    # Extract from <a>, <link>, and <area> tags
    for tag_name, attr in [("a", "href"), ("link", "href"), ("area", "href")]:
        for tag in soup.find_all(tag_name, **{attr: True}):
            url = normalize_url(base_url, tag.get(attr))
            if url:
                links.add(url)

    return links