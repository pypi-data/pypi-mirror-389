"""DeploymentService: Orchestrates multi-step app deployment flows.

Handles:
- Deployment validation and prerequisites
- SSH connection setup
- Coordinating resource operations
- Error handling and rollback
"""

import logging
from typing import Optional

from ..command_executor import CommandExecutor
from ..integrations.github import GitHubTokenManager
from ..resources.os_resources import HostServerUbuntu
from ..ssh import Ssh
from ..store import EasyRunnerStore, SecretStore
from .app_service import AppService
from .service_result import ServiceResult

logger = logging.getLogger(__name__)


class DeploymentService:
    """Service for orchestrating app deployments."""

    def __init__(self, store: EasyRunnerStore, secret_store: SecretStore):
        """Initialize service with store and secret store dependencies.

        Args:
            store: EasyRunnerStore instance for persistence
            secret_store: SecretStore instance for secure token storage
        """
        self.store = store
        self.secret_store = secret_store
        self.app_service = AppService(store=store)
        self.token_manager = GitHubTokenManager(secret_store=secret_store)

    def deploy_app(
        self,
        server_name: str,
        app_name: str,
        ssh_username: str,
        ssh_key_path: str,
        github_token: Optional[str] = None,
        debug: bool = False,
        silent: bool = False,
    ) -> ServiceResult[dict]:
        """Deploy an app to a server.

        This is the main orchestration method. It:
        1. Validates the app is ready for deployment
        2. Retrieves GitHub token if needed
        3. Establishes SSH connection
        4. Delegates to HostServerUbuntu resource for actual deployment
        5. Handles errors and provides feedback

        Args:
            server_name: Name of the server to deploy to
            app_name: Name of the app to deploy
            ssh_username: SSH username for connection
            ssh_key_path: Path to SSH private key
            github_token: Optional GitHub token (retrieved from store if not provided)
            debug: Enable debug logging
            silent: Suppress non-error output

        Returns:
            ServiceResult with deployment details on success, or error information
        """
        try:
            # Step 1: Validate app is ready for deployment
            validation_result = self.app_service.validate_app_for_deployment(
                server_name=server_name, app_name=app_name
            )
            if not validation_result.success:
                logger.warning(f"App validation failed: {validation_result.message}")
                return ServiceResult.error(
                    message=validation_result.message,
                    error_code=validation_result.error_code,
                )

            app = validation_result.data
            if not app:
                # Should not happen if validation_result.success is True, but guard anyway
                return ServiceResult.error(
                    message=f"App '{app_name}' data is missing",
                    error_code="APP_DATA_MISSING",
                )

            # Step 2: Get GitHub token if not provided
            if github_token is None:
                try:
                    github_token = self.token_manager.get_token()
                except Exception as e:
                    logger.error(f"Failed to retrieve GitHub token: {str(e)}")
                    return ServiceResult.error(
                        message="GitHub token not found. Authenticate with GitHub first using 'er link github'.",
                        error_code="GITHUB_TOKEN_NOT_FOUND",
                    )

            if not github_token:
                logger.error("No GitHub token available")
                return ServiceResult.error(
                    message="No GitHub token configured. Please authenticate with GitHub.",
                    error_code="GITHUB_TOKEN_NOT_CONFIGURED",
                )

            # Step 3: Get server info to get hostname/IP
            server_result = self.app_service.get_app(
                server_name=server_name, app_name=app_name
            )
            if not server_result.success:
                logger.error(f"Server not found: {server_name}")
                return ServiceResult.error(
                    message=f"Server '{server_name}' not found",
                    error_code="SERVER_NOT_FOUND",
                )

            server = self.store.get_server_by_name(name=server_name)
            if not server:
                logger.error(f"Server '{server_name}' is missing.")
                return ServiceResult.error(
                    message=f"Server '{server_name}' is missing.",
                    error_code="SERVER_NOT_FOUND",
                )

            # Step 4: Establish SSH connection and deploy
            logger.info(
                f"Starting deployment: {app_name} to {server_name} via SSH as {ssh_username}"
            )

            with Ssh(
                hostname_or_ipv4=server.hostname_or_ip,
                username=ssh_username,
                key_filename=ssh_key_path,
            ) as ssh_client:
                executor = CommandExecutor(ssh_client=ssh_client)
                host_server = HostServerUbuntu(
                    easyrunner_username=ssh_username,
                    executor=executor,
                    debug=debug,
                    silent=silent,
                )

                # Delegate to resource for actual deployment
                logger.info(f"Executing deployment flow for {app_name}")
                host_server.deploy_app_flow_a(
                    repo_url=app.repo_url,  # type: ignore
                    custom_app_domain_name=app.custom_domain,  # type: ignore
                    github_access_token=github_token,
                )

            logger.info(f"Deployment completed: {app_name} on {server_name}")
            return ServiceResult.ok(
                message=f"App '{app_name}' deployed successfully to '{server_name}'",
                data={
                    "app_name": app_name,
                    "server_name": server_name,
                    "custom_domain": app.custom_domain,
                },
            )

        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ServiceResult.error(
                message=error_msg,
                error_code="DEPLOYMENT_FAILED",
                details={"exception_type": type(e).__name__},
            )
