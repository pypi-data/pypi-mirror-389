"""Thread pool manager implementation."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from threading import Lock

from ..utils.exceptions import PoolCreationError, ShutdownError
from .types import PoolDict


class DedicatedThreadManager:
    """
    Managed thread pool executor for async/sync function execution.

    This class provides dedicated thread pools for synchronous functions
    and shared thread pools for asynchronous functions.

    Args:
        shared_pool_size: Maximum workers for shared async pool
        max_dedicated_pools: Maximum number of dedicated pools to create
        logger: Custom logger instance
    """

    def __init__(
            self,
            shared_pool_size: int = 100,
            max_dedicated_pools: int = 100,
            logger: Optional[logging.Logger] = None,
    ):
        self.dedicated_pool_size = 1
        self.shared_pool_size = shared_pool_size
        self.max_dedicated_pools = max_dedicated_pools

        self.logger = logger or logging.getLogger(__name__)
        self._lock = Lock()
        self._shutdown = False

        # Thread pools
        self.dedicated_pools: PoolDict = {}
        self.async_shared_pool: Optional[ThreadPoolExecutor] = None

        self._initialize_pools()

    def _initialize_pools(self) -> None:
        """Initialize thread pools."""
        try:
            self.async_shared_pool = ThreadPoolExecutor(
                max_workers=self.shared_pool_size,
                thread_name_prefix="async_shared_"
            )
            self.logger.debug("Initialized shared thread pool with %d workers",
                              self.shared_pool_size)
        except Exception as e:
            raise PoolCreationError(f"Failed to create shared thread pool: {e}") from e

    def get_dedicated_pool(self, endpoint_name: str) -> ThreadPoolExecutor:
        """
        Get or create a dedicated thread pool for the given endpoint.

        Args:
            endpoint_name: Unique identifier for the endpoint

        Returns:
            ThreadPoolExecutor: The dedicated thread pool

        Raises:
            ShutdownError: If manager is shutdown
            PoolCreationError: If pool creation fails or limit reached
        """
        if self._shutdown:
            raise ShutdownError("Thread manager is shutdown")

        with self._lock:
            if endpoint_name in self.dedicated_pools:
                return self.dedicated_pools[endpoint_name]

            if len(self.dedicated_pools) >= self.max_dedicated_pools:
                raise PoolCreationError(
                    f"Maximum dedicated pools ({self.max_dedicated_pools}) reached"
                )

            try:
                pool = ThreadPoolExecutor(
                    max_workers=self.dedicated_pool_size,
                    thread_name_prefix=f"dedicated_{endpoint_name}_"
                )
                self.dedicated_pools[endpoint_name] = pool
                self.logger.info("Created dedicated thread pool: %s", endpoint_name)
                return pool
            except Exception as e:
                raise PoolCreationError(
                    f"Failed to create dedicated pool for {endpoint_name}: {e}"
                ) from e

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown all thread pools.

        Args:
            wait: Whether to wait for thread pool shutdown
        """
        if self._shutdown:
            return

        self._shutdown = True
        self.logger.info("Shutting down thread manager...")

        # Shutdown dedicated pools
        for name, pool in self.dedicated_pools.items():
            try:
                pool.shutdown(wait=wait)
                self.logger.debug("Shutdown dedicated pool: %s", name)
            except Exception as e:
                self.logger.warning("Error shutting down pool %s: %s", name, e)

        # Shutdown shared pool
        if self.async_shared_pool:
            try:
                self.async_shared_pool.shutdown(wait=wait)
                self.logger.debug("Shutdown shared pool")
            except Exception as e:
                self.logger.warning("Error shutting down shared pool: %s", e)

        self.dedicated_pools.clear()
        self.async_shared_pool = None

    @property
    def is_shutdown(self) -> bool:
        """Check if manager is shutdown."""
        return self._shutdown

    @property
    def dedicated_pool_count(self) -> int:
        """Get number of dedicated pools."""
        return len(self.dedicated_pools)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)


# Global thread manager instance
_global_thread_manager: Optional[DedicatedThreadManager] = None


def get_thread_manager(
        shared_pool_size: int = 100,
        max_dedicated_pools: int = 100,
) -> DedicatedThreadManager:
    """
    Get or create the global thread manager instance.

    Args:
        shared_pool_size: Maximum workers for shared async pool
        max_dedicated_pools: Maximum number of dedicated pools to create

    Returns:
        DedicatedThreadManager: Global thread manager instance
    """
    global _global_thread_manager

    if _global_thread_manager is None or _global_thread_manager.is_shutdown:
        _global_thread_manager = DedicatedThreadManager(
            shared_pool_size=shared_pool_size,
            max_dedicated_pools=max_dedicated_pools,
        )

    return _global_thread_manager


def shutdown_global_manager(wait: bool = True) -> None:
    """Shutdown the global thread manager."""
    global _global_thread_manager
    if _global_thread_manager and not _global_thread_manager.is_shutdown:
        _global_thread_manager.shutdown(wait=wait)
