# LangGraph CLI commands
# Documentation: https://langchain-ai.github.io/langgraph/cloud/how-tos/studio/quick_start/

# Install LangGraph CLI with in-memory storage
[group('langgraph-cli')]
install-langgraph-cli:
	uv tool install 'langgraph-cli[inmem]'

# Build LangGraph application
[group('langgraph-cli')]
langgraph-build:
	uv tool run --from langgraph-cli langgraph build

# Run LangGraph in development mode
[group('langgraph-cli')]
langgraph-dev:
	uv tool run --from langgraph-cli langgraph dev

# Generate Dockerfile for LangGraph
[group('langgraph-cli')]
langgraph-dockerfile:
	uv tool run --from langgraph-cli langgraph dockerfile -c langgraph.json Dockerfile

# Start LangGraph services
[group('langgraph-cli')]
langgraph-up:
	uv tool run --from langgraph-cli langgraph up
