"""URL utility functions."""
from __future__ import annotations
from urllib.parse import urlparse, urljoin, urlunparse
from typing import List
import re
import os


def normalize_url(base_url: str, url: str | None) -> str | None:
    """Normalize a URL relative to a base URL."""
    if not url:
        return None
    
    url = url.strip()
    if not url:
        return None
    
    # Handle fragment-only URLs
    if url.startswith("#"):
        return None
    
    # Handle javascript:, mailto:, tel:, etc.
    if ":" in url and not url.startswith(("http://", "https://", "/")):
        scheme = url.split(":")[0]
        if scheme not in ("http", "https"):
            return None
    
    try:
        # Join with base URL to handle relative URLs
        full_url = urljoin(base_url, url)
        parsed = urlparse(full_url)
        
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ""  # Remove fragment
        ))
        
        # Remove trailing slash for consistency (except root)
        if normalized.endswith("/") and len(parsed.path) > 1:
            normalized = normalized[:-1]
        
        return normalized
    except Exception:
        return None


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def is_same_domain(url: str, domain: str) -> bool:
    """Check if URL belongs to the same domain."""
    url_domain = get_domain(url)
    return url_domain == domain.lower() if url_domain and domain else False


def is_path_excluded(url: str, exclude_paths: List[str]) -> bool:
    """Check if URL path is in the exclude list."""
    try:
        parsed = urlparse(url)
        path = parsed.path
        
        # Normalize path - ensure it starts with /
        if not path.startswith("/"):
            path = "/" + path
        
        # Remove trailing slash for comparison (except root)
        normalized_path = path.rstrip("/") if path != "/" else "/"
        
        for exclude_path in exclude_paths:
            # Normalize exclude path - remove trailing slash
            normalized_exclude = exclude_path.rstrip("/") if exclude_path != "/" else "/"
            
            # Check if path starts with exclude path
            if normalized_path.startswith(normalized_exclude):
                # Ensure it's not a partial match (e.g., /collections shouldn't match /collection)
                # Check if it's an exact match or followed by /
                if normalized_path == normalized_exclude or normalized_path.startswith(normalized_exclude + "/"):
                    return True
        return False
    except Exception:
        return False


def contains_priority_path(url: str, priority_paths: List[str]) -> bool:
    """Check if URL path is in the priority list."""
    try:
        parsed = urlparse(url)
        path = parsed.path
        
        # Normalize path - ensure it starts with /
        if not path.startswith("/"):
            path = "/" + path
        
        # Remove trailing slash for comparison (except root)
        normalized_path = path.rstrip("/") if path != "/" else "/"
        
        # Special handling for root path "/"
        if "/" in priority_paths:
            if normalized_path == "/":
                return True
        
        for priority_path in priority_paths:
            # Skip root path as it's handled above
            if priority_path == "/":
                continue
            
            # Normalize priority path - remove trailing slash
            normalized_priority = priority_path.rstrip("/") if priority_path != "/" else "/"
            
            # Check if path starts with priority path
            if normalized_path.startswith(normalized_priority):
                # Ensure it's not a partial match (e.g., /about shouldn't match /ab)
                # Check if it's an exact match or followed by /
                if normalized_path == normalized_priority or normalized_path.startswith(normalized_priority + "/"):
                    return True
        return False
    except Exception:
        return False


def create_safe_filename(url: str) -> str:
    """Create a safe filename from a URL."""
    try:
        parsed = urlparse(url)
        # Combine domain and path
        parts = [parsed.netloc] if parsed.netloc else []
        
        # Clean path
        path = parsed.path.strip("/")
        if path:
            # Replace slashes with underscores
            path = path.replace("/", "_")
            parts.append(path)
        
        # Combine parts
        filename = "_".join(parts) if parts else "index"
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename or "index"
    except Exception:
        return "page"
