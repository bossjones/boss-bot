"""Comprehensive tests for LangGraph SDK client functionality with proper mocking.

This module tests the LangGraphAssistantClient with comprehensive mocking of the
LangGraph SDK to avoid external dependencies while ensuring all functionality works correctly.
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from langgraph_sdk.schema import Assistant as SDKAssistant, GraphSchema
from pydantic import AnyHttpUrl, SecretStr, ValidationError

from boss_bot.ai.assistants.client import (
    AssistantSyncResult,
    LangGraphAssistantClient,
    LangGraphClientConfig,
    create_assistant_client,
    export_assistants_to_directory,
    sync_assistants_from_directory,
)
from boss_bot.ai.assistants.models import (
    AIConfiguration,
    AssistantConfig,
    AssistantMetadata,
    create_default_assistant_config,
)
from boss_bot.core.env import BossSettings


# Module-level fixtures shared across all test classes
@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=BossSettings)
    settings.langgraph_deployment_url = "https://api.langraph.com"
    settings.langgraph_api_key = SecretStr("test-api-key")
    settings.langchain_tracing_v2 = False
    return settings


@pytest.fixture
def mock_client_config():
    """Create mock client configuration."""
    return LangGraphClientConfig(
        deployment_url=AnyHttpUrl("https://api.langraph.com"),
        api_key=SecretStr("test-api-key"),
        timeout_seconds=30,
        max_retries=3,
        enable_tracing=False,
    )


@pytest.fixture
def mock_sdk_client():
    """Create mock LangGraph SDK client."""
    client = AsyncMock()
    client.assistants = AsyncMock()
    client.assistants.search = AsyncMock()
    client.assistants.create = AsyncMock()
    client.assistants.get = AsyncMock()
    client.assistants.update = AsyncMock()
    client.assistants.delete = AsyncMock()
    client.assistants.get_schemas = AsyncMock()
    return client


@pytest.fixture
def assistant_client(mock_client_config, mock_settings):
    """Create assistant client for testing."""
    return LangGraphAssistantClient(config=mock_client_config, settings=mock_settings)


@pytest.fixture
def mock_sdk_assistant():
    """Create mock SDK assistant."""
    assistant = Mock(spec=SDKAssistant)
    assistant.assistant_id = "test-assistant-123"
    assistant.name = "Test Assistant"
    assistant.graph_id = "download_workflow"
    assistant.created_at = datetime.utcnow()
    assistant.updated_at = datetime.utcnow()
    assistant.metadata = {
        "description": "Test assistant",
        "tags": ["test"],
        "enabled": True,
        "version": "1.0.0"
    }
    assistant.config = {
        "enable_ai_strategy_selection": True,
        "ai_model": "gpt-4",
        "ai_temperature": 0.3,
        "max_retries": 3,
        "timeout_seconds": 300,
        "download_quality": "good",
    }
    return assistant


class TestLangGraphClientConfig:
    """Test LangGraphClientConfig model."""

    def test_default_config(self):
        """Test default client configuration values."""
        config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com")
        )

        assert str(config.deployment_url) == "https://api.langraph.com/"
        assert config.api_key is None
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.enable_tracing is False

    def test_config_with_all_fields(self):
        """Test configuration with all fields set."""
        config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://custom.langraph.com"),
            api_key=SecretStr("secret-key"),
            timeout_seconds=60,
            max_retries=5,
            enable_tracing=True,
        )

        assert str(config.deployment_url) == "https://custom.langraph.com/"
        assert config.api_key.get_secret_value() == "secret-key"
        assert config.timeout_seconds == 60
        assert config.max_retries == 5
        assert config.enable_tracing is True

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeouts
        LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            timeout_seconds=1
        )
        LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            timeout_seconds=300
        )

        # Invalid timeouts
        with pytest.raises(ValidationError):
            LangGraphClientConfig(
                deployment_url=AnyHttpUrl("https://api.langraph.com"),
                timeout_seconds=0
            )

        with pytest.raises(ValidationError):
            LangGraphClientConfig(
                deployment_url=AnyHttpUrl("https://api.langraph.com"),
                timeout_seconds=301
            )

    def test_max_retries_validation(self):
        """Test max retries validation."""
        # Valid retries
        LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            max_retries=0
        )
        LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            max_retries=10
        )

        # Invalid retries
        with pytest.raises(ValidationError):
            LangGraphClientConfig(
                deployment_url=AnyHttpUrl("https://api.langraph.com"),
                max_retries=-1
            )

        with pytest.raises(ValidationError):
            LangGraphClientConfig(
                deployment_url=AnyHttpUrl("https://api.langraph.com"),
                max_retries=11
            )


class TestAssistantSyncResult:
    """Test AssistantSyncResult model."""

    def test_default_sync_result(self):
        """Test default sync result values."""
        result = AssistantSyncResult()

        assert result.created == 0
        assert result.updated == 0
        assert result.deleted == 0
        assert result.errors == []
        assert isinstance(result.synchronized_at, datetime)

    def test_sync_result_properties(self):
        """Test sync result computed properties."""
        result = AssistantSyncResult(
            created=5,
            updated=3,
            deleted=2,
            errors=[]
        )

        assert result.total_changes == 10
        assert result.success is True

        result_with_errors = AssistantSyncResult(
            created=1,
            updated=0,
            deleted=0,
            errors=["Error 1", "Error 2"]
        )

        assert result_with_errors.total_changes == 1
        assert result_with_errors.success is False


class TestLangGraphAssistantClient:
    """Test LangGraphAssistantClient functionality."""

    def test_client_initialization_with_config(self, mock_client_config, mock_settings):
        """Test client initialization with provided config."""
        client = LangGraphAssistantClient(config=mock_client_config, settings=mock_settings)

        assert client.config == mock_client_config
        assert client.settings == mock_settings
        assert client.client is None

    def test_client_initialization_default_config(self, mock_settings):
        """Test client initialization with default config."""
        client = LangGraphAssistantClient(settings=mock_settings)

        assert client.config is not None
        assert str(client.config.deployment_url) == "https://api.langraph.com/"
        assert client.config.api_key.get_secret_value() == "test-api-key"

    def test_create_default_config_with_fallbacks(self):
        """Test default config creation with various fallback scenarios."""
        # Test with minimal settings
        minimal_settings = Mock(spec=BossSettings)
        client = LangGraphAssistantClient(settings=minimal_settings)

        # Should fallback to localhost
        assert str(client.config.deployment_url) == "http://localhost:8000/"

    def test_create_default_config_with_langchain_fallback(self):
        """Test default config creation with LangChain fallback."""
        settings = Mock(spec=BossSettings)
        settings.langchain_endpoint = "https://langchain.api.com"
        settings.langchain_api_key = SecretStr("langchain-key")

        client = LangGraphAssistantClient(settings=settings)

        assert str(client.config.deployment_url) == "https://langchain.api.com/"
        assert client.config.api_key.get_secret_value() == "langchain-key"

    @pytest.mark.asyncio
    async def test_connect_success(self, assistant_client, mock_sdk_client):
        """Test successful connection."""
        with patch('boss_bot.ai.assistants.client.get_client', return_value=mock_sdk_client):
            await assistant_client.connect()

            assert assistant_client.client == mock_sdk_client
            # Health check should have been called
            mock_sdk_client.assistants.search.assert_called_once_with(limit=1)

    @pytest.mark.asyncio
    async def test_connect_failure(self, assistant_client):
        """Test connection failure."""
        with patch('boss_bot.ai.assistants.client.get_client', side_effect=Exception("Connection failed")):
            with pytest.raises(ConnectionError, match="LangGraph Cloud connection failed"):
                await assistant_client.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, assistant_client, mock_sdk_client):
        """Test disconnection."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.close = AsyncMock()

        await assistant_client.disconnect()

        assert assistant_client.client is None
        mock_sdk_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_close_method(self, assistant_client, mock_sdk_client):
        """Test disconnection when client has no close method."""
        assistant_client.client = mock_sdk_client
        # Don't add close method to mock

        await assistant_client.disconnect()

        assert assistant_client.client is None

    @pytest.mark.asyncio
    async def test_health_check_success(self, assistant_client, mock_sdk_client):
        """Test successful health check."""
        assistant_client.client = mock_sdk_client

        result = await assistant_client.health_check()

        assert result is True
        mock_sdk_client.assistants.search.assert_called_once_with(limit=1)

    @pytest.mark.asyncio
    async def test_health_check_failure(self, assistant_client, mock_sdk_client):
        """Test failed health check."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.search.side_effect = Exception("Health check failed")

        result = await assistant_client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, assistant_client):
        """Test health check when not connected."""
        with pytest.raises(ConnectionError, match="Not connected to LangGraph Cloud"):
            await assistant_client.health_check()

    @pytest.mark.asyncio
    async def test_health_check_cached(self, assistant_client, mock_sdk_client):
        """Test health check caching."""
        assistant_client.client = mock_sdk_client
        assistant_client._last_health_check = datetime.utcnow()

        # Should return True without calling SDK (cached)
        result = await assistant_client.health_check()

        assert result is True
        mock_sdk_client.assistants.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_force(self, assistant_client, mock_sdk_client):
        """Test forced health check."""
        assistant_client.client = mock_sdk_client
        assistant_client._last_health_check = datetime.utcnow()

        # Force should bypass cache
        result = await assistant_client.health_check(force=True)

        assert result is True
        mock_sdk_client.assistants.search.assert_called_once_with(limit=1)

    @pytest.mark.asyncio
    async def test_create_assistant(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test creating an assistant."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.create.return_value = mock_sdk_assistant

        config = create_default_assistant_config(
            name="Test Assistant",
            description="Test description"
        )

        result = await assistant_client.create_assistant(config)

        assert result == mock_sdk_assistant

        # Verify create was called with correct data
        call_args = mock_sdk_client.assistants.create.call_args
        assert call_args[1]["graph_id"] == config.graph_id
        assert call_args[1]["name"] == config.name
        assert "config" in call_args[1]
        assert "metadata" in call_args[1]

    @pytest.mark.asyncio
    async def test_create_assistant_not_connected(self, assistant_client):
        """Test creating assistant when not connected."""
        config = create_default_assistant_config("Test", "Test")

        with pytest.raises(ConnectionError, match="Not connected to LangGraph Cloud"):
            await assistant_client.create_assistant(config)

    @pytest.mark.asyncio
    async def test_get_assistant_success(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test getting an assistant successfully."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.get.return_value = mock_sdk_assistant

        result = await assistant_client.get_assistant("test-id")

        assert result == mock_sdk_assistant
        mock_sdk_client.assistants.get.assert_called_once_with("test-id")

    @pytest.mark.asyncio
    async def test_get_assistant_not_found(self, assistant_client, mock_sdk_client):
        """Test getting non-existent assistant."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.get.side_effect = Exception("Not found")

        result = await assistant_client.get_assistant("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_assistants(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test listing assistants."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.search.return_value = [mock_sdk_assistant]

        result = await assistant_client.list_assistants(limit=10, offset=0)

        assert len(result) == 1
        assert result[0] == mock_sdk_assistant
        mock_sdk_client.assistants.search.assert_called_once_with(limit=10, offset=0)

    @pytest.mark.asyncio
    async def test_list_assistants_with_graph_filter(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test listing assistants with graph ID filter."""
        assistant_client.client = mock_sdk_client

        # Create assistants with different graph IDs
        assistant1 = Mock(spec=SDKAssistant)
        assistant1.graph_id = "target_graph"

        assistant2 = Mock(spec=SDKAssistant)
        assistant2.graph_id = "other_graph"

        mock_sdk_client.assistants.search.return_value = [assistant1, assistant2]

        result = await assistant_client.list_assistants(graph_id="target_graph")

        assert len(result) == 1
        assert result[0].graph_id == "target_graph"

    @pytest.mark.asyncio
    async def test_update_assistant(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test updating an assistant."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.update.return_value = mock_sdk_assistant

        config = create_default_assistant_config(
            name="Updated Assistant",
            description="Updated description"
        )

        result = await assistant_client.update_assistant("test-id", config)

        assert result == mock_sdk_assistant

        # Verify update was called with correct data
        call_args = mock_sdk_client.assistants.update.call_args
        assert call_args[0][0] == "test-id"  # assistant_id
        assert call_args[1]["name"] == config.name

    @pytest.mark.asyncio
    async def test_delete_assistant(self, assistant_client, mock_sdk_client):
        """Test deleting an assistant."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.delete.return_value = None

        result = await assistant_client.delete_assistant("test-id")

        assert result is True
        mock_sdk_client.assistants.delete.assert_called_once_with("test-id")

    @pytest.mark.asyncio
    async def test_delete_assistant_failure(self, assistant_client, mock_sdk_client):
        """Test deleting assistant failure."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.delete.side_effect = Exception("Delete failed")

        with pytest.raises(Exception, match="Delete failed"):
            await assistant_client.delete_assistant("test-id")

    @pytest.mark.asyncio
    async def test_get_assistant_graphs(self, assistant_client, mock_sdk_client):
        """Test getting assistant graphs."""
        assistant_client.client = mock_sdk_client

        mock_graph = Mock(spec=GraphSchema)
        mock_graph.graph_id = "test_graph"
        mock_graph.name = "Test Graph"

        mock_sdk_client.assistants.get_schemas.return_value = [mock_graph]

        result = await assistant_client.get_assistant_graphs()

        assert len(result) == 1
        assert result[0] == mock_graph

    @pytest.mark.asyncio
    async def test_sync_from_yaml_success(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test successful sync from YAML files."""
        assistant_client.client = mock_sdk_client

        # Mock SDK responses
        mock_sdk_client.assistants.search.return_value = []  # No existing assistants
        mock_sdk_client.assistants.create.return_value = mock_sdk_assistant

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create test config files
            config1 = create_default_assistant_config("Assistant 1", "Description 1")
            config2 = create_default_assistant_config("Assistant 2", "Description 2")

            config1.to_yaml_file(config_dir / "assistant1.yaml")
            config2.to_yaml_file(config_dir / "assistant2.yaml")

            result = await assistant_client.sync_from_yaml(config_dir)

            assert result.created == 2
            assert result.updated == 0
            assert result.deleted == 0
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_sync_from_yaml_with_updates(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test sync from YAML with existing assistants to update."""
        assistant_client.client = mock_sdk_client

        # Create config
        config = create_default_assistant_config("Existing Assistant", "Description")

        # Mock existing assistant with same ID
        existing_assistant = Mock(spec=SDKAssistant)
        existing_assistant.assistant_id = config.assistant_id

        mock_sdk_client.assistants.search.return_value = [existing_assistant]
        mock_sdk_client.assistants.update.return_value = mock_sdk_assistant

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config.to_yaml_file(config_dir / "assistant.yaml")

            result = await assistant_client.sync_from_yaml(config_dir)

            assert result.created == 0
            assert result.updated == 1
            assert result.deleted == 0

    @pytest.mark.asyncio
    async def test_sync_from_yaml_with_deletions(self, assistant_client, mock_sdk_client):
        """Test sync from YAML with deletions."""
        assistant_client.client = mock_sdk_client

        # Mock existing assistant not in local configs
        existing_assistant = Mock(spec=SDKAssistant)
        existing_assistant.assistant_id = "orphaned-assistant"

        mock_sdk_client.assistants.search.return_value = [existing_assistant]
        mock_sdk_client.assistants.delete.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            # No config files - should delete existing assistant

            result = await assistant_client.sync_from_yaml(config_dir, delete_missing=True)

            assert result.created == 0
            assert result.updated == 0
            assert result.deleted == 1

    @pytest.mark.asyncio
    async def test_sync_from_yaml_with_errors(self, assistant_client, mock_sdk_client):
        """Test sync from YAML with errors."""
        assistant_client.client = mock_sdk_client

        mock_sdk_client.assistants.search.return_value = []
        mock_sdk_client.assistants.create.side_effect = Exception("Create failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            config = create_default_assistant_config("Test", "Test")
            config.to_yaml_file(config_dir / "assistant.yaml")

            result = await assistant_client.sync_from_yaml(config_dir)

            assert result.created == 0
            assert len(result.errors) == 1
            assert "Create failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_sync_to_yaml(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test sync to YAML files."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.search.return_value = [mock_sdk_assistant]

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            result = await assistant_client.sync_to_yaml(config_dir)

            assert result.created == 1
            assert len(result.errors) == 0

            # Check file was created
            files = list(config_dir.glob("*.yaml"))
            assert len(files) == 1

    @pytest.mark.asyncio
    async def test_sync_to_yaml_no_overwrite(self, assistant_client, mock_sdk_client, mock_sdk_assistant):
        """Test sync to YAML without overwriting existing files."""
        assistant_client.client = mock_sdk_client
        mock_sdk_client.assistants.search.return_value = [mock_sdk_assistant]

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create existing file with correct generated name (spaces removed)
            existing_file = config_dir / "testassistant.yaml"
            existing_file.touch()

            result = await assistant_client.sync_to_yaml(config_dir, overwrite_existing=False)

            # Should skip existing file
            assert result.created == 0

    def test_sdk_assistant_to_config_conversion(self, assistant_client, mock_sdk_assistant):
        """Test converting SDK assistant to AssistantConfig."""
        config = assistant_client._sdk_assistant_to_config(mock_sdk_assistant)

        assert config.name == mock_sdk_assistant.name
        assert config.assistant_id == mock_sdk_assistant.assistant_id
        assert config.graph_id == mock_sdk_assistant.graph_id
        assert config.description == mock_sdk_assistant.metadata["description"]
        assert config.tags == mock_sdk_assistant.metadata["tags"]
        assert config.enabled == mock_sdk_assistant.metadata["enabled"]

    def test_sdk_assistant_to_config_with_minimal_data(self, assistant_client):
        """Test converting SDK assistant with minimal data."""
        minimal_assistant = Mock(spec=SDKAssistant)
        minimal_assistant.assistant_id = "minimal-id"
        minimal_assistant.name = "Minimal Assistant"
        minimal_assistant.graph_id = "minimal_graph"
        minimal_assistant.metadata = {}
        minimal_assistant.config = {}
        minimal_assistant.created_at = None
        minimal_assistant.updated_at = None

        config = assistant_client._sdk_assistant_to_config(minimal_assistant)

        assert config.name == "Minimal Assistant"
        assert config.assistant_id == "minimal-id"
        assert config.description == "Assistant synced from cloud"
        assert config.tags == []
        assert config.enabled is True

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_client_config, mock_settings, mock_sdk_client):
        """Test async context manager functionality."""
        with patch('boss_bot.ai.assistants.client.get_client', return_value=mock_sdk_client):
            async with LangGraphAssistantClient(config=mock_client_config, settings=mock_settings) as client:
                assert client.client == mock_sdk_client
                # Health check should have been called during connect
                mock_sdk_client.assistants.search.assert_called_with(limit=1)

            # Client should be disconnected after context exit
            assert client.client is None


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.mark.asyncio
    async def test_create_assistant_client(self, mock_sdk_client):
        """Test creating and connecting assistant client."""
        with patch('boss_bot.ai.assistants.client.get_client', return_value=mock_sdk_client):
            client = await create_assistant_client()

            assert isinstance(client, LangGraphAssistantClient)
            assert client.client == mock_sdk_client

    @pytest.mark.asyncio
    async def test_sync_assistants_from_directory(self, mock_sdk_client):
        """Test syncing assistants from directory helper function."""
        with patch('boss_bot.ai.assistants.client.get_client', return_value=mock_sdk_client):
            mock_sdk_client.assistants.search.return_value = []

            with tempfile.TemporaryDirectory() as temp_dir:
                config_dir = Path(temp_dir)

                # Create test config
                config = create_default_assistant_config("Test", "Test")
                config.to_yaml_file(config_dir / "test.yaml")

                result = await sync_assistants_from_directory(
                    config_dir=config_dir,
                    deployment_url="https://api.langraph.com",
                    api_key="test-key"
                )

                assert isinstance(result, AssistantSyncResult)

    @pytest.mark.asyncio
    async def test_export_assistants_to_directory(self, mock_sdk_client, mock_sdk_assistant):
        """Test exporting assistants to directory helper function."""
        with patch('boss_bot.ai.assistants.client.get_client', return_value=mock_sdk_client):
            mock_sdk_client.assistants.search.return_value = [mock_sdk_assistant]

            with tempfile.TemporaryDirectory() as temp_dir:
                config_dir = Path(temp_dir)

                result = await export_assistants_to_directory(
                    config_dir=config_dir,
                    deployment_url="https://api.langraph.com",
                    api_key="test-key"
                )

                assert isinstance(result, AssistantSyncResult)
                assert result.created == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def assistant_client_with_mock(self, mock_client_config, mock_settings, mock_sdk_client):
        """Create assistant client with pre-connected mock."""
        client = LangGraphAssistantClient(config=mock_client_config, settings=mock_settings)
        client.client = mock_sdk_client
        return client

    @pytest.mark.asyncio
    async def test_create_assistant_error(self, assistant_client_with_mock):
        """Test error handling in create_assistant."""
        assistant_client_with_mock.client.assistants.create.side_effect = Exception("Create error")

        config = create_default_assistant_config("Test", "Test")

        with pytest.raises(Exception, match="Create error"):
            await assistant_client_with_mock.create_assistant(config)

    @pytest.mark.asyncio
    async def test_update_assistant_error(self, assistant_client_with_mock):
        """Test error handling in update_assistant."""
        assistant_client_with_mock.client.assistants.update.side_effect = Exception("Update error")

        config = create_default_assistant_config("Test", "Test")

        with pytest.raises(Exception, match="Update error"):
            await assistant_client_with_mock.update_assistant("test-id", config)

    @pytest.mark.asyncio
    async def test_list_assistants_error(self, assistant_client_with_mock):
        """Test error handling in list_assistants."""
        assistant_client_with_mock.client.assistants.search.side_effect = Exception("List error")

        with pytest.raises(Exception, match="List error"):
            await assistant_client_with_mock.list_assistants()

    @pytest.mark.asyncio
    async def test_get_assistant_graphs_error(self, assistant_client_with_mock):
        """Test error handling in get_assistant_graphs."""
        assistant_client_with_mock.client.assistants.get_schemas.side_effect = Exception("Schemas error")

        with pytest.raises(Exception, match="Schemas error"):
            await assistant_client_with_mock.get_assistant_graphs()

    @pytest.mark.asyncio
    async def test_sync_operations_not_connected(self, assistant_client):
        """Test sync operations when not connected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            with pytest.raises(ConnectionError, match="Not connected to LangGraph Cloud"):
                await assistant_client.sync_from_yaml(config_dir)

            with pytest.raises(ConnectionError, match="Not connected to LangGraph Cloud"):
                await assistant_client.sync_to_yaml(config_dir)


class TestConfigurationValidation:
    """Test configuration validation scenarios."""

    def test_invalid_deployment_url(self):
        """Test invalid deployment URL validation."""
        with pytest.raises(ValidationError):
            LangGraphClientConfig(deployment_url="not-a-url")

    def test_config_with_none_values(self):
        """Test configuration with None values where allowed."""
        config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            api_key=None
        )

        assert config.api_key is None

    def test_edge_case_timeouts(self):
        """Test edge case timeout values."""
        # Minimum timeout
        config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            timeout_seconds=1
        )
        assert config.timeout_seconds == 1

        # Maximum timeout
        config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl("https://api.langraph.com"),
            timeout_seconds=300
        )
        assert config.timeout_seconds == 300


class TestConcurrencyAndStateManagement:
    """Test concurrency and state management scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_health_checks(self, assistant_client, mock_sdk_client):
        """Test multiple concurrent health checks."""
        assistant_client.client = mock_sdk_client

        # Execute multiple health checks concurrently
        import asyncio
        results = await asyncio.gather(
            assistant_client.health_check(),
            assistant_client.health_check(),
            assistant_client.health_check()
        )

        # All should succeed
        assert all(results)

    @pytest.mark.asyncio
    async def test_client_state_after_error(self, assistant_client, mock_sdk_client):
        """Test client state after errors."""
        assistant_client.client = mock_sdk_client

        # Cause an error
        mock_sdk_client.assistants.search.side_effect = Exception("Error")

        # Health check should fail but client should remain connected
        result = await assistant_client.health_check()
        assert result is False
        assert assistant_client.client is not None

    @pytest.mark.asyncio
    async def test_reconnection_after_disconnect(self, assistant_client, mock_sdk_client):
        """Test reconnection after disconnect."""
        with patch('boss_bot.ai.assistants.client.get_client', return_value=mock_sdk_client):
            # Connect
            await assistant_client.connect()
            assert assistant_client.client is not None

            # Disconnect
            await assistant_client.disconnect()
            assert assistant_client.client is None

            # Reconnect
            await assistant_client.connect()
            assert assistant_client.client is not None
