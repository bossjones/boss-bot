# LangGraph CLI commands
# Documentation: https://langchain-ai.github.io/langgraph/cloud/how-tos/studio/quick_start/

# Install LangGraph CLI with in-memory storage
[group('langgraph-cli')]
install-langgraph-cli:
	uv tool install 'langgraph-cli[inmem]'

# Build LangGraph Platform API server Docker image
[group('langgraph-cli')]
langgraph-build:
	uv tool run --from langgraph-cli langgraph build -t boss-bot --pull -c langgraph.json

# Run LangGraph API server in development mode with hot reloading and debugging capabilities. This lightweight server requires no Docker installation and is suitable for development and testing. State is persisted to a local directory.
[group('langgraph-cli')]
langgraph-dev:
	uv tool run --from langgraph-cli langgraph dev

# Generate a Dockerfile for building a LangGraph Platform API server Docker image.
[group('langgraph-cli')]
langgraph-dockerfile:
	uv tool run --from langgraph-cli langgraph dockerfile -c langgraph.json Dockerfile

# Start LangGraph API server. For local testing, requires a LangSmith API key with access to LangGraph Platform closed beta. Requires a license key for production use.
[group('langgraph-cli')]
langgraph-up:
	uv tool run --from langgraph-cli langgraph up --wait --watch --verbose -c langgraph.json
