# MCP Docs Lookup

Fetch MCP documentation from the official website and validate it against local FastMCP documentation.

## Usage

```
/mcp-docs-lookup [topic] [--validate-local]
```

## Parameters

- `topic` (optional): Specific topic to lookup. If not provided, shows available topics.
- `--validate-local` (optional): Also validate against local FastMCP docs in `docs/fastmcp/`

## Available Topics

- `roadmap` - Development roadmap
- `architecture` - Core architecture concepts
- `architecture-python` - Python-specific architecture
- `prompts` - Prompt concepts
- `resources` - Resource concepts
- `roots` - Root concepts
- `sampling` - Sampling concepts
- `tools` - Tool concepts
- `transports` - Transport concepts
- `debugging` - Debugging tools
- `examples` - Examples
- `quickstart` - Server quickstart
- `building-with-llms` - Building MCP with LLMs tutorial

## Implementation

The command will:

1. Map the topic to the appropriate MCP documentation URL
2. Fetch the content using WebFetch
3. If `--validate-local` is specified, compare with relevant local FastMCP documentation
4. Return a summary of findings and any discrepancies

## URL Mapping

```python
MCP_DOC_URLS = {
    "roadmap": "https://modelcontextprotocol.io/development/roadmap",
    "architecture": "https://modelcontextprotocol.io/docs/concepts/architecture",
    "architecture-python": "https://modelcontextprotocol.io/docs/concepts/architecture#python",
    "prompts": "https://modelcontextprotocol.io/docs/concepts/prompts",
    "resources": "https://modelcontextprotocol.io/docs/concepts/resources",
    "roots": "https://modelcontextprotocol.io/docs/concepts/roots",
    "sampling": "https://modelcontextprotocol.io/docs/concepts/sampling",
    "tools": "https://modelcontextprotocol.io/docs/concepts/tools",
    "transports": "https://modelcontextprotocol.io/docs/concepts/transports",
    "debugging": "https://modelcontextprotocol.io/docs/tools/debugging",
    "examples": "https://modelcontextprotocol.io/examples",
    "quickstart": "https://modelcontextprotocol.io/quickstart/server",
    "building-with-llms": "https://modelcontextprotocol.io/tutorials/building-mcp-with-llms"
}
```

## Local Documentation Validation

When `--validate-local` is used, the command will:

1. Look for corresponding documentation in `docs/fastmcp/`
2. Compare key concepts and implementations
3. Identify any gaps or inconsistencies
4. Suggest updates or improvements to local documentation

## Examples

```bash
# List available topics
/mcp-docs-lookup

# Fetch architecture documentation
/mcp-docs-lookup architecture

# Fetch tools documentation and validate against local docs
/mcp-docs-lookup tools --validate-local

# Fetch Python architecture specifics
/mcp-docs-lookup architecture-python
```
