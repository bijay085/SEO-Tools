"""File handling utilities for saving scraped pages."""
from __future__ import annotations
import json
import os
from typing import List, Dict, Any
from .url_utils import create_safe_filename


SCRAPED_PAGES_DIR = "scraped_pages"


def _ensure_directory() -> None:
    """Ensure the scraped_pages directory exists."""
    if not os.path.exists(SCRAPED_PAGES_DIR):
        os.makedirs(SCRAPED_PAGES_DIR)


def save_page_with_schema(url: str, html: str, schemas: List[Dict[str, Any]]) -> None:
    """Save HTML page and JSON-LD schemas to files."""
    _ensure_directory()
    
    # Create safe filename from URL
    base_filename = create_safe_filename(url)
    
    # Save HTML file
    html_filename = os.path.join(SCRAPED_PAGES_DIR, f"{base_filename}.html")
    try:
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"Error saving HTML file {html_filename}: {e}")
    
    # Save JSON-LD schemas
    if schemas:
        json_filename = os.path.join(SCRAPED_PAGES_DIR, f"{base_filename}_schema.json")
        try:
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(schemas, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving schema file {json_filename}: {e}")
