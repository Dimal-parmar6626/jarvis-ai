"""Utility decorators."""

import functools
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Retry a function on failure."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    logger.warning("Attempt %d/%d failed for %s: %s", attempt, max_attempts, func.__name__, exc)
                    time.sleep(delay)

        return wrapper

    return decorator


def timed(func: Callable) -> Callable:
    """Log the execution time of a function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug("%s executed in %.2f ms", func.__name__, elapsed)
        return result

    return wrapper
