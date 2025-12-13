"""
Database utility functions with retry logic.
"""

import time
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError, PendingRollbackError

logger = logging.getLogger(__name__)


def retry_db_operation(max_retries=6, initial_delay=2, max_delay=10, backoff_factor=2):
    """
    Decorator to retry database operations with exponential backoff.
    Handles session rollback on connection errors.

    Args:
        max_retries: Maximum number of retry attempts (default: 6, total ~60 seconds)
        initial_delay: Initial delay in seconds before first retry (default: 2)
        max_delay: Maximum delay between retries in seconds (default: 10)
        backoff_factor: Multiplier for exponential backoff (default: 2)

    Total retry time: ~2 + 4 + 8 + 10 + 10 + 10 = ~44 seconds (up to 60s with jitter)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, PendingRollbackError) as e:
                    last_exception = e
                    
                    # Roll back the session to clear invalid transaction state
                    try:
                        from .extensions import db
                        db.session.rollback()
                        logger.debug("Session rolled back due to database error")
                    except Exception as rollback_error:
                        logger.warning(f"Failed to rollback session: {rollback_error}")
                    
                    # Handle PendingRollbackError - this means we need to retry
                    if isinstance(e, PendingRollbackError):
                        if attempt < max_retries:
                            logger.warning(
                                f"Pending rollback error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                                f"Retrying in {delay} seconds..."
                            )
                            time.sleep(delay)
                            delay = min(delay * backoff_factor, max_delay)
                            continue
                        else:
                            logger.error(
                                f"Pending rollback error after {max_retries + 1} attempts: {e}"
                            )
                            raise
                    
                    # Handle OperationalError (connection/timeout errors)
                    error_code = getattr(e.orig, 'args', [None])[0] if hasattr(e, 'orig') else None

                    # Check if it's a timeout or connection error
                    if error_code in ('HYT00', '08S01', '08001') or 'timeout' in str(e).lower():
                        if attempt < max_retries:
                            logger.warning(
                                f"Database connection failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                                f"Retrying in {delay} seconds..."
                            )
                            time.sleep(delay)
                            delay = min(delay * backoff_factor, max_delay)
                        else:
                            logger.error(
                                f"Database connection failed after {max_retries + 1} attempts: {e}"
                            )
                    else:
                        # Not a connection/timeout error, re-raise immediately
                        raise
                except Exception as e:
                    # Non-operational errors, re-raise immediately
                    raise

            # If we exhausted all retries, raise the last exception
            raise last_exception

        return wrapper
    return decorator


def test_db_connection(db):
    """
    Test database connection with retry logic.

    Args:
        db: SQLAlchemy database instance

    Returns:
        bool: True if connection successful, False otherwise
    """
    from sqlalchemy import text

    @retry_db_operation(max_retries=6, initial_delay=2, max_delay=10)
    def _test_connection():
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True

    try:
        return _test_connection()
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

