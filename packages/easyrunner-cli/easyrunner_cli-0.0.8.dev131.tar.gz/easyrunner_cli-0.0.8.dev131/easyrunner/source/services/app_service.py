"""AppService: Business logic for application management operations.

Handles:
- App validation and persistence
- App deployment orchestration
- App status checks
"""

import logging
from typing import List

from ..store import EasyRunnerStore
from ..store.data_models.app import App
from .service_result import ServiceResult

logger = logging.getLogger(__name__)


class AppService:
    """Service for app management business logic."""

    def __init__(self, store: EasyRunnerStore):
        """Initialize service with store dependency.

        Args:
            store: EasyRunnerStore instance for persistence
        """
        self.store = store

    def get_app(self, server_name: str, app_name: str) -> ServiceResult[App]:
        """Get an app from a server.

        Args:
            server_name: Name of the server
            app_name: Name of the app

        Returns:
            ServiceResult with App on success, or error if not found
        """
        try:
            # Get server
            server = self.store.get_server_by_name(name=server_name)
            if not server:
                logger.debug(f"Server not found: {server_name}")
                return ServiceResult.error(
                    message=f"Server '{server_name}' not found",
                    error_code="SERVER_NOT_FOUND",
                )

            # Get app from server
            app = next((a for a in server.apps if a.name == app_name), None)
            if not app:
                logger.debug(f"App not found: {app_name} on {server_name}")
                return ServiceResult.error(
                    message=f"App '{app_name}' not found on server '{server_name}'",
                    error_code="APP_NOT_FOUND",
                )

            return ServiceResult.ok(
                message=f"App '{app_name}' retrieved",
                data=app,
            )

        except Exception as e:
            logger.error(f"Error getting app: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to get app: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    def list_apps(self, server_name: str) -> ServiceResult[List[App]]:
        """List all apps on a server.

        Args:
            server_name: Name of the server

        Returns:
            ServiceResult with list of apps
        """
        try:
            # Get server
            server = self.store.get_server_by_name(name=server_name)
            if not server:
                logger.debug(f"Server not found: {server_name}")
                return ServiceResult.error(
                    message=f"Server '{server_name}' not found",
                    error_code="SERVER_NOT_FOUND",
                )

            apps = server.apps if server.apps else []
            return ServiceResult.ok(
                message=f"Retrieved {len(apps)} app(s)",
                data=apps,
            )

        except Exception as e:
            logger.error(f"Error listing apps: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to list apps: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    def validate_app_for_deployment(
        self, server_name: str, app_name: str
    ) -> ServiceResult[App]:
        """Validate that an app is ready for deployment.

        Business validation:
        - App exists
        - Server exists
        - App has custom domain set (required for deployment)
        - App has repo URL set

        Args:
            server_name: Name of the server
            app_name: Name of the app

        Returns:
            ServiceResult with App if valid, error otherwise
        """
        try:
            # Get the app (also validates server exists)
            app_result = self.get_app(server_name=server_name, app_name=app_name)
            if not app_result.success:
                return app_result

            app = app_result.data
            if not app:
                # Should not happen if app_result.success is True, but guard anyway
                return ServiceResult.error(
                    message=f"App '{app_name}' data is missing",
                    error_code="APP_DATA_MISSING",
                )

            # Business rule: custom domain required
            if not app.custom_domain:
                logger.warning(
                    f"App validation failed - no custom domain: {app_name} on {server_name}"
                )
                return ServiceResult.error(
                    message=f"App '{app_name}' must have a custom domain set before deployment",
                    error_code="MISSING_CUSTOM_DOMAIN",
                    details={"app_name": app_name, "server_name": server_name},
                )

            # Business rule: repo URL required
            if not app.repo_url or str(app.repo_url).strip() == "":
                logger.warning(
                    f"App validation failed - no repo URL: {app_name} on {server_name}"
                )
                return ServiceResult.error(
                    message=f"App '{app_name}' must have a repository URL set before deployment",
                    error_code="MISSING_REPO_URL",
                    details={"app_name": app_name, "server_name": server_name},
                )

            logger.info(f"App validation passed: {app_name} on {server_name}")
            return ServiceResult.ok(
                message=f"App '{app_name}' is ready for deployment",
                data=app,
            )

        except Exception as e:
            logger.error(f"Error validating app: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to validate app: {str(e)}",
                error_code="INTERNAL_ERROR",
            )
