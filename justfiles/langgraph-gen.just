# LangGraph Gen commands for generating LangGraph stubs from YAML specifications
# Documentation: https://github.com/langchain-ai/langgraph-gen-py

# Install LangGraph Gen
[group('langgraph-gen')]
install-langgraph-gen:
	uv add langgraph-gen

# Generate Python code from spec file
[group('langgraph-gen')]
gen spec="spec.yml":
	uvx langgraph-gen {{spec}}

# Generate Python code with custom output path
[group('langgraph-gen')]
gen-output spec="spec.yml" output="agent.py":
	uvx langgraph-gen {{spec}} -o {{output}}

# Generate Python code with implementation stubs
[group('langgraph-gen')]
gen-impl spec="spec.yml" output="agent.py" impl="implementation.py":
	uvx langgraph-gen {{spec}} -o {{output}} --implementation {{impl}}

# Generate TypeScript code from spec file
[group('langgraph-gen')]
gen-ts spec="spec.yml":
	uvx langgraph-gen {{spec}} --language typescript

# Generate TypeScript code with custom output path
[group('langgraph-gen')]
gen-ts-output spec="spec.yml" output="agent.ts":
	uvx langgraph-gen {{spec}} --language typescript -o {{output}}

# Generate TypeScript code with implementation stubs
[group('langgraph-gen')]
gen-ts-impl spec="spec.yml" output="agent.ts" impl="implementation.ts":
	uvx langgraph-gen {{spec}} --language typescript -o {{output}} --implementation {{impl}}

# Show LangGraph Gen version
[group('langgraph-gen')]
version:
	uvx langgraph-gen --version
