# | MCP Server         | Purpose                                                                                         |
# |--------------------|------------------------------------------------------------------------------------------------|
# | context7           | Real-time, version-specific documentation/code examples in prompts for accurate coding help[1][2] |
# | memory-bank        | Centralized, persistent storage and retrieval of project context/memory files[3]                |
# | mcp-knowledge-graph| Dynamic knowledge graph construction and querying for advanced AI context[4]                    |
# | taskmaster-ai      | AI-driven task management and workflow automation with LLM integration[5]                       |
# | peekaboo-mcp       | Screenshot capture and visual question answering for AI agents on macOS[6]                      |
# | reddit-mcp         | https://github.com/Arindam200/reddit-mcp Model Context Protocol server implementation for Reddit |
# | playwright-mcp     | https://github.com/microsoft/playwright-mcp Browser automation and web scraping via Playwright |
# | search-tools-mcp   | https://github.com/voxmenthe/search-tools-mcp Advanced search tools for content discovery      |
# | ht-mcp             | https://github.com/memextech/ht-mcp HTTP testing and API interaction utilities                  |
# | apple-mcp          | https://github.com/supermemoryai/apple-mcp Apple ecosystem integration for macOS/iOS devices   |

# add mcp to claude code
[group('mcp')]
add-mcp-to-claude-code:
    claude mcp add mcp-server-click -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/pallets/click
    claude mcp add mcp-server-democracy-exe -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/bossjones/democracy-exe
    claude mcp add mcp-server-discordpy -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/Rapptz/discord.py
    claude mcp add mcp-server-dpytest -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/craftspider/dpytest
    claude mcp add mcp-server-fastmcp -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/modelcontextprotocol/python-sdk
    claude mcp add mcp-server-gallery-dl -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/mikf/gallery-dl
    claude mcp add mcp-server-jinja2-tools -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/Avielyo10/jinja2-tools
    claude mcp add mcp-server-langgraph-builder -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/langchain-ai/langgraph-builder
    claude mcp add mcp-server-langgraph-gen-py -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/langchain-ai/langgraph-gen-py
    claude mcp add mcp-server-langgraph-swarm-py -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/langchain-ai/langgraph-swarm-py
    claude mcp add mcp-server-loguru -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/Delgan/loguru
    claude mcp add mcp-server-pydantic -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/pydantic/pydantic
    claude mcp add mcp-server-pydantic-settings -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/pydantic/pydantic-settings
    claude mcp add mcp-server-pytest-recording -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/kiwicom/pytest-recording
    claude mcp add mcp-server-red -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/Cog-Creators/Red-DiscordBot
    claude mcp add mcp-server-rich -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/Textualize/rich
    claude mcp add mcp-server-securityonion -- npx -y mcp-remote@v0.1.9 https://github.com/Security-Onion-Solutions/securityonion
    claude mcp add mcp-server-typer -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/fastapi/typer
    claude mcp add mcp-server-vcrpy -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/kevin1024/vcrpy
    claude mcp add mcp-server-yt-dlp -- npx -y mcp-remote@v0.1.9 https://gitmcp.io/yt-dlp/yt-dlp
    claude mcp add-json mcp-mermaid '{"command":"npx","args":["-y","mcp-mermaid"]}'
    claude mcp add-json mermaid-validator '{"command":"npx","args":["-y","@rtuin/mcp-mermaid-validator@latest"]}'
    claude mcp add langgraph-docs-mcp -- uvx --from mcpdoc mcpdoc --urls "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt LangChain:https://python.langchain.com/llms.txt" --transport stdio
    claude mcp add claude-code-docs-mcp -- uvx --from mcpdoc mcpdoc --urls "ClaudeCode:https://docs.anthropic.com/llms.txt" --transport stdio
    claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
    claude mcp add-json time '{"command":"uvx","args":["mcp-server-time","--local-timezone=America/New_York"]}'

# Generate MCP commands from repos.txt
[group('mcp')]
generate-mcp-commands:
    uv run python scripts/generate_mcp_commands.py
    @echo 'claude mcp add langgraph-docs-mcp -- uvx --from mcpdoc mcpdoc --urls "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt LangChain:https://python.langchain.com/llms.txt" --transport stdio'
    @echo 'claude mcp add claude-code-docs-mcp -- uvx --from mcpdoc mcpdoc --urls "ClaudeCode:https://docs.anthropic.com/llms.txt" --transport stdio'

# Generate experimental MCP commands from repos.txt
[group('mcp')]
generate-mcp-experimental:
    @echo 'claude mcp add context7 -- npx -y @upstash/context7-mcp@v1.0.14'
    @echo 'claude mcp add-json memory-bank '\''{"command":"npx","args":["-y","@allpepper/memory-bank-mcp@latest"], "env":{"MEMORY_BANK_ROOT":"/Users/malcolm/shared_memory_bank"}}'\'''
    @echo 'claude mcp add-json mcp-knowledge-graph '\''{"command":"npx","args":["-y","mcp-knowledge-graph","--memory-path","/Users/malcolm/shared_knowledge_graph"]}'\'''
    @echo 'claude mcp add-json taskmaster-ai '\''{"command":"npx","args":["-y","--package=task-master-ai","task-master-ai"],"env":{"ANTHROPIC_API_KEY":"$ANTHROPIC_API_KEY","PERPLEXITY_API_KEY":"$PERPLEXITY_API_KEY","OPENAI_API_KEY":"$OPENAI_API_KEY","GOOGLE_API_KEY":"$GOOGLE_API_KEY"}}'\'''
    @echo 'claude mcp add-json peekaboo-mcp '\''{"command":"npx","args":["-y","@steipete/peekaboo-mcp@v1.1.0"], "env":{"OPENAI_API_KEY":"$OPENAI_API_KEY","PEEKABOO_LOG_LEVEL":"debug","PEEKABOO_LOG_FILE":"~/Library/Logs/peekaboo-mcp-debug.log","PEEKABOO_DEFAULT_SAVE_PATH":"~/Pictures/PeekabooCaptures","PEEKABOO_CONSOLE_LOGGING":"false","PEEKABOO_CLI_TIMEOUT":"30000", "PEEKABOO_AI_PROVIDERS": "openai/gpt-4o"}}'\'''
    @echo 'claude mcp add-json browsermcp '\''{"command":"npx","args":["@browsermcp/mcp@latest"]}'\'''
    @echo 'claude mcp add-json perplexity-ask '\''{"command":"npx","args":["-y","server-perplexity-ask"],"env":{"PERPLEXITY_API_KEY":"$PERPLEXITY_API_KEY"}}'\'''
