"""LicenseService: Business logic for license checks and quota enforcement.

Handles:
- Server limit enforcement
- App limit enforcement
- License expiration checks
"""

import logging

from ..store import EasyRunnerStore
from .service_result import ServiceResult

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for license-related business logic."""

    def __init__(self, store: EasyRunnerStore):
        """Initialize service with store dependency.

        Args:
            store: EasyRunnerStore instance for persistence
        """
        self.store = store

    def can_add_server(self) -> ServiceResult[None]:
        """Check if a new server can be added based on license limits.

        Returns:
            ServiceResult indicating if server can be added
        """
        try:
            # TODO: Integrate with actual LicenseManager when it's refactored to core
            # For now, just return True (no license checks)
            logger.debug("License check: can_add_server - not yet integrated")
            return ServiceResult.ok(
                message="Server can be added (TODO: integrate with LicenseManager)",
            )

        except Exception as e:
            logger.error(f"Error checking server quota: {str(e)}", exc_info=True)
            # Be permissive on errors (don't block operations)
            return ServiceResult.ok(
                message="Server can be added (error in license check, permissive mode)",
            )

    def can_add_app(self, server_name: str) -> ServiceResult[None]:
        """Check if a new app can be added to a server based on license limits.

        Args:
            server_name: Name of the server

        Returns:
            ServiceResult indicating if app can be added
        """
        try:
            server = self.store.get_server_by_name(name=server_name)
            if not server:
                return ServiceResult.error(
                    message=f"Server '{server_name}' not found",
                    error_code="SERVER_NOT_FOUND",
                )

            # TODO: Check license limits for apps per server
            logger.debug(f"License check: can_add_app on {server_name}")
            return ServiceResult.ok(
                message="App can be added (TODO: check license limits)",
            )

        except Exception as e:
            logger.error(f"Error checking app quota: {str(e)}", exc_info=True)
            return ServiceResult.ok(
                message="App can be added (error in license check, permissive mode)",
            )
