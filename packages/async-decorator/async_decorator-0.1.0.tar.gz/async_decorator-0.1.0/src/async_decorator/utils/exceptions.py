"""Custom exceptions for async-decorator library."""


class AsyncDecoratorError(Exception):
    """Base exception for all async-decorator errors."""
    pass


class PoolCreationError(AsyncDecoratorError):
    """Raised when thread pool creation fails."""
    pass


class InvalidExecTypeError(AsyncDecoratorError):
    """Raised when an invalid execution type is provided."""
    pass


class ShutdownError(AsyncDecoratorError):
    """Raised when operations are attempted on a shutdown manager."""
    pass
