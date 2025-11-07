"""Service result types for structured error/success handling.

Services return result objects instead of raising exceptions or returning raw values.
This enables callers (CLI, Web API, etc.) to handle success and failure uniformly.
"""

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """Base result type for all service operations."""

    success: bool
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None
    details: Optional[dict[str, Any]] = None

    @classmethod
    def ok(cls, message: str = "Operation successful", data: Optional[T] = None, details: Optional[dict] = None) -> "ServiceResult[T]":
        """Create a successful result."""
        return cls(
            success=True,
            message=message,
            data=data,
            details=details,
        )

    @classmethod
    def error(cls, message: str, error_code: Optional[str] = None, details: Optional[dict] = None) -> "ServiceResult[T]":
        """Create an error result."""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            details=details,
        )


# Use ServiceResult[T] directly for server add, app deploy, and license check operations.
# Example:
# result: ServiceResult[Server]
# result: ServiceResult[AppDeployment]
# result: ServiceResult[LicenseInfo]
