"""
Utility decorators for the cross-chain framework.

This module provides decorators for common patterns in cross-chain communication.
"""

import functools
import time
from typing import Any, Callable, TypeVar

from langgraph_crosschain.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry a function if it raises specified exceptions.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function

    Example:
        >>> @retry(max_attempts=3, delay=1.0)
        ... def unreliable_function():
        ...     # might fail
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay}s: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached, but for type checking
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def log_call(
    level: int = 20,  # INFO
    include_args: bool = True,
    include_result: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Log function calls with arguments and results.

    Args:
        level: Logging level to use
        include_args: Whether to log function arguments
        include_result: Whether to log function result

    Returns:
        Decorated function

    Example:
        >>> @log_call(include_args=True)
        ... def my_function(x, y):
        ...     return x + y
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            func_logger = get_logger(func.__module__)

            if include_args:
                args_repr = ", ".join(repr(a) for a in args)
                kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
                all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
                func_logger.log(level, f"Calling {func.__name__}({all_args})")
            else:
                func_logger.log(level, f"Calling {func.__name__}")

            result = func(*args, **kwargs)

            if include_result:
                func_logger.log(level, f"{func.__name__} returned {result!r}")
            else:
                func_logger.log(level, f"{func.__name__} completed")

            return result

        return wrapper

    return decorator


def measure_time(
    log_result: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Measure and optionally log execution time of a function.

    Args:
        log_result: Whether to log the execution time

    Returns:
        Decorated function with a `last_execution_time` attribute

    Example:
        >>> @measure_time()
        ... def slow_function():
        ...     time.sleep(1)
        >>> slow_function()
        >>> print(slow_function.last_execution_time)
        1.0...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Store execution time as attribute
            wrapper.last_execution_time = execution_time  # type: ignore

            if log_result:
                func_logger = get_logger(func.__module__)
                func_logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")

            return result

        wrapper.last_execution_time = 0.0  # type: ignore
        return wrapper

    return decorator


def validate_chain_registered(
    chain_param: str = "chain_id",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Validate that a chain is registered before executing the function.

    Args:
        chain_param: Name of the parameter containing the chain ID

    Returns:
        Decorated function

    Example:
        >>> @validate_chain_registered()
        ... def process_chain(chain_id: str):
        ...     # process the chain
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            from langgraph_crosschain.core.chain_registry import ChainRegistry
            from langgraph_crosschain.exceptions import ChainNotFoundError

            # Try to get chain_id from kwargs first, then from args
            chain_id = kwargs.get(chain_param)

            if chain_id is None:
                # Try to get from args based on function signature
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if chain_param in param_names:
                    param_index = param_names.index(chain_param)
                    if param_index < len(args):
                        chain_id = args[param_index]

            if chain_id is not None:
                registry = ChainRegistry()
                if chain_id not in registry:
                    raise ChainNotFoundError(chain_id)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def thread_safe(func: Callable[..., T]) -> Callable[..., T]:
    """
    Make a function thread-safe using a lock.

    Note: This creates a lock per function, not per instance.
    For instance-level thread safety, use instance locks.

    Args:
        func: The function to make thread-safe

    Returns:
        Thread-safe version of the function

    Example:
        >>> @thread_safe
        ... def update_shared_data():
        ...     # update shared data
        ...     pass
    """
    import threading

    lock = threading.RLock()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        with lock:
            return func(*args, **kwargs)

    return wrapper
