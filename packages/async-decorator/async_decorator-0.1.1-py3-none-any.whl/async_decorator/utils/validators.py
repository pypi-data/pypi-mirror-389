"""Validation utilities for async-decorator."""

import re
from .exceptions import AsyncDecoratorError


class ValidationError(AsyncDecoratorError):
    """Raised when validation fails."""
    pass


def validate_endpoint_name(name: str) -> str:
    """
    Validate and normalize endpoint name.

    Args:
        name: Endpoint name to validate

    Returns:
        str: Normalized endpoint name

    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Endpoint name must be a non-empty string")

    # Remove any unsafe characters
    cleaned_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    if not cleaned_name:
        raise ValidationError("Endpoint name contains no valid characters")

    # Limit length
    if len(cleaned_name) > 32:
        cleaned_name = cleaned_name[:32]

    return cleaned_name


def validate_pool_size(size: int, min_size: int = 1, max_size: int = 100) -> int:
    """
    Validate thread pool size.

    Args:
        size: Pool size to validate
        min_size: Minimum allowed size
        max_size: Maximum allowed size

    Returns:
        int: Validated pool size

    Raises:
        ValidationError: If size is invalid
    """
    if not isinstance(size, int):
        raise ValidationError("Pool size must be an integer")

    if size < min_size:
        raise ValidationError(f"Pool size must be at least {min_size}")

    if size > max_size:
        raise ValidationError(f"Pool size cannot exceed {max_size}")

    return size
