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
