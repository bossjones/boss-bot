# LangGraph Assistant Management Guide

## Overview

Boss-Bot includes a comprehensive assistant management system for LangGraph Cloud, enabling you to create, deploy, and manage AI assistants directly from the command line. This system provides seamless integration between local YAML configurations and LangGraph Cloud deployments.

## Prerequisites

### Environment Configuration

Before using assistant management features, configure these environment variables in your `.env` file:

```bash
# Required: LangGraph Cloud deployment URL
LANGGRAPH_DEPLOYMENT_URL=https://your-deployment.langraph.app

# Required: API key for authentication
LANGGRAPH_API_KEY=your-api-key-here

# Optional: Default graph name for operations
LANGGRAPH_DEFAULT_GRAPH=download_workflow
```

### Installation

Ensure Boss-Bot is installed with development dependencies:

```bash
# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

## Command Reference

### `boss-bot assistants list`

Display all assistants from your LangGraph Cloud deployment.

**Syntax:**
```bash
boss-bot assistants list [OPTIONS]
```

**Options:**
- `--limit INTEGER`: Maximum number of assistants to display (default: 100)
- `--graph TEXT`: Filter by graph name
- `--format [table|json]`: Output format (default: table)

**Examples:**
```bash
# List all assistants in a rich table
boss-bot assistants list

# Filter by graph name
boss-bot assistants list --graph download_workflow

# JSON output for scripting
boss-bot assistants list --format json --limit 10
```

### `boss-bot assistants health`

Check connectivity and authentication with LangGraph Cloud.

**Syntax:**
```bash
boss-bot assistants health
```

**Output:**
- ✅ Success: "LangGraph Cloud connection is healthy"
- ❌ Failure: Detailed error message with troubleshooting steps

### `boss-bot assistants create-config`

Generate a new assistant configuration YAML file.

**Syntax:**
```bash
boss-bot assistants create-config [OPTIONS]
```

**Options:**
- `--name TEXT`: Assistant name (required)
- `--graph TEXT`: Graph name (default: from environment)
- `--output PATH`: Output file path (default: `assistants/{name}.yaml`)
- `--version TEXT`: Assistant version (default: "1.0.0")

**Examples:**
```bash
# Create a basic configuration
boss-bot assistants create-config --name content-analyzer

# Specify custom output path
boss-bot assistants create-config --name my-assistant --output configs/my-assistant.yaml

# Use specific graph
boss-bot assistants create-config --name downloader --graph download_workflow
```

### `boss-bot assistants sync-from`

Download assistant configurations from LangGraph Cloud to local YAML files.

**Syntax:**
```bash
boss-bot assistants sync-from [OPTIONS]
```

**Options:**
- `--output-dir PATH`: Directory for YAML files (default: `assistants/`)
- `--graph TEXT`: Filter by graph name
- `--overwrite`: Overwrite existing files

**Examples:**
```bash
# Sync all assistants
boss-bot assistants sync-from

# Sync to custom directory
boss-bot assistants sync-from --output-dir configs/cloud

# Sync specific graph only
boss-bot assistants sync-from --graph download_workflow --overwrite
```

### `boss-bot assistants sync-to`

Deploy local YAML configurations to LangGraph Cloud.

**Syntax:**
```bash
boss-bot assistants sync-to CONFIG_PATH [OPTIONS]
```

**Arguments:**
- `CONFIG_PATH`: Path to YAML file or directory

**Options:**
- `--dry-run`: Preview changes without deploying
- `--update`: Update existing assistants
- `--force`: Skip confirmation prompts

**Examples:**
```bash
# Deploy single assistant
boss-bot assistants sync-to assistants/content-analyzer.yaml

# Deploy all assistants in directory
boss-bot assistants sync-to assistants/

# Preview changes
boss-bot assistants sync-to assistants/ --dry-run

# Update existing assistant
boss-bot assistants sync-to assistants/my-assistant.yaml --update
```

### `boss-bot assistants graphs`

List available graphs from your LangGraph deployment.

**Syntax:**
```bash
boss-bot assistants graphs [OPTIONS]
```

**Options:**
- `--format [table|json|list]`: Output format (default: table)

**Examples:**
```bash
# Show graphs in table format
boss-bot assistants graphs

# Simple list for scripting
boss-bot assistants graphs --format list
```

## YAML Configuration Schema

Assistant configurations use a structured YAML format:

```yaml
# Metadata section (auto-generated)
metadata:
  created_at: "2024-01-20T10:30:00Z"
  updated_at: "2024-01-20T10:30:00Z"
  version: "1.0.0"
  source: "boss-bot-cli"

# Assistant configuration
assistant:
  name: "content-analyzer"
  assistant_id: "asst_abc123"  # Generated after deployment
  graph_id: "download_workflow"
  config:
    # Graph-specific configuration
    configurable:
      model_name: "gpt-4"
      temperature: 0.7
      max_retries: 3
    # System prompts
    system_message: "You are a content analysis assistant..."
    # Tool configurations
    tools:
      - name: "analyze_content"
        description: "Analyze media content"
    # Memory settings
    checkpointer:
      type: "memory"

  # Optional metadata
  metadata:
    description: "Analyzes social media content"
    tags: ["ai", "content", "analysis"]
    owner: "team-ai"
```

## Common Workflows

### Creating and Deploying a New Assistant

1. **Generate configuration:**
   ```bash
   boss-bot assistants create-config --name my-assistant
   ```

2. **Edit the generated YAML:**
   ```bash
   # Edit assistants/my-assistant.yaml with your settings
   ```

3. **Deploy to LangGraph Cloud:**
   ```bash
   boss-bot assistants sync-to assistants/my-assistant.yaml
   ```

4. **Verify deployment:**
   ```bash
   boss-bot assistants list --graph download_workflow
   ```

### Backing Up Cloud Assistants

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Sync all assistants
boss-bot assistants sync-from --output-dir backups/$(date +%Y%m%d)
```

### Updating Multiple Assistants

```bash
# Update all configurations in a directory
boss-bot assistants sync-to assistants/ --update --dry-run

# If changes look good, apply them
boss-bot assistants sync-to assistants/ --update --force
```

## Integration with Discord Bot

The assistant management system integrates with Boss-Bot's AI features:

1. **AI-Enhanced Commands**: Deployed assistants power Discord commands like `$smart-analyze` and `$smart-download`

2. **Multi-Agent Workflows**: Assistants work together in LangGraph workflows for complex tasks

3. **Dynamic Loading**: The bot automatically uses the latest deployed assistants

## Troubleshooting

### Connection Issues

**Error: "Failed to connect to LangGraph Cloud"**
- Verify `LANGGRAPH_DEPLOYMENT_URL` is correct
- Check network connectivity
- Ensure URL includes `https://` prefix

**Error: "Authentication failed"**
- Verify `LANGGRAPH_API_KEY` is valid
- Check API key permissions
- Regenerate key if expired

### Configuration Issues

**Error: "Invalid YAML format"**
- Validate YAML syntax using online tools
- Check indentation (use spaces, not tabs)
- Ensure all required fields are present

**Error: "Graph not found"**
- Run `boss-bot assistants graphs` to list available graphs
- Verify graph name spelling
- Check deployment configuration

### Deployment Issues

**Error: "Assistant already exists"**
- Use `--update` flag to update existing assistants
- Or delete the assistant from LangGraph Cloud first

**Error: "Configuration validation failed"**
- Review the error message for specific fields
- Check the schema documentation above
- Ensure all referenced tools/models are available

## Best Practices

1. **Version Control**: Keep YAML configurations in git
   ```bash
   git add assistants/
   git commit -m "Add assistant configurations"
   ```

2. **Naming Conventions**: Use descriptive, lowercase names with hyphens
   - Good: `content-analyzer`, `download-coordinator`
   - Avoid: `Assistant1`, `MyAssistant`

3. **Testing**: Always use `--dry-run` before bulk operations

4. **Documentation**: Add descriptions and metadata to configurations

5. **Backup**: Regularly sync from cloud to local files

## Advanced Usage

### Scripting and Automation

```bash
#!/bin/bash
# Deploy all assistants and capture results
for config in assistants/*.yaml; do
  echo "Deploying $(basename $config)..."
  boss-bot assistants sync-to "$config" --force
done
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Deploy Assistants
  env:
    LANGGRAPH_API_KEY: ${{ secrets.LANGGRAPH_API_KEY }}
    LANGGRAPH_DEPLOYMENT_URL: ${{ secrets.LANGGRAPH_URL }}
  run: |
    boss-bot assistants health
    boss-bot assistants sync-to assistants/ --force
```

### Monitoring Deployments

```bash
# Check deployment status
boss-bot assistants list --format json | jq '.[] | {name, version, updated_at}'
```

## Related Documentation

- [CLI Reference](cli.md) - Complete CLI command documentation
- [AI Integration](ai.md) - Overview of AI features
- [Environment Configuration](environment.md) - Full environment setup guide
