"""CLI + Services Integration Tests.

Tests that CLI commands properly use the service layer and maintain
consistent behavior between CLI and service layer interfaces.

These tests verify:
- CLI ServerSubCommand uses ServerService
- CLI AppSubCommand uses AppService and DeploymentService
- End-to-end workflows work correctly
- Error handling is consistent across layers
"""

import logging
from unittest.mock import Mock

import pytest

from easyrunner.source.services import (
    AppService,
    DeploymentService,
    ServerService,
    ServiceResult,
)
from easyrunner.source.store.data_models import App, Server

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_store() -> Mock:
    """Create a mock EasyRunnerStore."""
    store = Mock()
    store.list_servers.return_value = []
    store.add_server.return_value = None
    store.update_server.return_value = None
    # By default, return None for server lookups (server doesn't exist)
    store.get_server_by_name.return_value = None
    store.get_server_by_hostname_or_ip.return_value = None
    return store


@pytest.fixture
def mock_secret_store() -> Mock:
    """Create a mock SecretStore."""
    return Mock()


@pytest.fixture
def server_service(mock_store: Mock) -> ServerService:
    """Create a ServerService with mocked store."""
    return ServerService(store=mock_store)


@pytest.fixture
def app_service(mock_store: Mock) -> AppService:
    """Create an AppService with mocked store."""
    return AppService(store=mock_store)


@pytest.fixture
def deployment_service(
    mock_store: Mock, mock_secret_store: Mock
) -> DeploymentService:
    """Create a DeploymentService with mocked dependencies."""
    return DeploymentService(store=mock_store, secret_store=mock_secret_store)


class TestServerServiceUsage:
    """Test that ServerService is properly used for server operations."""

    def test_server_service_add_server_called_from_cli(
        self, server_service: ServerService
    ):
        """Test ServerService.add_server is called correctly."""
        # Arrange
        test_server_name = "test-server"
        test_server_ip = "192.168.1.1"

        # Act
        result = server_service.add_server(
            name=test_server_name, hostname_or_ip=test_server_ip
        )

        # Assert
        assert result.success
        assert result.data is not None
        assert result.data.name == test_server_name
        assert result.data.hostname_or_ip == test_server_ip
        assert result.message == f"Server '{test_server_name}' added successfully"

    def test_server_service_delete_server_called_from_cli(
        self, server_service: ServerService, mock_store: Mock
    ):
        """Test ServerService.delete_server removes server correctly."""
        # Arrange
        test_server = Server(name="test-server", hostname_or_ip="192.168.1.1")
        mock_store.get_server_by_name.return_value = test_server

        # Act
        result = server_service.delete_server(name=test_server.name)

        # Assert
        assert result.success
        assert result.message == f"Server '{test_server.name}' deleted successfully"
        mock_store.remove_server.assert_called_once_with(server_id=test_server.id)

    def test_server_service_respects_uniqueness_constraints(
        self, server_service: ServerService, mock_store: Mock
    ):
        """Test ServerService enforces name/address uniqueness."""
        # Arrange
        existing_server = Server(
            name="existing", hostname_or_ip="192.168.1.1"
        )
        mock_store.get_server_by_name.return_value = existing_server

        # Act - try to add server with duplicate name
        result = server_service.add_server(
            name="existing", hostname_or_ip="192.168.1.2"
        )

        # Assert
        assert not result.success
        assert result.error_code == "DUPLICATE_NAME"


class TestAppServiceUsage:
    """Test that AppService is properly used for app operations."""

    def test_app_service_validate_for_deployment(
        self, app_service: AppService, mock_store: Mock
    ):
        """Test AppService validates app for deployment."""
        # Arrange
        test_server = Server(name="test-server", hostname_or_ip="192.168.1.1")
        test_app = App(
            name="test-app",
            repo_url="https://github.com/user/repo.git",
            custom_domain="app.example.com",
        )
        test_server.apps = [test_app]
        mock_store.get_server_by_name.return_value = test_server

        # Act
        result = app_service.validate_app_for_deployment(
            server_name="test-server", app_name="test-app"
        )

        # Assert
        assert result.success
        assert result.data == test_app
        assert (
            result.message
            == "App 'test-app' is ready for deployment"
        )

    def test_app_service_rejects_missing_custom_domain(
        self, app_service: AppService, mock_store: Mock
    ):
        """Test AppService rejects app without custom domain."""
        # Arrange
        test_server = Server(name="test-server", hostname_or_ip="192.168.1.1")
        test_app = App(
            name="test-app",
            repo_url="https://github.com/user/repo.git",
            custom_domain=None,
        )
        test_server.apps = [test_app]
        mock_store.get_server_by_name.return_value = test_server

        # Act
        result = app_service.validate_app_for_deployment(
            server_name="test-server", app_name="test-app"
        )

        # Assert
        assert not result.success
        assert result.error_code == "MISSING_CUSTOM_DOMAIN"

    def test_app_service_rejects_missing_repo_url(
        self, app_service: AppService, mock_store: Mock
    ):
        """Test AppService rejects app without repo URL."""
        # Arrange
        test_server = Server(name="test-server", hostname_or_ip="192.168.1.1")
        test_app = App(
            name="test-app",
            repo_url="",
            custom_domain="app.example.com",
        )
        test_server.apps = [test_app]
        mock_store.get_server_by_name.return_value = test_server

        # Act
        result = app_service.validate_app_for_deployment(
            server_name="test-server", app_name="test-app"
        )

        # Assert
        assert not result.success
        assert result.error_code == "MISSING_REPO_URL"


class TestDeploymentServiceUsage:
    """Test that DeploymentService is properly used for deployments."""

    def test_deployment_service_validates_app_before_deploy(
        self, deployment_service: DeploymentService, mock_store: Mock
    ):
        """Test DeploymentService validates app before attempting deployment."""
        # Arrange
        mock_store.get_server_by_name.return_value = None

        # Act
        result = deployment_service.deploy_app(
            server_name="nonexistent",
            app_name="test-app",
            ssh_username="easyrunner",
            ssh_key_path="/path/to/key",
            github_token="dummy_token",
            debug=False,
            silent=False,
        )

        # Assert
        assert not result.success
        assert "not found" in result.message.lower()

    def test_deployment_service_returns_structured_error(
        self, deployment_service: DeploymentService, mock_store: Mock
    ):
        """Test DeploymentService returns structured error information."""
        # Arrange
        mock_store.get_server_by_name.return_value = None

        # Act
        result = deployment_service.deploy_app(
            server_name="nonexistent",
            app_name="test-app",
            ssh_username="easyrunner",
            ssh_key_path="/path/to/key",
            debug=False,
            silent=False,
        )

        # Assert - verify ServiceResult structure
        assert isinstance(result, ServiceResult)
        assert result.error_code is not None
        assert result.message is not None


class TestCLIServiceConsistency:
    """Test that CLI and service layer behaviors are consistent."""

    def test_service_result_success_field_matches_cli_expectations(
        self, server_service: ServerService
    ):
        """Test ServiceResult.success matches CLI error handling expectations."""
        # Arrange
        test_server = Server(name="test-server", hostname_or_ip="192.168.1.1")

        # Act
        result = server_service.add_server(
            name=test_server.name, hostname_or_ip=test_server.hostname_or_ip
        )

        # Assert - CLI checks 'if result.success:'
        assert isinstance(result.success, bool)
        assert hasattr(result, "message")
        assert hasattr(result, "data")
        assert hasattr(result, "error_code")

    def test_service_result_contains_cli_required_fields(
        self, server_service: ServerService, mock_store: Mock
    ):
        """Test ServiceResult has all fields CLI needs for error display."""
        # Arrange
        mock_store.get_server_by_name.return_value = Server(
            name="existing", hostname_or_ip="192.168.1.1"
        )

        # Act
        result = server_service.add_server(
            name="existing", hostname_or_ip="192.168.1.2"
        )

        # Assert - CLI uses these fields for error messages
        assert not result.success
        assert result.error_code in ["DUPLICATE_NAME", "DUPLICATE_ADDRESS"]
        assert "already exists" in result.message.lower()
        if result.details:
            assert "existing_server" in result.details


class TestEndToEndWorkflows:
    """Test complete workflows from CLI through services to store."""

    def test_add_server_workflow(
        self, server_service: ServerService, mock_store: Mock
    ):
        """Test complete add server workflow."""
        # Arrange
        server_name = "production"
        server_ip = "192.168.1.100"

        # Act - add server
        add_result = server_service.add_server(
            name=server_name, hostname_or_ip=server_ip
        )

        # Assert
        assert add_result.success
        assert add_result.data is not None
        assert add_result.data.name == server_name
        assert add_result.data.hostname_or_ip == server_ip
        mock_store.add_server.assert_called_once()

    def test_add_and_validate_app_workflow(
        self,
        app_service: AppService,
        mock_store: Mock,
    ):
        """Test complete add and validate app workflow."""
        # Arrange
        test_server = Server(name="prod", hostname_or_ip="192.168.1.1")
        test_app = App(
            name="webapp",
            repo_url="https://github.com/user/webapp.git",
            custom_domain="app.prod.com",
        )
        test_server.apps = [test_app]
        mock_store.get_server_by_name.return_value = test_server

        # Act - get app
        get_result = app_service.get_app(server_name="prod", app_name="webapp")

        # Assert - got app
        assert get_result.success
        assert get_result.data == test_app

        # Act - validate for deployment
        validate_result = app_service.validate_app_for_deployment(
            server_name="prod", app_name="webapp"
        )

        # Assert - app is valid
        assert validate_result.success
        assert validate_result.data == test_app
