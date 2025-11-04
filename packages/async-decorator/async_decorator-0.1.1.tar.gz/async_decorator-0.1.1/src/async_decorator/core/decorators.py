"""Execution type decorators for async-decorator."""

import asyncio
from functools import wraps
from typing import Callable, Any, Optional

from .types import ExecType
from .manager import get_thread_manager
from ..utils.exceptions import InvalidExecTypeError
from ..utils.validators import validate_endpoint_name


def async_decorator(
        exec_type: ExecType,
        endpoint_name: Optional[str] = '',
        shared_pool_size: int = 100,
        thread_manager=None,
) -> Callable:
    """
    Decorator to specify execution type for functions.

    Args:
        exec_type: Type of execution (EXCLUSIVE, SHARED_POOL)
        endpoint_name: Optional unique name for exclusive thread
        shared_pool_size: Optional Maximum workers for shared async pool
        thread_manager: Optional custom thread manager instance

    Returns:
        Callable: Decorated function

    Raises:
        InvalidExecTypeError: If invalid execution type is provided
    """

    def decorator(func: Callable) -> Callable:
        actual_endpoint_name = validate_endpoint_name(endpoint_name or func.__name__)
        manager = thread_manager or get_thread_manager(shared_pool_size)
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            loop = asyncio.get_event_loop()
            if exec_type == ExecType.EXCLUSIVE:
                # Execute in dedicated thread pool
                pool = manager.get_dedicated_pool(actual_endpoint_name)
            elif exec_type == ExecType.SHARED_POOL:
                # Execute in shared thread pool
                pool = manager.async_shared_pool
            else:
                raise InvalidExecTypeError(f"Unsupported execution type: {exec_type}")
            if is_coroutine:
                return await loop.run_in_executor(pool, lambda: asyncio.run(func(*args, **kwargs)))
            return await loop.run_in_executor(pool, lambda: func(*args, **kwargs))

        return wrapper

    return decorator
