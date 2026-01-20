"""Error handling utilities and retry logic."""
from __future__ import annotations
import time
import requests
from typing import Callable, TypeVar, Optional, Tuple, Any
from functools import wraps
from .logger import default_logger

T = TypeVar('T')

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1
DEFAULT_RETRYABLE_STATUS_CODES = {500, 502, 503, 504, 429}


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class NetworkError(ScraperError):
    """Network-related errors."""
    pass


class ParsingError(ScraperError):
    """HTML/JSON parsing errors."""
    pass


class ConfigurationError(ScraperError):
    """Configuration-related errors."""
    pass


def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    retryable_exceptions: Tuple[type, ...] = (requests.RequestException,),
    retryable_status_codes: set[int] = DEFAULT_RETRYABLE_STATUS_CODES
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff delay
        retryable_exceptions: Tuple of exception types to retry on
        retryable_status_codes: Set of HTTP status codes to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Check if result is a response tuple (response, status_code, error)
                    if isinstance(result, tuple) and len(result) == 3:
                        response, status_code, error = result
                        
                        # If there's an error or retryable status code, retry
                        if error and attempt < max_retries:
                            if isinstance(error, retryable_exceptions):
                                wait_time = backoff_factor * (2 ** attempt)
                                default_logger.warning(
                                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {error}. "
                                    f"Retrying in {wait_time:.2f}s..."
                                )
                                time.sleep(wait_time)
                                continue
                        
                        # If status code is retryable, retry
                        if status_code in retryable_status_codes and attempt < max_retries:
                            wait_time = backoff_factor * (2 ** attempt)
                            default_logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} returned status {status_code}. "
                                f"Retrying in {wait_time:.2f}s..."
                            )
                            time.sleep(wait_time)
                            continue
                    
                    return result
                    
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        default_logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} raised {type(e).__name__}: {e}. "
                            f"Retrying in {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        default_logger.error(
                            f"All {max_retries + 1} attempts failed. Last error: {e}"
                        )
                        raise
                except Exception as e:
                    # Non-retryable exceptions are raised immediately
                    default_logger.error(f"Non-retryable error: {e}")
                    raise
            
            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise ScraperError("Function failed after all retries")
        
        return wrapper
    return decorator


def safe_execute(func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[Optional[T], Optional[Exception]]:
    """
    Safely execute a function and return result or error.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Tuple of (result, error). One will be None.
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        default_logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
        return None, e
