"""Tests for the service layer.

This test suite verifies that:
1. ServerService correctly manages server CRUD operations with validation
2. AppService validates apps and checks deployment readiness
3. DeploymentService orchestrates multi-step deployments
4. LicenseService enforces license and quota rules
5. ServiceResult provides structured error handling
"""

from unittest.mock import Mock

import pytest

from easyrunner.source.services import (
    AppService,
    DeploymentService,
    LicenseService,
    ServerService,
    ServiceResult,
)
from easyrunner.source.store import EasyRunnerStore, SecretStore
from easyrunner.source.store.data_models.app import App
from easyrunner.source.store.data_models.server import Server


class MockSecretStore(SecretStore):
    """Mock implementation of SecretStore for testing."""

    def __init__(self):
        self.secrets = {}

    def store_secret(self, key: str, value: str) -> bool:
        self.secrets[key] = value
        return True

    def get_secret(self, key: str):
        return self.secrets.get(key)

    def delete_secret(self, key: str) -> bool:
        if key in self.secrets:
            del self.secrets[key]
            return True
        return False


@pytest.fixture
def mock_store():
    """Create a mock EasyRunnerStore."""
    store = Mock(spec=EasyRunnerStore)
    return store


@pytest.fixture
def mock_secret_store():
    """Create a mock SecretStore."""
    return MockSecretStore()


@pytest.fixture
def server_service(mock_store):
    """Create a ServerService with mocked store."""
    return ServerService(store=mock_store)


@pytest.fixture
def app_service(mock_store):
    """Create an AppService with mocked store."""
    return AppService(store=mock_store)


@pytest.fixture
def deployment_service(mock_store, mock_secret_store):
    """Create a DeploymentService with mocked dependencies."""
    return DeploymentService(store=mock_store, secret_store=mock_secret_store)


@pytest.fixture
def license_service(mock_store):
    """Create a LicenseService with mocked store."""
    return LicenseService(store=mock_store)


# ServiceResult Tests

def test_service_result_ok():
    """Test ServiceResult.ok() creates successful result."""
    result = ServiceResult.ok(message="Success", data="test_data")

    assert result.success is True
    assert result.message == "Success"
    assert result.data == "test_data"
    assert result.error_code is None


def test_service_result_error():
    """Test ServiceResult.error() creates error result."""
    result = ServiceResult.error(
        message="Failed",
        error_code="TEST_ERROR",
        details={"key": "value"}
    )

    assert result.success is False
    assert result.message == "Failed"
    assert result.error_code == "TEST_ERROR"
    assert result.details == {"key": "value"}


# ServerService Tests

def test_server_service_add_server_success(server_service, mock_store):
    """Test successfully adding a new server."""
    mock_store.get_server_by_name.return_value = None
    mock_store.get_server_by_hostname_or_ip.return_value = None

    result = server_service.add_server(
        name="test-server",
        hostname_or_ip="192.168.1.1"
    )

    assert result.success is True
    assert "added successfully" in result.message
    assert result.data is not None
    mock_store.add_server.assert_called_once()


def test_server_service_add_server_duplicate_name(server_service, mock_store):
    """Test adding server with duplicate name fails."""
    existing_server = Mock(spec=Server)
    existing_server.name = "test-server"
    mock_store.get_server_by_name.return_value = existing_server

    result = server_service.add_server(
        name="test-server",
        hostname_or_ip="192.168.1.1"
    )

    assert result.success is False
    assert "already exists" in result.message
    assert result.error_code == "DUPLICATE_NAME"
    mock_store.add_server.assert_not_called()


def test_server_service_add_server_duplicate_address(server_service, mock_store):
    """Test adding server with duplicate address fails."""
    mock_store.get_server_by_name.return_value = None
    existing_server = Mock(spec=Server)
    existing_server.name = "other-server"
    existing_server.hostname_or_ip = "192.168.1.1"
    mock_store.get_server_by_hostname_or_ip.return_value = existing_server

    result = server_service.add_server(
        name="test-server",
        hostname_or_ip="192.168.1.1"
    )

    assert result.success is False
    assert "already exists" in result.message
    assert result.error_code == "DUPLICATE_ADDRESS"
    mock_store.add_server.assert_not_called()


def test_server_service_get_server_success(server_service, mock_store):
    """Test successfully retrieving a server."""
    server = Mock(spec=Server)
    server.name = "test-server"
    mock_store.get_server_by_name.return_value = server

    result = server_service.get_server(name="test-server")

    assert result.success is True
    assert result.data == server
    assert "retrieved" in result.message


def test_server_service_get_server_not_found(server_service, mock_store):
    """Test retrieving non-existent server."""
    mock_store.get_server_by_name.return_value = None

    result = server_service.get_server(name="nonexistent")

    assert result.success is False
    assert result.error_code == "NOT_FOUND"
    assert "not found" in result.message


def test_server_service_list_servers(server_service, mock_store):
    """Test listing all servers."""
    servers = [Mock(spec=Server), Mock(spec=Server)]
    mock_store.list_servers.return_value = servers

    result = server_service.list_servers()

    assert result.success is True
    assert result.data == servers
    assert "Retrieved 2 server(s)" in result.message


def test_server_service_delete_server_success(server_service, mock_store):
    """Test successfully deleting a server."""
    server = Mock(spec=Server)
    server.id = "server_id_123"
    server.name = "test-server"
    mock_store.get_server_by_name.return_value = server

    result = server_service.delete_server(name="test-server")

    assert result.success is True
    assert "deleted successfully" in result.message
    mock_store.remove_server.assert_called_once_with(server_id="server_id_123")


def test_server_service_delete_server_not_found(server_service, mock_store):
    """Test deleting non-existent server."""
    mock_store.get_server_by_name.return_value = None

    result = server_service.delete_server(name="nonexistent")

    assert result.success is False
    assert result.error_code == "NOT_FOUND"
    mock_store.remove_server.assert_not_called()


# AppService Tests

def test_app_service_get_app_success(app_service, mock_store):
    """Test successfully retrieving an app."""
    server = Mock(spec=Server)
    server.name = "test-server"
    app = Mock(spec=App)
    app.name = "test-app"
    server.apps = [app]

    mock_store.get_server_by_name.return_value = server

    result = app_service.get_app(server_name="test-server", app_name="test-app")

    assert result.success is True
    assert result.data == app


def test_app_service_get_app_server_not_found(app_service, mock_store):
    """Test getting app when server doesn't exist."""
    mock_store.get_server_by_name.return_value = None

    result = app_service.get_app(server_name="nonexistent", app_name="test-app")

    assert result.success is False
    assert result.error_code == "SERVER_NOT_FOUND"


def test_app_service_get_app_not_found(app_service, mock_store):
    """Test getting app that doesn't exist on server."""
    server = Mock(spec=Server)
    server.name = "test-server"
    server.apps = []

    mock_store.get_server_by_name.return_value = server

    result = app_service.get_app(server_name="test-server", app_name="nonexistent")

    assert result.success is False
    assert result.error_code == "APP_NOT_FOUND"


def test_app_service_list_apps(app_service, mock_store):
    """Test listing all apps on a server."""
    server = Mock(spec=Server)
    server.name = "test-server"
    app1 = Mock(spec=App)
    app2 = Mock(spec=App)
    server.apps = [app1, app2]

    mock_store.get_server_by_name.return_value = server

    result = app_service.list_apps(server_name="test-server")

    assert result.success is True
    assert result.data == [app1, app2]


def test_app_service_validate_app_for_deployment_success(app_service, mock_store):
    """Test successfully validating app for deployment."""
    server = Mock(spec=Server)
    server.name = "test-server"
    app = Mock(spec=App)
    app.name = "test-app"
    app.custom_domain = "example.com"
    app.repo_url = "https://github.com/test/repo"
    server.apps = [app]

    mock_store.get_server_by_name.return_value = server

    result = app_service.validate_app_for_deployment(
        server_name="test-server",
        app_name="test-app"
    )

    assert result.success is True
    assert result.data == app


def test_app_service_validate_app_missing_custom_domain(app_service, mock_store):
    """Test validation fails when custom domain is missing."""
    server = Mock(spec=Server)
    server.name = "test-server"
    app = Mock(spec=App)
    app.name = "test-app"
    app.custom_domain = None
    app.repo_url = "https://github.com/test/repo"
    server.apps = [app]

    mock_store.get_server_by_name.return_value = server

    result = app_service.validate_app_for_deployment(
        server_name="test-server",
        app_name="test-app"
    )

    assert result.success is False
    assert result.error_code == "MISSING_CUSTOM_DOMAIN"
    assert "custom domain" in result.message


def test_app_service_validate_app_missing_repo_url(app_service, mock_store):
    """Test validation fails when repo URL is missing."""
    server = Mock(spec=Server)
    server.name = "test-server"
    app = Mock(spec=App)
    app.name = "test-app"
    app.custom_domain = "example.com"
    app.repo_url = ""
    server.apps = [app]

    mock_store.get_server_by_name.return_value = server

    result = app_service.validate_app_for_deployment(
        server_name="test-server",
        app_name="test-app"
    )

    assert result.success is False
    assert result.error_code == "MISSING_REPO_URL"
    assert "repository URL" in result.message


# DeploymentService Tests

def test_deployment_service_initialization(deployment_service, mock_store, mock_secret_store):
    """Test DeploymentService initializes correctly with dependencies."""
    assert deployment_service.store is mock_store
    assert deployment_service.secret_store is mock_secret_store
    assert deployment_service.app_service is not None
    assert deployment_service.token_manager is not None


# LicenseService Tests


def test_license_service_can_add_server_allows_when_under_quota(
    license_service, mock_store
):
    """Test license service allows adding servers when under quota."""
    # Simulate quota not exceeded
    mock_store.count_servers.return_value = 2
    license_service.MAX_SERVERS = 5

    result = license_service.can_add_server()

    assert result.success is True
    assert "allowed" in result.message.lower()
    assert result.error_code is None


def test_license_service_can_add_server_blocks_when_over_quota(
    license_service, mock_store
):
    """Test license service blocks adding servers when quota exceeded."""
    # Simulate quota exceeded
    mock_store.count_servers.return_value = 5
    license_service.MAX_SERVERS = 5

    result = license_service.can_add_server()

    assert result.success is False
    assert result.error_code == "SERVER_QUOTA_EXCEEDED"
    assert "quota" in result.message.lower()


def test_license_service_can_add_app_allows_when_under_quota(
    license_service, mock_store
):
    """Test license service allows adding apps when under quota."""
    # Simulate quota not exceeded
    mock_store.count_apps_for_server.return_value = 1
    license_service.MAX_APPS_PER_SERVER = 3

    result = license_service.can_add_app(server_name="test-server")

    assert result.success is True
    assert "allowed" in result.message.lower()
    assert result.error_code is None


def test_license_service_can_add_app_blocks_when_over_quota(
    license_service, mock_store
):
    """Test license service blocks adding apps when quota exceeded."""
    # Simulate quota exceeded
    mock_store.count_apps_for_server.return_value = 3
    license_service.MAX_APPS_PER_SERVER = 3

    result = license_service.can_add_app(server_name="test-server")

    assert result.success is False
    assert result.error_code == "APP_QUOTA_EXCEEDED"
    assert "quota" in result.message.lower()


# Integration Tests

def test_server_add_and_list_workflow(server_service, mock_store):
    """Test workflow: add server -> list servers."""
    # Setup: configure mock to allow adding
    mock_store.get_server_by_name.return_value = None
    mock_store.get_server_by_hostname_or_ip.return_value = None
    mock_store.list_servers.return_value = []

    # Step 1: Add server
    add_result = server_service.add_server(
        name="prod-server",
        hostname_or_ip="10.0.0.1"
    )
    assert add_result.success is True

    # Step 2: List servers
    list_result = server_service.list_servers()
    assert list_result.success is True


def test_server_add_and_get_workflow(server_service, mock_store):
    """Test workflow: add server -> get server."""
    # Setup: configure mock
    server_mock = Mock(spec=Server)
    server_mock.name = "test-server"
    
    mock_store.get_server_by_name.side_effect = [
        None,  # First call in add_server (check for existing)
        server_mock  # Second call in get_server
    ]
    mock_store.get_server_by_hostname_or_ip.return_value = None

    # Step 1: Add server
    add_result = server_service.add_server(
        name="test-server",
        hostname_or_ip="192.168.1.1"
    )
    assert add_result.success is True

    # Step 2: Get server
    get_result = server_service.get_server(name="test-server")
    assert get_result.success is True
    assert get_result.data.name == "test-server"


def test_service_error_handling_consistency():
    """Test that all services handle errors consistently."""
    # Create a mock store that raises an exception
    mock_store = Mock(spec=EasyRunnerStore)
    mock_store.get_server_by_name.side_effect = RuntimeError("Database error")

    server_service = ServerService(store=mock_store)

    result = server_service.get_server(name="test")

    # Should handle exception gracefully
    assert result.success is False
    assert result.error_code == "INTERNAL_ERROR"
    assert "Failed to get server" in result.message


def test_service_result_type_safety():
    """Test ServiceResult maintains type information."""
    # Test with string data
    result_str = ServiceResult.ok(data="test_string")
    assert result_str.data == "test_string"

    # Test with dict data
    result_dict = ServiceResult.ok(data={"key": "value"})
    assert result_dict.data == {"key": "value"}

    # Test with None data
    result_none = ServiceResult.ok(data=None)
    assert result_none.data is None
