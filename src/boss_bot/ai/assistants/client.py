"""LangGraph SDK client for assistant management.

This module provides a comprehensive interface for managing LangGraph assistants
through the LangGraph Cloud API, including CRUD operations, configuration
synchronization, and deployment management.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langgraph_sdk import get_client
from langgraph_sdk.schema import Assistant as SDKAssistant
from langgraph_sdk.schema import GraphSchema
from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, ValidationError

from boss_bot.ai.assistants.models import (
    Assistant,
    AssistantConfig,
    AssistantMetadata,
    AssistantStatus,
    load_assistant_configs,
    save_assistant_configs,
)
from boss_bot.core.env import BossSettings

logger = logging.getLogger(__name__)


class LangGraphClientConfig(BaseModel):
    """Configuration for LangGraph SDK client.

    Attributes:
        deployment_url: LangGraph Cloud deployment URL
        api_key: API key for authentication
        timeout_seconds: Request timeout in seconds
        max_retries: Maximum number of retries for failed requests
        enable_tracing: Enable request tracing
    """

    deployment_url: AnyHttpUrl = Field(..., description="LangGraph Cloud deployment URL")
    api_key: SecretStr | None = Field(None, description="API key for authentication")
    timeout_seconds: int = Field(default=30, gt=0, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum number of retries for failed requests")
    enable_tracing: bool = Field(default=False, description="Enable request tracing")


class AssistantSyncResult(BaseModel):
    """Result of assistant synchronization operation.

    Attributes:
        created: Number of assistants created
        updated: Number of assistants updated
        deleted: Number of assistants deleted
        errors: List of synchronization errors
        synchronized_at: When synchronization completed
    """

    created: int = Field(default=0, ge=0)
    updated: int = Field(default=0, ge=0)
    deleted: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
    synchronized_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_changes(self) -> int:
        """Total number of changes made."""
        return self.created + self.updated + self.deleted

    @property
    def success(self) -> bool:
        """Whether synchronization was successful."""
        return len(self.errors) == 0


class LangGraphAssistantClient:
    """LangGraph SDK client for assistant management.

    This client provides a comprehensive interface for managing LangGraph assistants
    through the LangGraph Cloud API, including CRUD operations, configuration
    synchronization, and deployment management.

    Features:
    - Full CRUD operations for assistants
    - Configuration synchronization between local YAML and cloud
    - Health checks and connection testing
    - Error handling and retry logic
    - Support for both local development and cloud deployment

    Attributes:
        config: Client configuration
        client: LangGraph SDK client instance
        settings: Boss-Bot application settings
    """

    def __init__(
        self,
        config: LangGraphClientConfig | None = None,
        settings: BossSettings | None = None,
    ) -> None:
        """Initialize LangGraph assistant client.

        Args:
            config: Client configuration (auto-detected if None)
            settings: Application settings (auto-loaded if None)
        """
        self.settings = settings or BossSettings()
        self.config = config or self._create_default_config()
        self.client = None
        self._last_health_check: datetime | None = None
        self._health_check_interval_seconds = 300  # 5 minutes

        logger.info(f"Initialized LangGraph assistant client for {self.config.deployment_url}")

    def _create_default_config(self) -> LangGraphClientConfig:
        """Create default client configuration from environment.

        Returns:
            Default LangGraphClientConfig
        """
        # Try to detect deployment URL from various sources
        deployment_url = None
        api_key = None

        # Check LangGraph-specific settings first
        if hasattr(self.settings, "langgraph_deployment_url"):
            deployment_url = str(self.settings.langgraph_deployment_url)

        if hasattr(self.settings, "langgraph_api_key") and self.settings.langgraph_api_key:
            api_key = self.settings.langgraph_api_key

        # Fallback to LangChain settings
        if not deployment_url and hasattr(self.settings, "langchain_endpoint"):
            deployment_url = str(self.settings.langchain_endpoint)

        if not api_key and hasattr(self.settings, "langchain_api_key"):
            api_key = self.settings.langchain_api_key

        # Fallback to localhost for development
        if not deployment_url:
            deployment_url = "http://localhost:8000"

        return LangGraphClientConfig(
            deployment_url=AnyHttpUrl(deployment_url),
            api_key=api_key,
            timeout_seconds=30,
            max_retries=3,
            enable_tracing=getattr(self.settings, "langchain_tracing_v2", False),
        )

    async def connect(self) -> None:
        """Establish connection to LangGraph Cloud.

        Raises:
            ConnectionError: If connection fails
            ValueError: If configuration is invalid
        """
        try:
            # Prepare client kwargs
            client_kwargs = {
                "url": str(self.config.deployment_url),
                "timeout": self.config.timeout_seconds,
            }

            # Add API key if available
            if self.config.api_key:
                client_kwargs["api_key"] = self.config.api_key.get_secret_value()

            # Create LangGraph SDK client using get_client
            self.client = get_client(**client_kwargs)

            # Test connection
            await self.health_check()

            logger.info(f"Successfully connected to LangGraph Cloud at {self.config.deployment_url}")

        except Exception as e:
            logger.error(f"Failed to connect to LangGraph Cloud: {e}")
            raise ConnectionError(f"LangGraph Cloud connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from LangGraph Cloud."""
        if self.client:
            # LangGraph SDK client may need cleanup
            if hasattr(self.client, "close"):
                try:
                    await self.client.close()
                except Exception as e:
                    logger.warning(f"Error closing client: {e}")

            self.client = None
            self._last_health_check = None
            logger.info("Disconnected from LangGraph Cloud")

    async def health_check(self, force: bool = False) -> bool:
        """Check connection health.

        Args:
            force: Force health check even if recently performed

        Returns:
            True if healthy, False otherwise

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        # Skip if recently checked (unless forced)
        now = datetime.utcnow()
        if (
            not force
            and self._last_health_check
            and (now - self._last_health_check).total_seconds() < self._health_check_interval_seconds
        ):
            return True

        try:
            # Try to search assistants as a health check with minimal results
            # This is a lightweight operation that tests connectivity
            await self.client.assistants.search(limit=1)

            self._last_health_check = now
            logger.debug("LangGraph Cloud health check passed")
            return True

        except Exception as e:
            logger.warning(f"LangGraph Cloud health check failed: {e}")
            return False

    async def create_assistant(self, config: AssistantConfig) -> SDKAssistant:
        """Create a new assistant in LangGraph Cloud.

        Args:
            config: Assistant configuration

        Returns:
            Created assistant from LangGraph Cloud

        Raises:
            ConnectionError: If not connected
            ValueError: If configuration is invalid
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        try:
            # Convert config to LangGraph format
            assistant_data = {
                "graph_id": config.graph_id,
                "name": config.name,
                "config": config.to_config_schema(),
                "metadata": {
                    "description": config.description,
                    "assistant_id": config.assistant_id,
                    "tags": config.tags,
                    "enabled": config.enabled,
                    "created_by": "boss-bot",
                    "version": config.metadata.version,
                },
            }

            # Create assistant via SDK
            assistant = await self.client.assistants.create(**assistant_data)

            logger.info(f"Created assistant '{config.name}' with ID: {assistant.assistant_id}")
            return assistant

        except Exception as e:
            logger.error(f"Failed to create assistant '{config.name}': {e}")
            raise

    async def get_assistant(self, assistant_id: str) -> SDKAssistant | None:
        """Get assistant by ID.

        Args:
            assistant_id: Assistant identifier

        Returns:
            Assistant if found, None otherwise

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        try:
            assistant = await self.client.assistants.get(assistant_id)
            logger.debug(f"Retrieved assistant: {assistant_id}")
            return assistant

        except Exception as e:
            logger.debug(f"Assistant not found: {assistant_id} - {e}")
            return None

    async def list_assistants(
        self,
        limit: int | None = None,
        offset: int | None = None,
        graph_id: str | None = None,
    ) -> list[SDKAssistant]:
        """List assistants from LangGraph Cloud.

        Args:
            limit: Maximum number of assistants to return
            offset: Number of assistants to skip
            graph_id: Filter by graph ID

        Returns:
            List of assistants

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        try:
            # Build search parameters
            search_params = {}
            if limit is not None:
                search_params["limit"] = limit
            if offset is not None:
                search_params["offset"] = offset

            # Search assistants
            assistants = await self.client.assistants.search(**search_params)

            # Filter by graph_id if specified
            if graph_id:
                assistants = [a for a in assistants if a.graph_id == graph_id]

            logger.debug(f"Listed {len(assistants)} assistants")
            return assistants

        except Exception as e:
            logger.error(f"Failed to list assistants: {e}")
            raise

    async def update_assistant(
        self,
        assistant_id: str,
        config: AssistantConfig,
    ) -> SDKAssistant:
        """Update assistant configuration.

        Args:
            assistant_id: Assistant identifier
            config: Updated assistant configuration

        Returns:
            Updated assistant

        Raises:
            ConnectionError: If not connected
            ValueError: If assistant not found
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        try:
            # Prepare update data
            update_data = {
                "name": config.name,
                "config": config.to_config_schema(),
                "metadata": {
                    "description": config.description,
                    "assistant_id": config.assistant_id,
                    "tags": config.tags,
                    "enabled": config.enabled,
                    "updated_by": "boss-bot",
                    "version": config.metadata.version,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            }

            # Update assistant via SDK
            assistant = await self.client.assistants.update(assistant_id, **update_data)

            logger.info(f"Updated assistant '{config.name}' (ID: {assistant_id})")
            return assistant

        except Exception as e:
            logger.error(f"Failed to update assistant '{assistant_id}': {e}")
            raise

    async def delete_assistant(self, assistant_id: str) -> bool:
        """Delete assistant from LangGraph Cloud.

        Args:
            assistant_id: Assistant identifier

        Returns:
            True if deleted successfully

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        try:
            await self.client.assistants.delete(assistant_id)
            logger.info(f"Deleted assistant: {assistant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete assistant '{assistant_id}': {e}")
            raise

    async def get_assistant_graphs(self) -> list[Any]:
        """Get available assistant graphs.

        Returns:
            List of available graphs

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        try:
            # Get available schemas which represents graphs
            schemas = await self.client.assistants.get_schemas()
            logger.debug(f"Retrieved {len(schemas)} assistant schemas")
            return schemas

        except Exception as e:
            logger.error(f"Failed to get assistant graphs: {e}")
            raise

    async def sync_from_yaml(
        self,
        config_dir: Path,
        delete_missing: bool = False,
    ) -> AssistantSyncResult:
        """Synchronize assistants from local YAML configurations.

        Args:
            config_dir: Directory containing YAML configuration files
            delete_missing: Whether to delete cloud assistants not found locally

        Returns:
            Synchronization result

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        result = AssistantSyncResult()

        try:
            # Load local configurations
            local_configs = load_assistant_configs(config_dir)
            logger.info(f"Loaded {len(local_configs)} local assistant configurations")

            # Get cloud assistants
            cloud_assistants = await self.list_assistants()
            cloud_assistant_ids = {a.assistant_id for a in cloud_assistants}

            # Sync each local config
            for config in local_configs:
                try:
                    if config.assistant_id in cloud_assistant_ids:
                        # Update existing assistant
                        await self.update_assistant(config.assistant_id, config)
                        result.updated += 1
                        logger.info(f"Updated assistant: {config.name}")
                    else:
                        # Create new assistant
                        await self.create_assistant(config)
                        result.created += 1
                        logger.info(f"Created assistant: {config.name}")

                except Exception as e:
                    error_msg = f"Failed to sync assistant '{config.name}': {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

            # Delete missing assistants if requested
            if delete_missing:
                local_assistant_ids = {config.assistant_id for config in local_configs}
                for cloud_assistant in cloud_assistants:
                    if cloud_assistant.assistant_id not in local_assistant_ids:
                        try:
                            await self.delete_assistant(cloud_assistant.assistant_id)
                            result.deleted += 1
                            logger.info(f"Deleted missing assistant: {cloud_assistant.assistant_id}")
                        except Exception as e:
                            error_msg = f"Failed to delete assistant '{cloud_assistant.assistant_id}': {e}"
                            result.errors.append(error_msg)
                            logger.error(error_msg)

            logger.info(
                f"Sync completed: {result.created} created, {result.updated} updated, "
                f"{result.deleted} deleted, {len(result.errors)} errors"
            )

        except Exception as e:
            error_msg = f"Sync operation failed: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        return result

    async def sync_to_yaml(
        self,
        config_dir: Path,
        overwrite_existing: bool = False,
    ) -> AssistantSyncResult:
        """Synchronize cloud assistants to local YAML configurations.

        Args:
            config_dir: Directory where to save YAML configurations
            overwrite_existing: Whether to overwrite existing local files

        Returns:
            Synchronization result

        Raises:
            ConnectionError: If not connected
        """
        if not self.client:
            raise ConnectionError("Not connected to LangGraph Cloud")

        result = AssistantSyncResult()

        try:
            # Get cloud assistants
            cloud_assistants = await self.list_assistants()
            logger.info(f"Retrieved {len(cloud_assistants)} cloud assistants")

            # Ensure config directory exists
            config_dir.mkdir(parents=True, exist_ok=True)

            # Convert each cloud assistant to local config
            configs_to_save = []
            for cloud_assistant in cloud_assistants:
                try:
                    # Convert SDK assistant to AssistantConfig
                    config = self._sdk_assistant_to_config(cloud_assistant)
                    configs_to_save.append(config)

                    # Generate safe filename
                    safe_name = "".join(c for c in config.name if c.isalnum() or c in "-_").lower()
                    file_path = config_dir / f"{safe_name}.yaml"

                    # Check if file exists
                    if file_path.exists() and not overwrite_existing:
                        logger.warning(f"Skipping existing file: {file_path}")
                        continue

                    # Save configuration
                    config.to_yaml_file(file_path)
                    result.created += 1
                    logger.info(f"Saved assistant config: {config.name} to {file_path}")

                except Exception as e:
                    error_msg = f"Failed to save assistant '{cloud_assistant.assistant_id}': {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

            logger.info(f"Sync to YAML completed: {result.created} saved, {len(result.errors)} errors")

        except Exception as e:
            error_msg = f"Sync to YAML failed: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        return result

    def _sdk_assistant_to_config(self, sdk_assistant: SDKAssistant) -> AssistantConfig:
        """Convert SDK assistant to AssistantConfig.

        Args:
            sdk_assistant: SDK assistant object

        Returns:
            AssistantConfig instance
        """
        # Extract metadata
        metadata = sdk_assistant.metadata or {}

        # Build configuration data
        config_data = {
            "name": sdk_assistant.name,
            "description": metadata.get("description", "Assistant synced from cloud"),
            "assistant_id": sdk_assistant.assistant_id,
            "graph_id": sdk_assistant.graph_id,
            "tags": metadata.get("tags", []),
            "enabled": metadata.get("enabled", True),
        }

        # Add SDK config if available
        if hasattr(sdk_assistant, "config") and sdk_assistant.config:
            # Map SDK config to our format
            sdk_config = sdk_assistant.config

            # AI configuration
            if any(key in sdk_config for key in ["enable_ai_strategy_selection", "ai_model", "ai_temperature"]):
                config_data["ai"] = {
                    "enable_ai_strategy_selection": sdk_config.get("enable_ai_strategy_selection", True),
                    "enable_content_analysis": sdk_config.get("enable_content_analysis", True),
                    "ai_model": sdk_config.get("ai_model", "gpt-4"),
                    "ai_temperature": sdk_config.get("ai_temperature", 0.3),
                    "ai_max_tokens": sdk_config.get("ai_max_tokens", 1000),
                    "ai_timeout_seconds": sdk_config.get("ai_timeout_seconds", 30),
                }

            # Download configuration
            if any(key in sdk_config for key in ["max_retries", "timeout_seconds", "download_quality"]):
                config_data["download"] = {
                    "max_retries": sdk_config.get("max_retries", 3),
                    "timeout_seconds": sdk_config.get("timeout_seconds", 300),
                    "download_quality": sdk_config.get("download_quality", "good"),
                    "max_concurrent_downloads": sdk_config.get("max_concurrent_downloads", 3),
                    "enable_fallback": sdk_config.get("enable_fallback", True),
                }

            # Platform configuration
            platform_keys = [
                "youtube_quality",
                "twitter_include_replies",
                "instagram_include_stories",
                "reddit_include_comments",
            ]
            if any(key in sdk_config for key in platform_keys):
                config_data["platforms"] = {
                    "youtube_quality": sdk_config.get("youtube_quality", "720p"),
                    "twitter_include_replies": sdk_config.get("twitter_include_replies", False),
                    "instagram_include_stories": sdk_config.get("instagram_include_stories", True),
                    "reddit_include_comments": sdk_config.get("reddit_include_comments", False),
                    "generic_user_agent": sdk_config.get(
                        "generic_user_agent", "Mozilla/5.0 (compatible; Boss-Bot/1.0)"
                    ),
                }

        # Set metadata
        config_data["metadata"] = {
            "version": metadata.get("version", "1.0.0"),
            "created_at": sdk_assistant.created_at or datetime.utcnow(),
            "updated_at": sdk_assistant.updated_at or datetime.utcnow(),
        }

        return AssistantConfig.model_validate(config_data)

    async def __aenter__(self) -> LangGraphAssistantClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()


# Helper functions for client management


async def create_assistant_client(
    settings: BossSettings | None = None,
    config: LangGraphClientConfig | None = None,
) -> LangGraphAssistantClient:
    """Create and connect LangGraph assistant client.

    Args:
        settings: Application settings
        config: Client configuration

    Returns:
        Connected LangGraph assistant client

    Raises:
        ConnectionError: If connection fails
    """
    client = LangGraphAssistantClient(config=config, settings=settings)
    await client.connect()
    return client


async def sync_assistants_from_directory(
    config_dir: Path,
    deployment_url: str | None = None,
    api_key: str | None = None,
    delete_missing: bool = False,
) -> AssistantSyncResult:
    """Synchronize assistants from a configuration directory.

    Args:
        config_dir: Directory containing YAML configuration files
        deployment_url: LangGraph Cloud deployment URL
        api_key: API key for authentication
        delete_missing: Whether to delete cloud assistants not found locally

    Returns:
        Synchronization result
    """
    # Create client configuration if URL provided
    client_config = None
    if deployment_url:
        client_config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl(deployment_url),
            api_key=SecretStr(api_key) if api_key else None,
        )

    # Create and use client
    async with LangGraphAssistantClient(config=client_config) as client:
        return await client.sync_from_yaml(config_dir, delete_missing=delete_missing)


async def export_assistants_to_directory(
    config_dir: Path,
    deployment_url: str | None = None,
    api_key: str | None = None,
    overwrite_existing: bool = False,
) -> AssistantSyncResult:
    """Export cloud assistants to a configuration directory.

    Args:
        config_dir: Directory where to save YAML configurations
        deployment_url: LangGraph Cloud deployment URL
        api_key: API key for authentication
        overwrite_existing: Whether to overwrite existing local files

    Returns:
        Synchronization result
    """
    # Create client configuration if URL provided
    client_config = None
    if deployment_url:
        client_config = LangGraphClientConfig(
            deployment_url=AnyHttpUrl(deployment_url),
            api_key=SecretStr(api_key) if api_key else None,
        )

    # Create and use client
    async with LangGraphAssistantClient(config=client_config) as client:
        return await client.sync_to_yaml(config_dir, overwrite_existing=overwrite_existing)
