"""
Logging utilities for GIS operations.
"""

import logging
import os
import time
from functools import wraps


class Logger:
    """Configure and manage logging for GIS operations."""

    def __init__(self, name='gis_engine'):
        self.logger = logging.getLogger(name)
        self.logger.propagate = False  # prevent duplicate logs

    # --------------------------------------------------
    # Setup Logger
    # --------------------------------------------------

    def setup(self, level=logging.INFO, log_file=None):
        """
        Setup logger configuration.

        Args:
            level: Logging level.
            log_file: Optional file to write logs to.
        """

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.setLevel(level)

    # --------------------------------------------------
    # Log Methods
    # --------------------------------------------------

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def exception(self, message):
        """Log exception with traceback."""
        self.logger.exception(message)

    # --------------------------------------------------
    # Performance Timer Decorator
    # --------------------------------------------------

    def timeit(self):
        """Decorator to measure execution time of functions."""

        def decorator(func):

            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()

                duration = round(end_time - start_time, 4)
                self.logger.info(
                    f"Execution time for '{func.__name__}': {duration} seconds"
                )

                return result

            return wrapper

        return decorator