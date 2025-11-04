"""
Async Decorator - A flexible async/sync execution library with dedicated thread pools.
"""

from .core.types import ExecType
from .core.decorators import async_decorator
from .core.manager import DedicatedThreadManager, get_thread_manager, shutdown_global_manager
from .utils.exceptions import AsyncDecoratorError, PoolCreationError

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.1.0"

__author__ = "FadsII"
__email__ = "594604366@qq.com"

__all__ = [
    "ExecType",
    "async_decorator",
    "DedicatedThreadManager",
    "get_thread_manager",
    "shutdown_global_manager",
    "AsyncDecoratorError",
    "PoolCreationError",
    "__version__",
]
