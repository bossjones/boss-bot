# MCP Client Library Implementation Plan

<instructions>
This plan outlines the implementation of a Model Context Protocol (MCP) client library for the boss-bot project. The implementation should follow these core principles:
- Use structured thinking and reasoning throughout development
- Maintain simplicity and avoid complex changes
- Provide clear examples and documentation
- Follow the standard workflow with verifiable checkpoints
</instructions>

## Overview

<thinking>
The Model Context Protocol (MCP) represents a standardized way for AI applications to connect with external data sources and tools. For the boss-bot project, this means we can extend the bot's capabilities by connecting to various MCP servers that expose different functionalities.

Key considerations for this implementation:
1. MVP should be as simple as possible - stdio transport only
2. No authentication complexity for initial version
3. Integration with existing bot architecture (Discord cogs, CLI commands)
4. Focus on local MCP servers running as subprocesses
5. Maintain consistency with existing boss-bot patterns
</thinking>

This plan outlines the implementation of a Model Context Protocol (MCP) client library for the boss-bot project. The MCP will enable the bot to connect with external data sources and tools through a standardized protocol.

### MVP Scope
- **Transport**: stdio-based communication only
- **Authentication**: No authentication required
- **Target**: Local MCP servers running as subprocesses
- **Integration**: Discord bot and CLI interface support

## Problem Analysis

<thinking>
The Model Context Protocol solves a key integration challenge: how can AI applications reliably connect to external systems and tools? Without MCP, each integration requires custom implementation. With MCP, we get a standardized protocol that works across different types of data sources and tools.

For boss-bot specifically, this opens up possibilities like:
- Connecting to file system servers for document processing
- Integrating with database servers for data queries
- Adding custom tool servers for specialized operations
- Expanding capabilities without modifying core bot code
</thinking>

The Model Context Protocol (MCP) is an open standard that allows AI applications to connect with external data sources and tools. It acts as a "USB-C port for AI applications," solving integration challenges between LLM applications and various external systems.

### Key MCP Concepts:
- **Resources**: Read-only data/context (files, database records, logs)
- **Tools**: Functions that AI models can execute with defined parameters
- **Prompts**: Reusable templates and workflows for LLM interactions
- **Transport**: Communication layer (stdio, HTTP/SSE, Streamable HTTP)

### Client Architecture:
```
Discord Bot/CLI → MCP Client → stdio Transport → MCP Server
```

## Standard Workflow

<thinking>
The standard workflow ensures we maintain control and verification at each step, avoiding any large or complex changes that could destabilize the existing codebase. Each phase should be small, testable, and reversible.
</thinking>

1. ✅ **Think through the problem** - Research completed, architecture understood
2. ⏳ **Write plan with todo items** - This document
3. ❌ **Check in for plan verification** - Pending user approval
4. ❌ **Work on todo items** - Awaiting plan approval
5. ❌ **High-level explanations** - Will provide during implementation
6. ❌ **Simple, minimal changes** - Focus on incremental development
7. ❌ **Review section** - Will be added after implementation

<instructions>
During implementation, each step should include:
- Clear explanation of what changes are being made
- Reasoning for why this approach was chosen
- Verification that the change works as expected
- Documentation of any issues encountered and how they were resolved
</instructions>

## Todo Items

<thinking>
The todo items should be organized in logical phases, with each item being small enough to implement and test independently. The phases should build upon each other, starting with the simplest possible implementation and gradually adding complexity.

Phase 1 focuses on getting the basic dependencies and structure in place.
Phase 2 implements the core client functionality.
Each subsequent phase adds a specific area of functionality.
</thinking>

### Phase 1: Project Setup and Dependencies

<instructions>
This phase establishes the foundation. Each item should be verified to work before moving to the next.
</instructions>

- [ ] Add MCP python-sdk dependency to pyproject.toml (`mcp` package, version >= 1.2.0)
  <thinking>This is the foundational dependency. Version >= 1.2.0 is required for stdio transport support.</thinking>

- [ ] Create `src/boss_bot/integrations/mcp/` directory structure
  <thinking>Following the existing integrations pattern in the codebase for consistency.</thinking>

- [ ] Create basic module structure with `__init__.py` files
  <thinking>Proper Python module setup to ensure imports work correctly.</thinking>

- [ ] Add MCP client imports and verify SDK availability
  <thinking>Quick verification that the dependency was installed correctly and can be imported.</thinking>

### Phase 2: Core Client Implementation

<instructions>
This phase implements the minimal viable MCP client. Focus on the simplest possible implementation that can connect to a server.
</instructions>

- [ ] Create `src/boss_bot/integrations/mcp/client.py` - Main MCP client class
  <thinking>This will be the core class that handles MCP protocol communication.</thinking>

- [ ] Implement `MCPClient` class with stdio transport support
  <example>
  ```python
  class MCPClient:
      async def connect(self, server_params: StdioServerParameters) -> None:
          # Establish stdio connection to MCP server

      async def disconnect(self) -> None:
          # Clean up connection and subprocess
  ```
  </example>

- [ ] Add server process management (start/stop subprocess)
  <thinking>Need to manage the lifecycle of the MCP server subprocess safely.</thinking>

- [ ] Implement session lifecycle (initialize, discover, cleanup)
  <thinking>Follow the MCP protocol flow: initialize, negotiate capabilities, then allow operations.</thinking>

- [ ] Add JSON-RPC 2.0 message handling
  <thinking>MCP uses JSON-RPC 2.0 for all communication, so this is essential.</thinking>

- [ ] Create capability negotiation during handshake
  <thinking>Part of the MCP protocol - client and server exchange supported capabilities.</thinking>

### Phase 3: Configuration and Settings

<instructions>
This phase integrates MCP configuration with the existing boss-bot settings system. Use the established patterns from BossSettings.
</instructions>

- [ ] Add MCP settings to `src/boss_bot/core/env.py` (BossSettings)
  <thinking>Integrate with existing Pydantic settings for consistency.</thinking>

- [ ] Create MCP server configuration schema (server paths, commands, args)
  <example>
  ```python
  class MCPServerConfig(BaseModel):
      command: str
      args: List[str] = Field(default_factory=list)
      env: Optional[Dict[str, str]] = None
  ```
  </example>

- [ ] Add environment variable support for MCP server configs
  <thinking>Follow the existing BOSS_BOT_ prefix pattern for environment variables.</thinking>

- [ ] Implement server parameter validation
  <thinking>Ensure server commands exist and are executable before attempting connection.</thinking>

### Phase 4: Core Operations Implementation

<instructions>
This phase implements the actual MCP protocol operations. Each operation should be implemented with proper error handling.
</instructions>

- [ ] Implement resource discovery and listing
  <thinking>Resources are read-only data sources that the MCP server exposes.</thinking>

- [ ] Add resource content retrieval
  <thinking>After discovering resources, we need to be able to fetch their content.</thinking>

- [ ] Implement tool discovery and execution
  <thinking>Tools are functions that can be executed with parameters - this is key functionality.</thinking>

- [ ] Add prompt template discovery (basic support)
  <thinking>Start with basic prompt support, can be enhanced later.</thinking>

- [ ] Create error handling and recovery mechanisms
  <thinking>MCP operations can fail in various ways - network issues, server errors, etc.</thinking>

- [ ] Add connection timeout and retry logic
  <thinking>Essential for reliability when dealing with external processes.</thinking>

### Phase 5: Integration Layer
- [ ] Create `src/boss_bot/integrations/mcp/manager.py` - High-level manager class
- [ ] Add multiple server connection management
- [ ] Implement connection pooling and lifecycle management
- [ ] Create unified interface for Discord/CLI consumption
- [ ] Add logging and monitoring integration

### Phase 6: Discord Bot Integration
- [ ] Create new Discord cog `src/boss_bot/bot/cogs/mcp.py`
- [ ] Add `/mcp-servers` command to list available servers
- [ ] Add `/mcp-resources` command to browse resources
- [ ] Add `/mcp-tools` command to discover and execute tools
- [ ] Implement error handling and user-friendly messages

### Phase 7: CLI Integration
- [ ] Create `src/boss_bot/cli/commands/mcp.py` - MCP CLI commands
- [ ] Add `bossctl mcp servers` subcommand
- [ ] Add `bossctl mcp resources` subcommand
- [ ] Add `bossctl mcp tools` subcommand
- [ ] Add `bossctl mcp execute` subcommand for tool execution

### Phase 8: Testing Implementation
- [ ] Create `tests/test_integrations/test_mcp/` directory structure
- [ ] Add unit tests for `MCPClient` class
- [ ] Create integration tests with mock MCP servers
- [ ] Add stdio transport testing
- [ ] Test error scenarios and edge cases
- [ ] Add Discord cog integration tests
- [ ] Add CLI command tests

### Phase 9: Documentation and Examples
- [ ] Create basic usage documentation in docstrings
- [ ] Add configuration examples to CLAUDE.md
- [ ] Create simple example MCP server for testing
- [ ] Add troubleshooting guide for common issues

### Phase 10: Final Integration and Testing
- [ ] Integration testing with real MCP servers
- [ ] Performance testing and optimization
- [ ] End-to-end testing through Discord and CLI
- [ ] Code review and refactoring
- [ ] Final documentation update

## Technical Architecture

<thinking>
The architecture should follow boss-bot's existing patterns while providing a clean abstraction for MCP functionality. Key considerations:

1. Separation of concerns - client handles protocol, manager handles multiple connections
2. Integration with existing bot architecture
3. Testability - each component should be unit testable
4. Extensibility - should be easy to add new MCP server types
5. Error handling - graceful failure and recovery
</thinking>

### Directory Structure

<example>
Following the established boss-bot patterns for integrations and testing:
</example>

```
src/boss_bot/integrations/mcp/
├── __init__.py              # Module exports
├── client.py                # Core MCP client implementation
├── manager.py               # High-level connection manager
├── models.py                # Pydantic models for MCP data
├── exceptions.py            # MCP-specific exceptions
└── utils.py                 # Helper utilities

src/boss_bot/bot/cogs/
├── mcp.py                   # Discord MCP commands

src/boss_bot/cli/commands/
├── mcp.py                   # CLI MCP commands

tests/test_integrations/test_mcp/
├── test_client.py           # Client unit tests
├── test_manager.py          # Manager tests
├── test_integration.py      # Integration tests
└── conftest.py              # MCP test fixtures
```

<thinking>
This structure separates the core MCP client logic from the integration points (Discord, CLI), making it easier to test and maintain. The tests mirror the source structure for easy navigation.
</thinking>

### Key Classes and Interfaces

#### MCPClient
```python
class MCPClient:
    """Core MCP client for stdio transport."""

    async def connect(self, server_params: StdioServerParameters) -> None
    async def disconnect(self) -> None
    async def list_resources(self) -> List[Resource]
    async def get_resource(self, uri: str) -> ResourceContent
    async def list_tools(self) -> List[Tool]
    async def call_tool(self, name: str, arguments: Dict) -> ToolResult
    async def list_prompts(self) -> List[Prompt]
```

#### MCPManager
```python
class MCPManager:
    """High-level manager for multiple MCP connections."""

    async def start(self) -> None
    async def stop(self) -> None
    async def get_all_resources(self) -> Dict[str, List[Resource]]
    async def get_all_tools(self) -> Dict[str, List[Tool]]
    async def execute_tool(self, server: str, tool: str, args: Dict) -> ToolResult
```

### Configuration Schema
```python
class MCPSettings(BaseModel):
    """MCP client configuration."""

    enabled: bool = False
    servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    connection_timeout: int = 30
    retry_attempts: int = 3

class MCPServerConfig(BaseModel):
    """Individual MCP server configuration."""

    command: str
    args: List[str] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None
```

## Integration Points

### Environment Variables
```bash
# Enable MCP client
export BOSS_BOT_MCP_ENABLED=true

# Server configurations (JSON format)
export BOSS_BOT_MCP_SERVERS='{
    "filesystem": {
        "command": "python",
        "args": ["-m", "mcp_server_filesystem", "/path/to/data"],
        "env": {}
    }
}'
```

### Discord Commands
```
# List available MCP servers
$mcp-servers

# Browse resources from a server
$mcp-resources filesystem

# List available tools
$mcp-tools filesystem

# Execute a tool
$mcp-execute filesystem read_file path="/etc/hosts"
```

### CLI Commands
```bash
# List servers
bossctl mcp servers

# Browse resources
bossctl mcp resources filesystem --list

# Execute tools
bossctl mcp execute filesystem read_file --path "/etc/hosts"
```

## Dependencies

### Required Packages
- `mcp` (>= 1.2.0) - Official MCP Python SDK
- `pydantic` - Already available for data validation
- `asyncio` - Already available for async operations

### Development Dependencies
- `pytest-asyncio` - Already available for testing async code
- `pytest-mock` - Already available for mocking

## Risk Assessment

### Low Risks
- **stdio transport**: Well-documented and stable
- **No authentication**: Removes security complexity
- **Local servers only**: No network/firewall issues

### Medium Risks
- **Process management**: Server subprocess lifecycle needs careful handling
- **Error handling**: Network-like errors even with local processes
- **Resource cleanup**: Proper cleanup of connections and processes

### High Risks
- **Performance**: Multiple server connections may impact bot responsiveness
- **Security**: Even local servers can pose security risks if misconfigured
- **Complexity**: MCP protocol has many edge cases and failure modes

## Success Criteria

### MVP Success Metrics
- [ ] Successfully connect to at least one MCP server via stdio
- [ ] List and retrieve resources from connected server
- [ ] Discover and execute at least basic tools
- [ ] Integration working in both Discord and CLI interfaces
- [ ] All tests passing with reasonable coverage (>60%)
- [ ] No memory leaks or connection handling issues

### Future Expansion Criteria
- HTTP/SSE transport support
- Authentication mechanisms
- Multiple simultaneous server connections
- Resource caching and optimization
- Advanced prompt template support

## Notes

- Focus on simplicity and reliability over feature completeness
- Use existing bot patterns for error handling and logging
- Leverage the python-sdk's built-in capabilities rather than reimplementing
- Test thoroughly with the MCP Inspector tool during development
- Consider the bot's existing async patterns when designing the client

## Review Section

<instructions>
This section will be completed after implementation. During implementation, update this section with:
- Summary of changes made
- Lessons learned during development
- Any deviations from the original plan
- Performance observations
- Areas for future improvement
</instructions>

<findings>
*This section will be populated during and after implementation.*
</findings>

<recommendations>
*Future enhancement recommendations will be added here after MVP completion.*
</recommendations>

---

**Plan Status**: ⏳ Awaiting approval
**Created**: 2025-06-23
**Next Steps**: User verification and approval to begin implementation

<instructions>
Once approved, implementation should proceed phase by phase, with each phase being completed and verified before moving to the next. Each completed phase should update the corresponding todo items and provide a brief summary of what was accomplished.
</instructions>
