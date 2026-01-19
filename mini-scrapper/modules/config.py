"""Configuration loading module."""
from __future__ import annotations
import json
import os
from typing import List
from dataclasses import dataclass, field

# Config is inside modules/config/
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
# Support both scrapper.json and scraper.json (fallback)
_scrapper_path = os.path.join(CONFIG_DIR, "scrapper.json")
_scraper_path = os.path.join(CONFIG_DIR, "scraper.json")
CONFIG_PATH = _scrapper_path if os.path.exists(_scrapper_path) else _scraper_path


@dataclass
class ScraperConfig:
    """Scraper configuration container."""
    exclude_paths: List[str] = field(default_factory=list)
    priority_paths: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)


def _normalize_path(path: str) -> str | None:
    """Normalize a path string, ensuring it starts with /."""
    if not isinstance(path, str):
        return None
    path = path.strip()
    if not path:
        return None
    return path if path.startswith("/") else "/" + path


def load_config() -> ScraperConfig:
    """Load and parse configuration from scraper.json."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return ScraperConfig()

    exclude = [p for p in map(_normalize_path, data.get("exclude_paths", [])) if p]
    priority = [p for p in map(_normalize_path, data.get("priority_paths", [])) if p]
    variables = [v.strip() for v in data.get("variables", []) if isinstance(v, str) and v.strip()]

    return ScraperConfig(exclude_paths=exclude, priority_paths=priority, variables=variables)


# Convenience functions for backward compatibility
def load_excluded_paths() -> List[str]:
    return load_config().exclude_paths

def load_priority_paths() -> List[str]:
    return load_config().priority_paths

def load_variables() -> List[str]:
    return load_config().variables