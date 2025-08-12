"""Comprehensive tests for LangGraph assistant Pydantic models and YAML operations.

This module tests all Pydantic models, validation, serialization/deserialization,
and YAML operations for the assistant management system.
"""

from __future__ import annotations

import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from pydantic import ValidationError

from boss_bot.ai.assistants.models import (
    AIConfiguration,
    Assistant,
    AssistantConfig,
    AssistantMetadata,
    AssistantStatus,
    DownloadConfiguration,
    PlatformConfiguration,
    PlatformType,
    QualityLevel,
    WorkflowConfiguration,
    create_default_assistant_config,
    load_assistant_configs,
    save_assistant_configs,
)


class TestPlatformType:
    """Test PlatformType enum."""

    def test_platform_type_values(self):
        """Test all platform type enum values."""
        assert PlatformType.YOUTUBE == "youtube"
        assert PlatformType.TWITTER == "twitter"
        assert PlatformType.INSTAGRAM == "instagram"
        assert PlatformType.REDDIT == "reddit"
        assert PlatformType.GENERIC == "generic"

    def test_platform_type_membership(self):
        """Test platform type membership checks."""
        assert "youtube" in PlatformType
        assert "twitter" in PlatformType
        assert "invalid_platform" not in PlatformType

    def test_platform_type_iteration(self):
        """Test iterating over platform types."""
        platforms = list(PlatformType)
        assert len(platforms) == 5
        assert PlatformType.YOUTUBE in platforms


class TestQualityLevel:
    """Test QualityLevel enum."""

    def test_quality_level_values(self):
        """Test all quality level enum values."""
        assert QualityLevel.LOW == "low"
        assert QualityLevel.GOOD == "good"
        assert QualityLevel.HIGH == "high"
        assert QualityLevel.BEST == "best"

    def test_quality_level_ordering(self):
        """Test quality levels can be used for ordering."""
        qualities = [QualityLevel.LOW, QualityLevel.GOOD, QualityLevel.HIGH, QualityLevel.BEST]
        quality_values = [q.value for q in qualities]
        assert quality_values == ["low", "good", "high", "best"]


class TestAssistantStatus:
    """Test AssistantStatus enum."""

    def test_assistant_status_values(self):
        """Test all assistant status enum values."""
        assert AssistantStatus.ACTIVE == "active"
        assert AssistantStatus.INACTIVE == "inactive"
        assert AssistantStatus.ERROR == "error"
        assert AssistantStatus.INITIALIZING == "initializing"

    def test_assistant_status_membership(self):
        """Test assistant status membership checks."""
        assert "active" in AssistantStatus
        assert "unknown" not in AssistantStatus


class TestAIConfiguration:
    """Test AIConfiguration model."""

    def test_default_ai_configuration(self):
        """Test default AI configuration values."""
        config = AIConfiguration()

        assert config.enable_ai_strategy_selection is True
        assert config.enable_content_analysis is True
        assert config.ai_model == "gpt-4"
        assert config.ai_temperature == 0.3
        assert config.ai_max_tokens == 1000
        assert config.ai_timeout_seconds == 30

    def test_ai_configuration_custom_values(self):
        """Test AI configuration with custom values."""
        config = AIConfiguration(
            enable_ai_strategy_selection=False,
            enable_content_analysis=False,
            ai_model="claude-3",
            ai_temperature=0.7,
            ai_max_tokens=2000,
            ai_timeout_seconds=60,
        )

        assert config.enable_ai_strategy_selection is False
        assert config.enable_content_analysis is False
        assert config.ai_model == "claude-3"
        assert config.ai_temperature == 0.7
        assert config.ai_max_tokens == 2000
        assert config.ai_timeout_seconds == 60

    def test_ai_temperature_validation(self):
        """Test AI temperature validation."""
        # Valid temperatures
        AIConfiguration(ai_temperature=0.0)
        AIConfiguration(ai_temperature=0.5)
        AIConfiguration(ai_temperature=1.0)

        # Invalid temperatures
        with pytest.raises(ValidationError):
            AIConfiguration(ai_temperature=-0.1)

        with pytest.raises(ValidationError):
            AIConfiguration(ai_temperature=1.1)

    def test_ai_max_tokens_validation(self):
        """Test AI max tokens validation."""
        # Valid values
        AIConfiguration(ai_max_tokens=1)
        AIConfiguration(ai_max_tokens=1000)
        AIConfiguration(ai_max_tokens=10000)

        # Invalid values
        with pytest.raises(ValidationError):
            AIConfiguration(ai_max_tokens=0)

        with pytest.raises(ValidationError):
            AIConfiguration(ai_max_tokens=-1)

    def test_ai_timeout_validation(self):
        """Test AI timeout validation."""
        # Valid values
        AIConfiguration(ai_timeout_seconds=1)
        AIConfiguration(ai_timeout_seconds=30)
        AIConfiguration(ai_timeout_seconds=300)

        # Invalid values
        with pytest.raises(ValidationError):
            AIConfiguration(ai_timeout_seconds=0)

        with pytest.raises(ValidationError):
            AIConfiguration(ai_timeout_seconds=-1)

    def test_ai_model_validation(self):
        """Test AI model validation."""
        # Valid models
        config = AIConfiguration(ai_model="gpt-4")
        assert config.ai_model == "gpt-4"

        config = AIConfiguration(ai_model="  Claude-3  ")
        assert config.ai_model == "claude-3"  # Should be stripped and lowercased

        # Whitespace-only string - should be allowed but stripped to empty
        config = AIConfiguration(ai_model="   ")
        assert config.ai_model == ""  # After stripping

        # Invalid models - empty strings should fail validation
        with pytest.raises(ValidationError, match="AI model must be a non-empty string"):
            AIConfiguration(ai_model="")


class TestDownloadConfiguration:
    """Test DownloadConfiguration model."""

    def test_default_download_configuration(self):
        """Test default download configuration values."""
        config = DownloadConfiguration()

        assert config.max_retries == 3
        assert config.timeout_seconds == 300
        assert config.download_quality == QualityLevel.GOOD
        assert config.max_concurrent_downloads == 3
        assert config.enable_fallback is True

    def test_download_configuration_custom_values(self):
        """Test download configuration with custom values."""
        config = DownloadConfiguration(
            max_retries=5,
            timeout_seconds=600,
            download_quality=QualityLevel.BEST,
            max_concurrent_downloads=5,
            enable_fallback=False,
        )

        assert config.max_retries == 5
        assert config.timeout_seconds == 600
        assert config.download_quality == QualityLevel.BEST
        assert config.max_concurrent_downloads == 5
        assert config.enable_fallback is False

    def test_max_retries_validation(self):
        """Test max retries validation."""
        # Valid values
        DownloadConfiguration(max_retries=0)
        DownloadConfiguration(max_retries=5)
        DownloadConfiguration(max_retries=10)

        # Invalid values
        with pytest.raises(ValidationError):
            DownloadConfiguration(max_retries=-1)

        with pytest.raises(ValidationError):
            DownloadConfiguration(max_retries=11)

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid values
        DownloadConfiguration(timeout_seconds=1)
        DownloadConfiguration(timeout_seconds=300)
        DownloadConfiguration(timeout_seconds=3600)

        # Invalid values
        with pytest.raises(ValidationError):
            DownloadConfiguration(timeout_seconds=0)

        with pytest.raises(ValidationError):
            DownloadConfiguration(timeout_seconds=3601)

    def test_max_concurrent_downloads_validation(self):
        """Test max concurrent downloads validation."""
        # Valid values
        DownloadConfiguration(max_concurrent_downloads=1)
        DownloadConfiguration(max_concurrent_downloads=5)
        DownloadConfiguration(max_concurrent_downloads=10)

        # Invalid values
        with pytest.raises(ValidationError):
            DownloadConfiguration(max_concurrent_downloads=0)

        with pytest.raises(ValidationError):
            DownloadConfiguration(max_concurrent_downloads=11)


class TestPlatformConfiguration:
    """Test PlatformConfiguration model."""

    def test_default_platform_configuration(self):
        """Test default platform configuration values."""
        config = PlatformConfiguration()

        assert config.youtube_quality == "720p"
        assert config.twitter_include_replies is False
        assert config.instagram_include_stories is True
        assert config.reddit_include_comments is False
        assert config.generic_user_agent == "Mozilla/5.0 (compatible; Boss-Bot/1.0)"

    def test_platform_configuration_custom_values(self):
        """Test platform configuration with custom values."""
        config = PlatformConfiguration(
            youtube_quality="1080p",
            twitter_include_replies=True,
            instagram_include_stories=False,
            reddit_include_comments=True,
            generic_user_agent="Custom-Bot/2.0",
        )

        assert config.youtube_quality == "1080p"
        assert config.twitter_include_replies is True
        assert config.instagram_include_stories is False
        assert config.reddit_include_comments is True
        assert config.generic_user_agent == "Custom-Bot/2.0"

    def test_youtube_quality_validation(self):
        """Test YouTube quality validation."""
        # Valid qualities
        valid_qualities = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "best", "worst"]
        for quality in valid_qualities:
            config = PlatformConfiguration(youtube_quality=quality)
            assert config.youtube_quality == quality

        # Invalid quality
        with pytest.raises(ValidationError):
            PlatformConfiguration(youtube_quality="invalid_quality")


class TestWorkflowConfiguration:
    """Test WorkflowConfiguration model."""

    def test_default_workflow_configuration(self):
        """Test default workflow configuration values."""
        config = WorkflowConfiguration()

        assert config.enable_parallel_processing is True
        assert config.max_workflow_duration_seconds == 600
        assert config.enable_detailed_logging is False
        assert config.checkpoint_interval_seconds == 30

    def test_workflow_configuration_custom_values(self):
        """Test workflow configuration with custom values."""
        config = WorkflowConfiguration(
            enable_parallel_processing=False,
            max_workflow_duration_seconds=1200,
            enable_detailed_logging=True,
            checkpoint_interval_seconds=60,
        )

        assert config.enable_parallel_processing is False
        assert config.max_workflow_duration_seconds == 1200
        assert config.enable_detailed_logging is True
        assert config.checkpoint_interval_seconds == 60

    def test_max_workflow_duration_validation(self):
        """Test max workflow duration validation."""
        # Valid values
        WorkflowConfiguration(max_workflow_duration_seconds=1)
        WorkflowConfiguration(max_workflow_duration_seconds=600)
        WorkflowConfiguration(max_workflow_duration_seconds=3600)

        # Invalid values
        with pytest.raises(ValidationError):
            WorkflowConfiguration(max_workflow_duration_seconds=0)

        with pytest.raises(ValidationError):
            WorkflowConfiguration(max_workflow_duration_seconds=3601)

    def test_checkpoint_interval_validation(self):
        """Test checkpoint interval validation."""
        # Valid values
        WorkflowConfiguration(checkpoint_interval_seconds=1)
        WorkflowConfiguration(checkpoint_interval_seconds=30)
        WorkflowConfiguration(checkpoint_interval_seconds=300)

        # Invalid values
        with pytest.raises(ValidationError):
            WorkflowConfiguration(checkpoint_interval_seconds=0)


class TestAssistantMetadata:
    """Test AssistantMetadata model."""

    def test_default_metadata(self):
        """Test default metadata values."""
        metadata = AssistantMetadata()

        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
        assert metadata.version == "1.0.0"
        assert metadata.total_requests == 0
        assert metadata.successful_requests == 0
        assert metadata.failed_requests == 0
        assert metadata.average_response_time_seconds == 0.0
        assert metadata.last_used_at is None

    def test_metadata_custom_values(self):
        """Test metadata with custom values."""
        now = datetime.utcnow()
        metadata = AssistantMetadata(
            created_at=now,
            updated_at=now,
            version="2.1.0",
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time_seconds=1.5,
            last_used_at=now,
        )

        assert metadata.created_at == now
        assert metadata.updated_at == now
        assert metadata.version == "2.1.0"
        assert metadata.total_requests == 100
        assert metadata.successful_requests == 95
        assert metadata.failed_requests == 5
        assert metadata.average_response_time_seconds == 1.5
        assert metadata.last_used_at == now

    def test_version_validation(self):
        """Test version validation."""
        # Valid versions
        AssistantMetadata(version="1.0.0")
        AssistantMetadata(version="10.20.30")
        AssistantMetadata(version="1.0.0-alpha")
        AssistantMetadata(version="1.0.0-beta1")  # More restrictive pattern

        # Invalid versions
        with pytest.raises(ValidationError, match="Version must follow semantic versioning"):
            AssistantMetadata(version="1.0")

        with pytest.raises(ValidationError, match="Version must follow semantic versioning"):
            AssistantMetadata(version="invalid")

        with pytest.raises(ValidationError, match="Version must follow semantic versioning"):
            AssistantMetadata(version="1.0.0.0")

    def test_request_counts_validation(self):
        """Test request counts validation."""
        # Valid counts
        AssistantMetadata(
            total_requests=100,
            successful_requests=90,
            failed_requests=10
        )

        AssistantMetadata(
            total_requests=100,
            successful_requests=100,
            failed_requests=0
        )

        # Invalid counts - sum exceeds total
        with pytest.raises(ValidationError):
            AssistantMetadata(
                total_requests=100,
                successful_requests=90,
                failed_requests=20  # 90 + 20 > 100
            )

    def test_negative_values_validation(self):
        """Test validation of negative values."""
        # Negative values should be rejected
        with pytest.raises(ValidationError):
            AssistantMetadata(total_requests=-1)

        with pytest.raises(ValidationError):
            AssistantMetadata(successful_requests=-1)

        with pytest.raises(ValidationError):
            AssistantMetadata(failed_requests=-1)

        with pytest.raises(ValidationError):
            AssistantMetadata(average_response_time_seconds=-1.0)


class TestAssistantConfig:
    """Test AssistantConfig model."""

    def test_default_assistant_config(self):
        """Test default assistant configuration."""
        config = AssistantConfig(
            name="Test Assistant",
            description="Test description"
        )

        assert config.name == "Test Assistant"
        assert config.description == "Test description"
        assert isinstance(config.assistant_id, str)
        assert len(config.assistant_id) > 0
        assert config.graph_id == "download_workflow"
        assert isinstance(config.ai, AIConfiguration)
        assert isinstance(config.download, DownloadConfiguration)
        assert isinstance(config.platforms, PlatformConfiguration)
        assert isinstance(config.workflow, WorkflowConfiguration)
        assert isinstance(config.metadata, AssistantMetadata)
        assert config.tags == []
        assert config.enabled is True

    def test_assistant_config_custom_values(self):
        """Test assistant config with custom values."""
        config = AssistantConfig(
            name="Custom Assistant",
            description="Custom description",
            assistant_id="custom-id-123",
            graph_id="custom_workflow",
            tags=["test", "custom"],
            enabled=False
        )

        assert config.name == "Custom Assistant"
        assert config.description == "Custom description"
        assert config.assistant_id == "custom-id-123"
        assert config.graph_id == "custom_workflow"
        # Tags are processed by validator - sorted and cleaned
        assert sorted(config.tags) == sorted(["test", "custom"])
        assert config.enabled is False

    def test_name_validation(self):
        """Test name validation."""
        # Valid names
        AssistantConfig(name="Valid Name", description="Test")
        AssistantConfig(name="A" * 100, description="Test")  # Max length

        # Invalid names
        with pytest.raises(ValidationError):
            AssistantConfig(name="", description="Test")  # Empty

        with pytest.raises(ValidationError):
            AssistantConfig(name="A" * 101, description="Test")  # Too long

    def test_description_validation(self):
        """Test description validation."""
        # Valid descriptions
        AssistantConfig(name="Test", description="Valid description")
        AssistantConfig(name="Test", description="A" * 500)  # Max length

        # Invalid descriptions
        with pytest.raises(ValidationError):
            AssistantConfig(name="Test", description="")  # Empty

        with pytest.raises(ValidationError):
            AssistantConfig(name="Test", description="A" * 501)  # Too long

    def test_assistant_id_validation(self):
        """Test assistant ID validation."""
        # Valid IDs
        config = AssistantConfig(name="Test", description="Test", assistant_id="valid-id")
        assert config.assistant_id == "valid-id"

        config = AssistantConfig(name="Test", description="Test", assistant_id="  spaced-id  ")
        assert config.assistant_id == "spaced-id"  # Should be stripped

        # Invalid IDs
        with pytest.raises(ValidationError):
            AssistantConfig(name="Test", description="Test", assistant_id="")

        with pytest.raises(ValidationError):
            AssistantConfig(name="Test", description="Test", assistant_id="   ")

    def test_tags_validation(self):
        """Test tags validation and cleanup."""
        config = AssistantConfig(
            name="Test",
            description="Test",
            tags=["Tag1", "tag2", "TAG1", "  tag3  ", "", "tag2"]
        )

        # Should be cleaned: lowercased, stripped, deduplicated, empty removed
        expected_tags = ["tag1", "tag2", "tag3"]
        assert sorted(config.tags) == sorted(expected_tags)

    def test_to_config_schema(self):
        """Test conversion to config schema."""
        config = AssistantConfig(
            name="Test Assistant",
            description="Test description",
            ai=AIConfiguration(
                enable_ai_strategy_selection=True,
                enable_content_analysis=False,
                ai_model="gpt-4",
                ai_temperature=0.5,
            ),
            download=DownloadConfiguration(
                max_retries=5,
                timeout_seconds=600,
                download_quality=QualityLevel.HIGH,
            ),
            platforms=PlatformConfiguration(
                youtube_quality="1080p",
                twitter_include_replies=True,
            ),
        )

        schema = config.to_config_schema()

        assert schema["enable_ai_strategy_selection"] is True
        assert schema["enable_content_analysis"] is False
        assert schema["ai_model"] == "gpt-4"
        assert schema["ai_temperature"] == 0.5
        assert schema["max_retries"] == 5
        assert schema["timeout_seconds"] == 600
        assert schema["download_quality"] == "high"
        assert schema["youtube_quality"] == "1080p"
        assert schema["twitter_include_replies"] is True

    def test_update_metadata(self):
        """Test metadata update functionality."""
        config = AssistantConfig(name="Test", description="Test")

        # First, set up initial state
        config.update_metadata(
            total_requests=1,
            successful_requests=1,
            failed_requests=0,
            response_time_seconds=2.0
        )

        assert config.metadata.total_requests == 1
        assert config.metadata.successful_requests == 1
        assert config.metadata.failed_requests == 0
        assert config.metadata.average_response_time_seconds == 2.0
        assert config.metadata.last_used_at is not None

        # Update with more requests
        config.update_metadata(
            total_requests=10,
            successful_requests=9,
            failed_requests=1,
            response_time_seconds=1.0
        )

        # Should be weighted average: (2.0 * 9 + 1.0) / 10 = 1.9
        assert abs(config.metadata.average_response_time_seconds - 1.9) < 0.01


class TestAssistant:
    """Test Assistant model."""

    def test_default_assistant(self):
        """Test default assistant instance."""
        config = AssistantConfig(name="Test", description="Test")
        assistant = Assistant(config=config)

        assert assistant.config == config
        assert assistant.status == AssistantStatus.INITIALIZING
        assert assistant.last_error is None
        assert isinstance(assistant.created_at, datetime)
        assert isinstance(assistant.session_id, str)
        assert len(assistant.session_id) > 0

    def test_assistant_properties(self):
        """Test assistant properties."""
        config = AssistantConfig(name="Test Assistant", description="Test")
        assistant = Assistant(config=config)

        assert assistant.name == "Test Assistant"
        assert assistant.assistant_id == config.assistant_id
        assert assistant.is_healthy is True  # INITIALIZING is healthy
        assert assistant.is_enabled is True  # Enabled and healthy

    def test_assistant_state_management(self):
        """Test assistant state management."""
        config = AssistantConfig(name="Test", description="Test")
        assistant = Assistant(config=config)

        # Test activation
        assistant.activate()
        assert assistant.status == AssistantStatus.ACTIVE
        assert assistant.last_error is None
        assert assistant.is_healthy is True

        # Test deactivation
        assistant.deactivate()
        assert assistant.status == AssistantStatus.INACTIVE
        assert assistant.is_healthy is False
        assert assistant.is_enabled is False

        # Test error state
        assistant.set_error("Test error")
        assert assistant.status == AssistantStatus.ERROR
        assert assistant.last_error == "Test error"
        assert assistant.is_healthy is False

    def test_record_request(self):
        """Test request recording."""
        config = AssistantConfig(name="Test", description="Test")
        assistant = Assistant(config=config)

        # Record successful request
        assistant.record_request(success=True, response_time_seconds=1.5)

        assert assistant.config.metadata.total_requests == 1
        assert assistant.config.metadata.successful_requests == 1
        assert assistant.config.metadata.failed_requests == 0
        assert assistant.config.metadata.average_response_time_seconds == 1.5

        # Record failed request
        assistant.record_request(success=False, response_time_seconds=2.0, error_message="Test error")

        assert assistant.config.metadata.total_requests == 2
        assert assistant.config.metadata.successful_requests == 1
        assert assistant.config.metadata.failed_requests == 1
        assert assistant.status == AssistantStatus.ERROR
        assert assistant.last_error == "Test error"


class TestYAMLOperations:
    """Test YAML serialization and deserialization."""

    def test_yaml_round_trip(self):
        """Test YAML serialization and deserialization round trip."""
        # Create a complex configuration
        config = AssistantConfig(
            name="Test Assistant",
            description="Test description with special characters: éñ中文",
            assistant_id="test-id-123",
            graph_id="custom_workflow",
            tags=["test", "yaml", "unicode"],
            enabled=True,
            ai=AIConfiguration(
                enable_ai_strategy_selection=False,
                ai_model="claude-3",
                ai_temperature=0.7,
            ),
            download=DownloadConfiguration(
                max_retries=5,
                download_quality=QualityLevel.BEST,
            ),
            platforms=PlatformConfiguration(
                youtube_quality="1080p",
                twitter_include_replies=True,
            ),
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Save to YAML
            config.to_yaml_file(temp_path)

            # Load from YAML
            loaded_config = AssistantConfig.from_yaml_file(temp_path)

            # Compare key fields
            assert loaded_config.name == config.name
            assert loaded_config.description == config.description
            assert loaded_config.assistant_id == config.assistant_id
            assert loaded_config.graph_id == config.graph_id
            assert loaded_config.tags == config.tags
            assert loaded_config.enabled == config.enabled

            # Compare nested configurations
            assert loaded_config.ai.enable_ai_strategy_selection == config.ai.enable_ai_strategy_selection
            assert loaded_config.ai.ai_model == config.ai.ai_model
            assert loaded_config.ai.ai_temperature == config.ai.ai_temperature

            assert loaded_config.download.max_retries == config.download.max_retries
            assert loaded_config.download.download_quality == config.download.download_quality

            assert loaded_config.platforms.youtube_quality == config.platforms.youtube_quality
            assert loaded_config.platforms.twitter_include_replies == config.platforms.twitter_include_replies

        finally:
            temp_path.unlink(missing_ok=True)

    def test_yaml_file_operations(self):
        """Test YAML file operations."""
        config = AssistantConfig(name="Test", description="Test")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_config.yaml"

            # Save to file
            config.to_yaml_file(temp_path)
            assert temp_path.exists()

            # Check YAML content
            with open(temp_path, encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)

            assert yaml_data['name'] == "Test"
            assert yaml_data['description'] == "Test"
            assert 'assistant_id' in yaml_data
            assert 'ai' in yaml_data
            assert 'download' in yaml_data

            # Load from file
            loaded_config = AssistantConfig.from_yaml_file(temp_path)
            assert loaded_config.name == config.name
            assert loaded_config.description == config.description

    def test_yaml_file_not_found(self):
        """Test loading from non-existent file."""
        non_existent_path = Path("/non/existent/file.yaml")

        with pytest.raises(FileNotFoundError):
            AssistantConfig.from_yaml_file(non_existent_path)

    def test_yaml_invalid_content(self):
        """Test loading invalid YAML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                AssistantConfig.from_yaml_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_yaml_empty_file(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Configuration file is empty"):
                AssistantConfig.from_yaml_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_yaml_directory_creation(self):
        """Test YAML file saving with directory creation."""
        config = AssistantConfig(name="Test", description="Test")

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "dir" / "config.yaml"

            # Save with directory creation
            config.to_yaml_file(nested_path, create_dirs=True)

            assert nested_path.exists()
            assert nested_path.parent.exists()

            # Verify content
            loaded_config = AssistantConfig.from_yaml_file(nested_path)
            assert loaded_config.name == config.name


class TestHelperFunctions:
    """Test helper functions for assistant management."""

    def test_create_default_assistant_config(self):
        """Test creating default assistant configuration."""
        config = create_default_assistant_config(
            name="Default Assistant",
            description="Default description",
            graph_id="custom_graph"
        )

        assert config.name == "Default Assistant"
        assert config.description == "Default description"
        assert config.graph_id == "custom_graph"
        assert isinstance(config.ai, AIConfiguration)
        assert isinstance(config.download, DownloadConfiguration)

    def test_create_default_assistant_config_with_overrides(self):
        """Test creating default config with overrides."""
        config = create_default_assistant_config(
            name="Test",
            description="Test",
            enabled=False,
            tags=["custom", "test"]
        )

        assert config.enabled is False
        # Tags should be cleaned and deduplicated
        assert sorted(config.tags) == sorted(["custom", "test"])

    def test_load_assistant_configs_empty_directory(self):
        """Test loading from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            configs = load_assistant_configs(Path(temp_dir))
            assert configs == []

    def test_load_assistant_configs_non_existent_directory(self):
        """Test loading from non-existent directory."""
        non_existent_dir = Path("/non/existent/directory")
        configs = load_assistant_configs(non_existent_dir)
        assert configs == []

    def test_load_assistant_configs(self):
        """Test loading multiple assistant configurations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create multiple configs
            config1 = AssistantConfig(name="Assistant 1", description="First assistant")
            config2 = AssistantConfig(name="Assistant 2", description="Second assistant")

            config1.to_yaml_file(config_dir / "config1.yaml")
            config2.to_yaml_file(config_dir / "config2.yaml")

            # Create a non-YAML file that should be ignored
            (config_dir / "not_yaml.txt").write_text("not yaml content")

            # Load configs
            loaded_configs = load_assistant_configs(config_dir)

            assert len(loaded_configs) == 2
            names = {config.name for config in loaded_configs}
            assert names == {"Assistant 1", "Assistant 2"}

    def test_save_assistant_configs(self):
        """Test saving multiple assistant configurations."""
        config1 = AssistantConfig(name="Assistant 1", description="First assistant")
        config2 = AssistantConfig(name="Assistant-2_Test", description="Second assistant")  # Test name sanitization

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            save_assistant_configs([config1, config2], config_dir)

            # Check files were created (names are sanitized)
            files = list(config_dir.glob("*.yaml"))
            assert len(files) == 2

            # Verify content by loading back
            loaded_configs = load_assistant_configs(config_dir)
            assert len(loaded_configs) == 2

            names = {config.name for config in loaded_configs}
            assert names == {"Assistant 1", "Assistant-2_Test"}

    def test_load_assistant_configs_with_invalid_file(self):
        """Test loading configs with one invalid file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create valid config
            valid_config = AssistantConfig(name="Valid", description="Valid config")
            valid_config.to_yaml_file(config_dir / "valid.yaml")

            # Create invalid config file
            with open(config_dir / "invalid.yaml", 'w') as f:
                f.write("name: Missing required description field")

            # Load configs - should get only the valid one
            loaded_configs = load_assistant_configs(config_dir)

            assert len(loaded_configs) == 1
            assert loaded_configs[0].name == "Valid"


class TestAssistantFromConfigFile:
    """Test creating Assistant instances from configuration files."""

    def test_assistant_from_config_file(self):
        """Test creating assistant from configuration file."""
        config = AssistantConfig(name="File Assistant", description="From file")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            config.to_yaml_file(temp_path)

            assistant = Assistant.from_config_file(temp_path)

            assert assistant.config.name == config.name
            assert assistant.config.description == config.description
            assert assistant.status == AssistantStatus.ACTIVE  # Should be activated

        finally:
            temp_path.unlink(missing_ok=True)

    def test_assistant_save_config(self):
        """Test saving assistant configuration."""
        config = AssistantConfig(name="Save Test", description="Save test")
        assistant = Assistant(config=config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            assistant.save_config(temp_path)

            # Verify file was saved
            assert temp_path.exists()

            # Load and verify content
            loaded_config = AssistantConfig.from_yaml_file(temp_path)
            assert loaded_config.name == config.name
            assert loaded_config.description == config.description

        finally:
            temp_path.unlink(missing_ok=True)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_uuid_generation(self):
        """Test UUID generation for assistant IDs."""
        config1 = AssistantConfig(name="Test 1", description="Test")
        config2 = AssistantConfig(name="Test 2", description="Test")

        # Should generate different UUIDs
        assert config1.assistant_id != config2.assistant_id

        # Should be valid UUIDs
        uuid.UUID(config1.assistant_id)  # Should not raise
        uuid.UUID(config2.assistant_id)  # Should not raise

    def test_datetime_serialization(self):
        """Test datetime serialization in YAML."""
        config = AssistantConfig(name="Test", description="Test")

        # Update metadata to have datetime values
        now = datetime.utcnow()
        config.metadata.created_at = now
        config.metadata.updated_at = now
        config.metadata.last_used_at = now

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            config.to_yaml_file(temp_path)

            # Check YAML content has ISO format strings
            with open(temp_path) as f:
                yaml_content = f.read()

            assert now.isoformat() in yaml_content

            # Load and verify datetimes are preserved
            loaded_config = AssistantConfig.from_yaml_file(temp_path)

            # Should be close (within 1 second due to serialization)
            time_diff = abs((loaded_config.metadata.created_at - now).total_seconds())
            assert time_diff < 1.0

        finally:
            temp_path.unlink(missing_ok=True)

    def test_complex_validation_scenarios(self):
        """Test complex validation scenarios."""
        # Test metadata validation with edge case values
        metadata = AssistantMetadata(
            total_requests=1000000,  # Large number
            successful_requests=999999,
            failed_requests=1,
            average_response_time_seconds=0.001,  # Very small response time
        )

        assert metadata.total_requests == 1000000
        assert metadata.average_response_time_seconds == 0.001

        # Test configuration with all extreme values
        config = AssistantConfig(
            name="A",  # Minimum length
            description="B",  # Minimum length
            ai=AIConfiguration(
                ai_temperature=0.0,  # Minimum
                ai_max_tokens=1,  # Minimum
                ai_timeout_seconds=1,  # Minimum
            ),
            download=DownloadConfiguration(
                max_retries=0,  # Minimum
                timeout_seconds=1,  # Minimum
                max_concurrent_downloads=1,  # Minimum
            ),
            workflow=WorkflowConfiguration(
                max_workflow_duration_seconds=1,  # Minimum
                checkpoint_interval_seconds=1,  # Minimum
            ),
        )

        assert config.name == "A"
        assert config.ai.ai_temperature == 0.0
        assert config.download.max_retries == 0
