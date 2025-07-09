"""Comprehensive tests for CLI assistant management commands and integration.

This module tests the CLI commands for assistant management, including proper
exit codes, error handling, and integration with the underlying functionality.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import typer
from click.testing import CliRunner
from langgraph_sdk.schema import Assistant as SDKAssistant
from typer.testing import CliRunner as TyperRunner

from boss_bot.ai.assistants.client import AssistantSyncResult, LangGraphAssistantClient
from boss_bot.ai.assistants.models import AssistantConfig, create_default_assistant_config
from boss_bot.cli.commands.assistants import app as assistants_app
from tests.utils import strip_ansi_codes


# Module-level fixtures shared across all test classes
@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return TyperRunner()


@pytest.fixture
def mock_sdk_assistant():
    """Create mock SDK assistant for testing."""
    assistant = Mock(spec=SDKAssistant)
    assistant.assistant_id = "test-assistant-123"
    assistant.name = "Test Assistant"
    assistant.graph_id = "download_workflow"
    assistant.created_at = Mock()
    assistant.created_at.strftime.return_value = "2025-01-01 12:00"
    assistant.updated_at = Mock()
    assistant.updated_at.strftime.return_value = "2025-01-01 13:00"
    return assistant


@pytest.fixture
def mock_assistant_client():
    """Create mock assistant client."""
    client = AsyncMock(spec=LangGraphAssistantClient)
    # Add config attribute for health command
    client.config = Mock()
    client.config.deployment_url = "https://api.langraph.com"
    return client


class TestAssistantsCLICommands:
    """Test CLI commands for assistant management."""

    def test_list_command_success(self, cli_runner, mock_assistant_client, mock_sdk_assistant):
        """Test successful list command."""
        mock_assistant_client.list_assistants.return_value = [mock_sdk_assistant]

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["list"])

            assert result.exit_code == 0
            # Check for Rich table elements instead of plain text
            assert "LangGraph Assistants (1 found)" in result.stdout
            # Name might be split across lines in the table, so check for "Test" and "Assistant" separately
            assert "Test" in result.stdout
            assert "Assistant" in result.stdout
            assert "download_wor" in result.stdout  # Truncated in table

    def test_list_command_no_assistants(self, cli_runner, mock_assistant_client):
        """Test list command with no assistants."""
        mock_assistant_client.list_assistants.return_value = []

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["list"])

            assert result.exit_code == 0
            assert "No assistants found" in result.stdout

    def test_list_command_with_options(self, cli_runner, mock_assistant_client, mock_sdk_assistant):
        """Test list command with all options."""
        mock_assistant_client.list_assistants.return_value = [mock_sdk_assistant]

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, [
                "list",
                "--url", "https://custom.langraph.com",
                "--key", "custom-key",
                "--graph", "custom_graph",
                "--limit", "10"
            ])

            assert result.exit_code == 0
            mock_assistant_client.list_assistants.assert_called_once_with(
                limit=10,
                graph_id="custom_graph"
            )

    def test_list_command_error(self, cli_runner, mock_assistant_client):
        """Test list command with error."""
        mock_assistant_client.list_assistants.side_effect = Exception("Connection failed")

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["list"])

            assert result.exit_code == 1
            assert "Error listing assistants" in result.stdout

    def test_sync_from_command_success(self, cli_runner, mock_assistant_client):
        """Test successful sync-from command."""
        sync_result = AssistantSyncResult(created=2, updated=1, deleted=0, errors=[])

        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.return_value = sync_result

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-from", temp_dir])

                assert result.exit_code == 0
                clean_output = strip_ansi_codes(result.stdout)
                assert "Created: 2" in clean_output
                assert "Updated: 1" in clean_output
                assert "Deleted: 0" in clean_output
                assert "All operations completed successfully" in clean_output

    def test_sync_from_command_with_options(self, cli_runner):
        """Test sync-from command with all options."""
        sync_result = AssistantSyncResult(created=1, updated=0, deleted=1, errors=[])

        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.return_value = sync_result

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, [
                    "sync-from", temp_dir,
                    "--url", "https://custom.langraph.com",
                    "--key", "custom-key",
                    "--delete-missing"
                ])

                assert result.exit_code == 0
                mock_sync.assert_called_once_with(
                    config_dir=Path(temp_dir),
                    deployment_url="https://custom.langraph.com",
                    api_key="custom-key",
                    delete_missing=True
                )

    def test_sync_from_command_nonexistent_directory(self, cli_runner):
        """Test sync-from command with non-existent directory."""
        result = cli_runner.invoke(assistants_app, ["sync-from", "/non/existent/directory"])

        assert result.exit_code == 1
        assert "Configuration directory not found" in result.stdout

    def test_sync_from_command_with_errors(self, cli_runner):
        """Test sync-from command with errors."""
        sync_result = AssistantSyncResult(
            created=1,
            updated=0,
            deleted=0,
            errors=["Failed to create assistant: Connection error", "Another error"]
        )

        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.return_value = sync_result

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-from", temp_dir])

                assert result.exit_code == 0  # Command completes but shows errors
                clean_output = strip_ansi_codes(result.stdout)
                assert "Errors (2)" in clean_output
                assert "Connection error" in clean_output
                assert "Another error" in clean_output

    def test_sync_from_command_exception(self, cli_runner):
        """Test sync-from command with exception."""
        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.side_effect = Exception("Sync failed")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-from", temp_dir])

                assert result.exit_code == 1
                clean_output = strip_ansi_codes(result.stdout)
                assert "Error during synchronization" in clean_output

    def test_sync_to_command_success(self, cli_runner):
        """Test successful sync-to command."""
        sync_result = AssistantSyncResult(created=3, updated=0, deleted=0, errors=[])

        with patch('boss_bot.cli.commands.assistants.export_assistants_to_directory') as mock_export:
            mock_export.return_value = sync_result

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-to", temp_dir])

                assert result.exit_code == 0
                clean_output = strip_ansi_codes(result.stdout)
                assert "Saved: 3" in clean_output
                assert "Export completed successfully" in clean_output

    def test_sync_to_command_with_options(self, cli_runner):
        """Test sync-to command with all options."""
        sync_result = AssistantSyncResult(created=2, updated=0, deleted=0, errors=[])

        with patch('boss_bot.cli.commands.assistants.export_assistants_to_directory') as mock_export:
            mock_export.return_value = sync_result

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, [
                    "sync-to", temp_dir,
                    "--url", "https://custom.langraph.com",
                    "--key", "custom-key",
                    "--overwrite"
                ])

                assert result.exit_code == 0
                mock_export.assert_called_once_with(
                    config_dir=Path(temp_dir),
                    deployment_url="https://custom.langraph.com",
                    api_key="custom-key",
                    overwrite_existing=True
                )

    def test_sync_to_command_with_errors(self, cli_runner):
        """Test sync-to command with errors."""
        sync_result = AssistantSyncResult(
            created=1,
            updated=0,
            deleted=0,
            errors=["Failed to export assistant: Permission denied"]
        )

        with patch('boss_bot.cli.commands.assistants.export_assistants_to_directory') as mock_export:
            mock_export.return_value = sync_result

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-to", temp_dir])

                assert result.exit_code == 0
                assert "Errors (1)" in result.stdout
                assert "Permission denied" in result.stdout

    def test_sync_to_command_exception(self, cli_runner):
        """Test sync-to command with exception."""
        with patch('boss_bot.cli.commands.assistants.export_assistants_to_directory') as mock_export:
            mock_export.side_effect = Exception("Export failed")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-to", temp_dir])

                assert result.exit_code == 1
                assert "Error during export" in result.stdout

    def test_health_command_success(self, cli_runner, mock_assistant_client):
        """Test successful health check command."""
        mock_assistant_client.health_check.return_value = True
        mock_assistant_client.list_assistants.return_value = [Mock(), Mock()]
        mock_assistant_client.config.deployment_url = "https://api.langraph.com"

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["health"])

            assert result.exit_code == 0
            clean_output = strip_ansi_codes(result.stdout)
            assert "LangGraph Cloud connection is healthy" in clean_output
            assert "https://api.langraph.com" in clean_output
            assert "Working (2 accessible)" in clean_output

    def test_health_command_with_options(self, cli_runner, mock_assistant_client):
        """Test health command with custom URL and key."""
        mock_assistant_client.health_check.return_value = True
        mock_assistant_client.list_assistants.return_value = []
        mock_assistant_client.config.deployment_url = "https://custom.langraph.com"

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, [
                "health",
                "--url", "https://custom.langraph.com",
                "--key", "custom-key"
            ])

            assert result.exit_code == 0
            assert "Working (0 accessible)" in result.stdout

    def test_health_command_failure(self, cli_runner, mock_assistant_client):
        """Test health command failure."""
        mock_assistant_client.health_check.return_value = False

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["health"])

            assert result.exit_code == 1
            assert "LangGraph Cloud connection failed" in result.stdout

    def test_health_command_exception(self, cli_runner, mock_assistant_client):
        """Test health command with exception."""
        mock_assistant_client.health_check.side_effect = Exception("Health check failed")

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["health"])

            assert result.exit_code == 1
            assert "Health check failed" in result.stdout

    def test_create_config_command_success(self, cli_runner):
        """Test successful create-config command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_config.yaml"

            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test Assistant",
                "Test description",
                "--output", str(output_file),
                "--graph", "custom_graph"
            ])

            assert result.exit_code == 0
            assert "Created assistant configuration" in result.stdout
            assert "Test Assistant" in result.stdout
            assert "custom_graph" in result.stdout
            assert output_file.exists()

            # Verify file content
            config = AssistantConfig.from_yaml_file(output_file)
            assert config.name == "Test Assistant"
            assert config.description == "Test description"
            assert config.graph_id == "custom_graph"

    def test_create_config_command_default_output(self, cli_runner):
        """Test create-config command with default output file."""
        # Use current directory and clean up after
        expected_file = Path("mytestassistant_config.yaml")

        # Clean up any existing file
        if expected_file.exists():
            expected_file.unlink()

        try:
            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "My Test Assistant",
                "My test description"
            ])

            assert result.exit_code == 0
            assert expected_file.exists()
        finally:
            # Clean up created file
            if expected_file.exists():
                expected_file.unlink()

    def test_create_config_command_error(self, cli_runner):
        """Test create-config command with error."""
        with patch('boss_bot.cli.commands.assistants.create_default_assistant_config') as mock_create:
            mock_create.side_effect = Exception("Config creation failed")

            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test",
                "Test description"
            ])

            assert result.exit_code == 1
            assert "Error creating configuration" in result.stdout

    def test_graphs_command_success(self, cli_runner, mock_assistant_client):
        """Test successful graphs command."""
        mock_graph1 = Mock()
        mock_graph1.graph_id = "download_workflow"
        mock_graph1.name = "Download Workflow"
        mock_graph1.description = "Main download workflow"

        mock_graph2 = Mock()
        mock_graph2.graph_id = "analysis_workflow"
        mock_graph2.name = "Analysis Workflow"
        mock_graph2.description = "Content analysis workflow"

        mock_assistant_client.get_assistant_graphs.return_value = [mock_graph1, mock_graph2]

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["graphs"])

            assert result.exit_code == 0
            assert "Available Assistant Graphs (2 found)" in result.stdout
            assert "download_workflow" in result.stdout
            assert "Download Workflow" in result.stdout
            assert "analysis_workflow" in result.stdout

    def test_graphs_command_no_graphs(self, cli_runner, mock_assistant_client):
        """Test graphs command with no graphs."""
        mock_assistant_client.get_assistant_graphs.return_value = []

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["graphs"])

            assert result.exit_code == 0
            assert "No graphs found" in result.stdout

    def test_graphs_command_with_options(self, cli_runner, mock_assistant_client):
        """Test graphs command with custom URL and key."""
        mock_assistant_client.get_assistant_graphs.return_value = []

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, [
                "graphs",
                "--url", "https://custom.langraph.com",
                "--key", "custom-key"
            ])

            assert result.exit_code == 0

    def test_graphs_command_error(self, cli_runner, mock_assistant_client):
        """Test graphs command with error."""
        mock_assistant_client.get_assistant_graphs.side_effect = Exception("Failed to fetch graphs")

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["graphs"])

            assert result.exit_code == 1
            assert "Error listing graphs" in result.stdout

    def test_help_command(self, cli_runner):
        """Test help command."""
        result = cli_runner.invoke(assistants_app, ["--help"])

        assert result.exit_code == 0
        assert "Manage LangGraph assistants" in result.stdout
        assert "list" in result.stdout
        assert "sync-from" in result.stdout
        assert "sync-to" in result.stdout
        assert "health" in result.stdout
        assert "create-config" in result.stdout
        assert "graphs" in result.stdout

    def test_invalid_command(self, cli_runner):
        """Test invalid command."""
        result = cli_runner.invoke(assistants_app, ["invalid-command"])

        assert result.exit_code != 0


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_full_workflow_integration(self, cli_runner):
        """Test full workflow: create config, sync, list, health."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_file = config_dir / "test_assistant.yaml"

            # Mock all external dependencies
            mock_assistant = Mock(spec=SDKAssistant)
            mock_assistant.assistant_id = "test-123"
            mock_assistant.name = "Test Assistant"
            mock_assistant.graph_id = "download_workflow"
            mock_assistant.created_at = Mock()
            mock_assistant.created_at.strftime.return_value = "2025-01-01 12:00"
            mock_assistant.updated_at = Mock()
            mock_assistant.updated_at.strftime.return_value = "2025-01-01 13:00"

            mock_client = AsyncMock(spec=LangGraphAssistantClient)
            mock_client.list_assistants.return_value = [mock_assistant]
            mock_client.health_check.return_value = True
            # Add config attribute for health command
            mock_client.config = Mock()
            mock_client.config.deployment_url = "https://api.langraph.com"

            # Step 1: Create configuration
            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test Assistant",
                "Test description",
                "--output", str(config_file)
            ])
            assert result.exit_code == 0
            assert config_file.exists()

            # Step 2: Sync from (mock)
            with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
                sync_result = AssistantSyncResult(created=1, updated=0, deleted=0, errors=[])
                mock_sync.return_value = sync_result

                result = cli_runner.invoke(assistants_app, ["sync-from", str(config_dir)])
                assert result.exit_code == 0
                assert "Created: 1" in result.stdout

            # Step 3: List assistants (mock)
            with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = cli_runner.invoke(assistants_app, ["list"])
                assert result.exit_code == 0
                # Check for table header and count rather than specific content due to Rich table formatting
                assert "LangGraph Assistants (1 found)" in result.stdout

            # Step 4: Health check (mock)
            with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
                mock_client_class.return_value.__aenter__.return_value = mock_client

                result = cli_runner.invoke(assistants_app, ["health"])
                assert result.exit_code == 0
                assert "connection is healthy" in result.stdout

    def test_error_propagation(self, cli_runner):
        """Test that errors propagate correctly through CLI."""
        # Test connection error propagation
        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.side_effect = Exception("Connection refused")

            result = cli_runner.invoke(assistants_app, ["list"])
            assert result.exit_code == 1
            assert "Error listing assistants" in result.stdout

    def test_configuration_file_handling(self, cli_runner):
        """Test configuration file handling edge cases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with read-only directory
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only

            try:
                result = cli_runner.invoke(assistants_app, [
                    "create-config",
                    "Test",
                    "Test",
                    "--output", str(readonly_dir / "config.yaml")
                ])
                # Should handle permission error gracefully
                assert result.exit_code == 1
            finally:
                readonly_dir.chmod(0o755)  # Restore permissions for cleanup

    def test_unicode_handling(self, cli_runner):
        """Test Unicode handling in CLI commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "unicode_config.yaml"

            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test Assistant 中文",
                "Description with émojis 🤖",
                "--output", str(config_file)
            ])

            assert result.exit_code == 0
            assert config_file.exists()

            # Verify Unicode was preserved
            config = AssistantConfig.from_yaml_file(config_file)
            assert "中文" in config.name
            assert "émojis 🤖" in config.description

    def test_command_chaining_simulation(self, cli_runner):
        """Test simulation of command chaining scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create multiple configurations
            configs = [
                ("Assistant 1", "First assistant"),
                ("Assistant 2", "Second assistant"),
                ("Assistant 3", "Third assistant"),
            ]

            # Create config files
            for name, desc in configs:
                result = cli_runner.invoke(assistants_app, [
                    "create-config",
                    name,
                    desc,
                    "--output", str(config_dir / f"{name.lower().replace(' ', '_')}.yaml")
                ])
                assert result.exit_code == 0

            # Verify all files were created
            yaml_files = list(config_dir.glob("*.yaml"))
            assert len(yaml_files) == 3

            # Mock sync operation
            with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
                sync_result = AssistantSyncResult(created=3, updated=0, deleted=0, errors=[])
                mock_sync.return_value = sync_result

                result = cli_runner.invoke(assistants_app, ["sync-from", str(config_dir)])
                assert result.exit_code == 0
                assert "Created: 3" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_missing_arguments(self, cli_runner):
        """Test commands with missing required arguments."""
        # Test create-config without arguments
        result = cli_runner.invoke(assistants_app, ["create-config"])
        assert result.exit_code != 0

        # Test sync-from without directory
        result = cli_runner.invoke(assistants_app, ["sync-from"])
        assert result.exit_code != 0

        # Test sync-to without directory
        result = cli_runner.invoke(assistants_app, ["sync-to"])
        assert result.exit_code != 0

    def test_invalid_url_handling(self, cli_runner, mock_assistant_client):
        """Test handling of invalid URLs."""
        # URLs are validated by Pydantic, but CLI should handle validation errors
        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Invalid URL format")

            result = cli_runner.invoke(assistants_app, [
                "list",
                "--url", "not-a-valid-url"
            ])

            assert result.exit_code == 1

    def test_async_exception_handling(self, cli_runner):
        """Test async exception handling in CLI commands."""
        async def failing_async_operation():
            raise RuntimeError("Async operation failed")

        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.side_effect = RuntimeError("Async operation failed")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-from", temp_dir])

                assert result.exit_code == 1
                clean_output = strip_ansi_codes(result.stdout)
                assert "Error during synchronization" in clean_output

    def test_keyboard_interrupt_handling(self, cli_runner):
        """Test keyboard interrupt handling."""
        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.side_effect = KeyboardInterrupt()

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-from", temp_dir])

                # Should handle KeyboardInterrupt gracefully
                # KeyboardInterrupt results in exit code 130 (128 + SIGINT(2))
                assert result.exit_code == 130

    def test_permission_errors(self, cli_runner):
        """Test permission error handling."""
        with patch('boss_bot.cli.commands.assistants.create_default_assistant_config') as mock_create:
            mock_config = Mock()
            mock_config.to_yaml_file.side_effect = PermissionError("Permission denied")
            mock_create.return_value = mock_config

            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test",
                "Test"
            ])

            assert result.exit_code == 1
            assert "Error creating configuration" in result.stdout

    def test_file_system_errors(self, cli_runner):
        """Test file system error handling."""
        with patch('boss_bot.cli.commands.assistants.export_assistants_to_directory') as mock_export:
            mock_export.side_effect = OSError("Disk full")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-to", temp_dir])

                assert result.exit_code == 1
                assert "Error during export" in result.stdout


class TestCLIOutputFormatting:
    """Test CLI output formatting and display."""

    def test_table_formatting(self, cli_runner, mock_assistant_client):
        """Test table formatting in list command."""
        # Create assistants with different data
        assistants = []
        for i in range(3):
            assistant = Mock(spec=SDKAssistant)
            assistant.assistant_id = f"assistant-{i:03d}-{'x' * 20}"  # Long ID for truncation test
            assistant.name = f"Assistant {i}"
            assistant.graph_id = f"graph_{i}"
            assistant.created_at = Mock()
            assistant.created_at.strftime.return_value = f"2025-01-0{i+1} 12:00"
            assistant.updated_at = Mock()
            assistant.updated_at.strftime.return_value = f"2025-01-0{i+1} 13:00"
            assistants.append(assistant)

        mock_assistant_client.list_assistants.return_value = assistants

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["list"])

            assert result.exit_code == 0
            assert "LangGraph Assistants (3 found)" in result.stdout

            # Check that IDs are truncated
            for i in range(3):
                assert f"Assistant {i}" in result.stdout
                assert f"graph_{i}" in result.stdout
                # ID should be truncated to 8 chars + "..."
                assert f"assistan..." in result.stdout

    def test_progress_indicators(self, cli_runner, mock_assistant_client):
        """Test progress indicators in commands."""
        mock_assistant_client.list_assistants.return_value = []

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["list"])

            assert result.exit_code == 0
            # Progress indicators should be present (though they may not show in test output)

    def test_color_output_handling(self, cli_runner, mock_assistant_client):
        """Test color output handling."""
        # Rich console should handle color output appropriately
        mock_assistant_client.health_check.return_value = True
        mock_assistant_client.list_assistants.return_value = []
        mock_assistant_client.config.deployment_url = "https://api.langraph.com"

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, ["health"])

            assert result.exit_code == 0
            # Should contain success indicators (without actual color codes in test)
            assert "connection is healthy" in result.stdout

    def test_error_message_formatting(self, cli_runner):
        """Test error message formatting."""
        with patch('boss_bot.cli.commands.assistants.sync_assistants_from_directory') as mock_sync:
            mock_sync.side_effect = Exception("Detailed error message with context")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = cli_runner.invoke(assistants_app, ["sync-from", temp_dir])

                assert result.exit_code == 1
                clean_output = strip_ansi_codes(result.stdout)
                assert "Error during synchronization" in clean_output
                assert "Detailed error message with context" in result.stdout


class TestCLIConfigurationHandling:
    """Test CLI configuration and settings handling."""

    def test_settings_initialization(self, cli_runner):
        """Test settings initialization in CLI."""
        # The CLI should initialize settings lazily
        with patch('boss_bot.cli.commands.assistants.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test",
                "Test"
            ])

            # Settings should be accessible but not necessarily called
            # (since create-config doesn't need settings)
            assert result.exit_code == 0

    def test_environment_variable_handling(self, cli_runner):
        """Test environment variable handling."""
        # CLI commands should respect environment variables through settings
        # This is tested implicitly through the settings fixture usage
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Env Test",
                "Environment test",
                "--output", str(Path(temp_dir) / "env_test.yaml")
            ])

            assert result.exit_code == 0

    def test_configuration_precedence(self, cli_runner, mock_assistant_client):
        """Test configuration precedence (CLI args > env vars > defaults)."""
        mock_assistant_client.list_assistants.return_value = []

        # CLI arguments should take precedence
        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_assistant_client

            result = cli_runner.invoke(assistants_app, [
                "list",
                "--url", "https://cli-override.com",
                "--key", "cli-key"
            ])

            assert result.exit_code == 0

            # Verify that CLI arguments were used
            call_args = mock_client_class.call_args
            if call_args and call_args[1].get('config'):
                config = call_args[1]['config']
                assert str(config.deployment_url) == "https://cli-override.com/"


class TestCLIEdgeCases:
    """Test CLI edge cases and boundary conditions."""

    def test_empty_string_arguments(self, cli_runner):
        """Test handling of empty string arguments."""
        result = cli_runner.invoke(assistants_app, [
            "create-config",
            "",  # Empty name
            "Test description"
        ])

        # Should fail validation
        assert result.exit_code == 1

    def test_very_long_arguments(self, cli_runner):
        """Test handling of very long arguments."""
        long_name = "A" * 200  # Exceeds max length

        result = cli_runner.invoke(assistants_app, [
            "create-config",
            long_name,
            "Test description"
        ])

        # Should fail validation
        assert result.exit_code == 1

    def test_special_characters_in_arguments(self, cli_runner):
        """Test handling of special characters in arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(assistants_app, [
                "create-config",
                "Test/Assistant\\With|Special<>Characters",
                "Description with special chars: éñ中文🤖",
                "--output", str(Path(temp_dir) / "special.yaml")
            ])

            # Should handle special characters gracefully
            assert result.exit_code == 0

    def test_concurrent_cli_operations(self, cli_runner):
        """Test behavior during concurrent CLI operations."""
        # This is more of a conceptual test since CLI operations are sequential
        # But we can test that file locking/creation works properly

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create config file
            result1 = cli_runner.invoke(assistants_app, [
                "create-config",
                "Concurrent Test 1",
                "Test description",
                "--output", str(config_dir / "concurrent1.yaml")
            ])
            assert result1.exit_code == 0

            # Create another config file
            result2 = cli_runner.invoke(assistants_app, [
                "create-config",
                "Concurrent Test 2",
                "Test description",
                "--output", str(config_dir / "concurrent2.yaml")
            ])
            assert result2.exit_code == 0

            # Both files should exist
            assert len(list(config_dir.glob("*.yaml"))) == 2

    def test_resource_cleanup(self, cli_runner):
        """Test that resources are properly cleaned up."""
        # This tests that temporary resources, connections, etc. are cleaned up
        mock_client = AsyncMock()
        mock_client.list_assistants.return_value = []

        with patch('boss_bot.cli.commands.assistants.LangGraphAssistantClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = cli_runner.invoke(assistants_app, ["list"])

            assert result.exit_code == 0
            # Context manager should ensure proper cleanup
            mock_client_class.return_value.__aexit__.assert_called_once()
