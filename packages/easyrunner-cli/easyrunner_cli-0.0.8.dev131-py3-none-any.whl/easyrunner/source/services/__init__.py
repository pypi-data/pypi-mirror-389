"""Service layer for business logic orchestration.

Services are the bridge between interfaces (CLI, Web API, Web UI) and core logic.
They encapsulate business rules, validation, and orchestration without being
tied to any specific interface.

Key principles:
- Pure business logic (testable without I/O)
- Return structured results (not UI formatting)
- Can be consumed by CLI, Web API, and Web UI equally
- No presentation logic (no Rich tables, JSON formatting, etc.)
"""

from .app_service import AppService
from .deployment_service import DeploymentService
from .license_service import LicenseService
from .server_service import ServerService
from .service_result import (
    ServiceResult,
)

__all__ = [
    "ServerService",
    "AppService",
    "DeploymentService",
    "LicenseService",
    "ServiceResult",
]
