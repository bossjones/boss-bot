# LangGraph CLI commands
# Documentation: https://langchain-ai.github.io/langgraph/cloud/how-tos/studio/quick_start/

# Install LangGraph CLI with in-memory storage
[group('langgraph-cli')]
install-langgraph-cli:
	uv tool install 'langgraph-cli[inmem]'

# Build LangGraph application
[group('langgraph-cli')]
build:
	uvx langgraph build

# Run LangGraph in development mode
[group('langgraph-cli')]
dev:
	uvx langgraph dev

# Generate Dockerfile for LangGraph
[group('langgraph-cli')]
dockerfile:
	uvx langgraph dockerfile

# Start LangGraph services
[group('langgraph-cli')]
up:
	uvx langgraph up
