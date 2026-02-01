"""Base utilities for seed commands to suppress SQL logging."""

import logging
from contextlib import contextmanager


@contextmanager
def suppress_sql_logging():
    """Temporarily suppress Django's SQL query logging.

    This is useful for seed commands that execute many database operations,
    as the SQL output can be overwhelming and obscure the actual progress.
    """
    # Get the django.db.backends logger
    logger = logging.getLogger("django.db.backends")

    # Store original level
    original_level = logger.level

    try:
        # Set to WARNING to suppress DEBUG/INFO SQL logs
        logger.setLevel(logging.WARNING)
        yield
    finally:
        # Restore original level
        logger.setLevel(original_level)
