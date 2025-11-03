"""Type definitions and enums for async-decorator."""

from enum import Enum
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from concurrent.futures import ThreadPoolExecutor


class ExecType(Enum):
    """
    Execution type enumeration.

    Attributes:
        EXCLUSIVE: Execute sync functions in exclusive threads
        SHARED_POOL: Execute async functions in shared thread pool
    """
    EXCLUSIVE = "exclusive"
    SHARED_POOL = "shared_pool"


# Type aliases
PoolDict = Dict[str, "ThreadPoolExecutor"]
