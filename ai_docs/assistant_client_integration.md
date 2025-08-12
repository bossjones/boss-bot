# LangGraph Assistant Client Integration

This document describes the comprehensive LangGraph SDK integration for assistant management in Boss-Bot.

## Overview

The `LangGraphAssistantClient` provides a complete interface for managing LangGraph assistants through the LangGraph Cloud API. It includes CRUD operations, configuration synchronization, deployment management, and CLI commands.

## Features

### 🚀 Core Capabilities
- **Full CRUD Operations**: Create, read, update, and delete assistants
- **Configuration Synchronization**: Bidirectional sync between local YAML and cloud
- **Health Checks**: Connection testing and monitoring
- **Error Handling**: Robust error handling with retry logic
- **Environment Integration**: Seamless integration with Boss-Bot settings

### 🔧 Configuration Management
- **YAML-based Configuration**: Human-readable assistant configurations
- **Validation**: Comprehensive validation using Pydantic models
- **Version Control**: Track configuration versions and changes
- **Metadata Management**: Rich metadata tracking for assistants

### 📦 Deployment Support
- **Local Development**: Works with local LangGraph instances
- **Cloud Deployment**: Full support for LangGraph Cloud
- **Environment Variables**: Configurable via environment settings
- **Authentication**: API key-based authentication support

## Architecture

### File Structure
```
src/boss_bot/ai/assistants/
├── __init__.py          # Public API exports
├── client.py            # LangGraph SDK client implementation
└── models.py            # Pydantic models for configuration

src/boss_bot/cli/commands/
└── assistants.py        # CLI commands for assistant management

src/boss_bot/core/
└── env.py              # Environment settings (updated)

examples/
└── assistant_client_example.py  # Usage examples
```

### Key Components

#### 1. LangGraphAssistantClient
Main client class providing:
- Async context manager support
- Connection management
- Full CRUD operations
- Synchronization methods
- Health monitoring

#### 2. Configuration Models
- `AssistantConfig`: Complete assistant configuration
- `LangGraphClientConfig`: Client connection settings
- `AssistantSyncResult`: Synchronization results
- Various supporting enums and validators

#### 3. CLI Commands
- `list`: List assistants from cloud
- `sync-from`: Upload local configs to cloud
- `sync-to`: Download cloud configs locally
- `health`: Check connection health
- `create-config`: Generate default configurations
- `graphs`: List available workflow graphs

## Installation & Setup

### Environment Variables

Add to your `.env` file:
```bash
# LangGraph Cloud Configuration
LANGGRAPH_DEPLOYMENT_URL=http://localhost:8000
LANGGRAPH_API_KEY=your_api_key_here

# LangChain Settings (fallback)
LANGCHAIN_ENDPOINT=http://localhost:8000
LANGCHAIN_API_KEY=your_langchain_key
LANGCHAIN_TRACING_V2=true
```

### Dependencies

The client uses the existing `langgraph-sdk` dependency:
```toml
langgraph-sdk>=0.1.70
```

## Usage Examples

### 1. Basic Client Usage

```python
from boss_bot.ai.assistants import LangGraphAssistantClient

# Using async context manager
async with LangGraphAssistantClient() as client:
    # List assistants
    assistants = await client.list_assistants()

    # Create new assistant
    config = create_default_assistant_config(
        name="My Assistant",
        description="Custom assistant for downloads"
    )
    assistant = await client.create_assistant(config)

    # Update assistant
    config.ai.ai_temperature = 0.5
    updated = await client.update_assistant(assistant.assistant_id, config)
```

### 2. Configuration Management

```python
from boss_bot.ai.assistants.models import AssistantConfig
from pathlib import Path

# Load from YAML
config = AssistantConfig.from_yaml_file(Path("assistant.yaml"))

# Save to YAML
config.to_yaml_file(Path("updated_assistant.yaml"))

# Create default configuration
config = create_default_assistant_config(
    name="Content Analyzer",
    description="AI-powered content analysis",
    graph_id="content_analysis_workflow"
)
```

### 3. Synchronization

```python
from boss_bot.ai.assistants import sync_assistants_from_directory

# Sync local configs to cloud
result = await sync_assistants_from_directory(
    config_dir=Path("./assistants"),
    deployment_url="https://your-deployment.langgraph.dev",
    api_key="your_api_key",
    delete_missing=False
)

print(f"Created: {result.created}, Updated: {result.updated}")
```

### 4. CLI Commands

```bash
# List assistants
uv run python -m boss_bot.cli assistants list

# Create configuration
uv run python -m boss_bot.cli assistants create-config "My Assistant" "Description"

# Sync from local to cloud
uv run python -m boss_bot.cli assistants sync-from ./configs --url https://api.langgraph.dev

# Export from cloud to local
uv run python -m boss_bot.cli assistants sync-to ./exports --overwrite

# Health check
uv run python -m boss_bot.cli assistants health --url https://api.langgraph.dev
```

## Configuration Schema

### Assistant Configuration YAML

```yaml
name: "Download Assistant"
description: "AI-powered download strategy selector"
assistant_id: "unique-uuid-here"
graph_id: "download_workflow"
enabled: true
tags:
  - "downloads"
  - "ai-enhanced"

ai:
  enable_ai_strategy_selection: true
  enable_content_analysis: true
  ai_model: "gpt-4"
  ai_temperature: 0.3
  ai_max_tokens: 1000
  ai_timeout_seconds: 30

download:
  max_retries: 3
  timeout_seconds: 300
  download_quality: "good"
  max_concurrent_downloads: 3
  enable_fallback: true

platforms:
  youtube_quality: "720p"
  twitter_include_replies: false
  instagram_include_stories: true
  reddit_include_comments: false
  generic_user_agent: "Mozilla/5.0 (compatible; Boss-Bot/1.0)"

workflow:
  enable_parallel_processing: true
  max_workflow_duration_seconds: 600
  enable_detailed_logging: false
  checkpoint_interval_seconds: 30

metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
  version: "1.0.0"
  total_requests: 0
  successful_requests: 0
  failed_requests: 0
  average_response_time_seconds: 0.0
```

## Error Handling

The client includes comprehensive error handling:

```python
try:
    async with LangGraphAssistantClient() as client:
        assistants = await client.list_assistants()
except ConnectionError as e:
    print(f"Connection failed: {e}")
except ValidationError as e:
    print(f"Configuration invalid: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

### 1. Configuration Management
- Use version control for YAML configurations
- Validate configurations before deployment
- Use meaningful names and descriptions
- Include relevant tags for organization

### 2. Deployment
- Test with local LangGraph instances first
- Use environment variables for deployment URLs
- Implement proper error handling
- Monitor assistant performance metrics

### 3. Synchronization
- Regular backups via `sync-to`
- Careful use of `delete_missing` flag
- Review sync results before proceeding
- Use staging environments for testing

### 4. Security
- Secure API keys in environment variables
- Use HTTPS for production deployments
- Limit API key permissions
- Regular key rotation

## Integration with Boss-Bot

The assistant client integrates seamlessly with Boss-Bot's existing architecture:

### 1. Settings Integration
- Uses `BossSettings` for configuration
- Respects existing environment variables
- Inherits logging and monitoring setup

### 2. AI Workflow Integration
- Compatible with existing AI agents
- Supports download workflow graphs
- Maintains configuration consistency

### 3. CLI Integration
- Follows Boss-Bot CLI patterns
- Uses Typer for command structure
- Rich console output formatting

## Testing

Run the example script to test functionality:
```bash
uv run python examples/assistant_client_example.py
```

For comprehensive testing:
```bash
# Run assistant-related tests
uv run python -m pytest tests/ -k assistant

# Check code formatting
uv run ruff check src/boss_bot/ai/assistants/
uv run ruff format src/boss_bot/ai/assistants/
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify LangGraph Cloud is running
   - Check deployment URL configuration
   - Validate API key and permissions

2. **Import Errors**
   - Ensure langgraph-sdk is installed
   - Check Python path configuration
   - Verify all dependencies are available

3. **Configuration Errors**
   - Validate YAML syntax
   - Check required fields are present
   - Ensure types match schema

4. **Sync Issues**
   - Verify directory paths exist
   - Check file permissions
   - Review error messages in sync results

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
uv run python -m boss_bot.cli assistants health
```

## Future Enhancements

Planned improvements include:
- Batch operations for multiple assistants
- Advanced filtering and search capabilities
- Real-time monitoring and alerting
- Integration with CI/CD pipelines
- Enhanced validation and testing tools

## API Reference

### LangGraphAssistantClient

#### Methods
- `connect()`: Establish connection
- `disconnect()`: Close connection
- `health_check(force=False)`: Test connectivity
- `create_assistant(config)`: Create new assistant
- `get_assistant(assistant_id)`: Retrieve assistant
- `list_assistants(limit, offset, graph_id)`: List assistants
- `update_assistant(assistant_id, config)`: Update assistant
- `delete_assistant(assistant_id)`: Delete assistant
- `sync_from_yaml(config_dir, delete_missing)`: Upload configs
- `sync_to_yaml(config_dir, overwrite_existing)`: Download configs

#### Helper Functions
- `create_assistant_client(settings, config)`: Create connected client
- `sync_assistants_from_directory(...)`: Directory sync helper
- `export_assistants_to_directory(...)`: Export helper

This integration provides a complete, production-ready solution for managing LangGraph assistants within the Boss-Bot ecosystem.
