"""ServerService: Business logic for server management operations.

Handles:
- Server addition with validation (uniqueness, etc.)
- Server retrieval and listing
- Server deletion
- Server setup verification
"""

import logging
from typing import List

from ..store import EasyRunnerStore
from ..store.data_models.server import Server
from .service_result import ServiceResult

logger = logging.getLogger(__name__)


class ServerService:
    """Service for server management business logic."""

    def __init__(self, store: EasyRunnerStore):
        """Initialize service with store dependency.

        Args:
            store: EasyRunnerStore instance for persistence
        """
        self.store = store

    def add_server(
        self, name: str, hostname_or_ip: str
    ) -> ServiceResult[Server]:
        """Add a server to the store with validation.

        Business validation:
        - Server name must be unique
        - Hostname/IP must be unique

        Args:
            name: Friendly name for the server
            hostname_or_ip: Hostname or IP address

        Returns:
            ServiceResult with created Server on success, or error message on failure
        """
        try:
            # Validation: check name uniqueness
            existing_by_name = self.store.get_server_by_name(name=name)
            if existing_by_name:
                logger.warning(f"Attempt to add server with duplicate name: {name}")
                return ServiceResult.error(
                    message=f"Server with name '{name}' already exists",
                    error_code="DUPLICATE_NAME",
                    details={"existing_server": existing_by_name.name},
                )

            # Validation: check hostname/IP uniqueness
            existing_by_addr = self.store.get_server_by_hostname_or_ip(
                hostname_or_ip=hostname_or_ip
            )
            if existing_by_addr:
                logger.warning(
                    f"Attempt to add server with duplicate address: {hostname_or_ip}"
                )
                return ServiceResult.error(
                    message=f"Server with address '{hostname_or_ip}' already exists",
                    error_code="DUPLICATE_ADDRESS",
                    details={"existing_server": existing_by_addr.name},
                )

            # Create and persist server
            server = Server(name=name, hostname_or_ip=hostname_or_ip)
            self.store.add_server(server=server)

            logger.info(f"Server added: {name} ({hostname_or_ip})")
            return ServiceResult.ok(
                message=f"Server '{name}' added successfully",
                data=server,
            )

        except Exception as e:
            logger.error(f"Error adding server: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to add server: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    def get_server(self, name: str) -> ServiceResult[Server]:
        """Get a server by name.

        Args:
            name: Server name

        Returns:
            ServiceResult with Server on success, or error if not found
        """
        try:
            server = self.store.get_server_by_name(name=name)
            if not server:
                logger.debug(f"Server not found: {name}")
                return ServiceResult.error(
                    message=f"Server '{name}' not found",
                    error_code="NOT_FOUND",
                )

            return ServiceResult.ok(
                message=f"Server '{name}' retrieved",
                data=server,
            )

        except Exception as e:
            logger.error(f"Error getting server: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to get server: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    def list_servers(self) -> ServiceResult[List[Server]]:
        """List all servers.

        Returns:
            ServiceResult with list of servers
        """
        try:
            servers = self.store.list_servers()
            return ServiceResult.ok(
                message=f"Retrieved {len(servers)} server(s)",
                data=servers,
            )

        except Exception as e:
            logger.error(f"Error listing servers: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to list servers: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

    def delete_server(self, name: str) -> ServiceResult[None]:
        """Delete a server by name.

        Args:
            name: Server name

        Returns:
            ServiceResult indicating success or failure
        """
        try:
            # Get the server first to validate it exists
            server_result = self.get_server(name)
            if not server_result.success:
                return ServiceResult.error(
                    message=server_result.message,
                    error_code=server_result.error_code,
                )

            # Delete from store using server id
            server = server_result.data
            if server:
                self.store.remove_server(server_id=server.id)

            logger.info(f"Server deleted: {name}")
            return ServiceResult.ok(
                message=f"Server '{name}' deleted successfully",
            )

        except Exception as e:
            logger.error(f"Error deleting server: {str(e)}", exc_info=True)
            return ServiceResult.error(
                message=f"Failed to delete server: {str(e)}",
                error_code="INTERNAL_ERROR",
            )
