import time
from collections.abc import Callable
from functools import wraps

from loguru import logger


def timer(func: Callable):
    """
    Decorator that measures the execution time of a function.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function with timing functionality.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.success(f"Function {func.__module__}.{func.__name__}() took {duration:.3f} seconds to execute")
        return result

    return wrapper
