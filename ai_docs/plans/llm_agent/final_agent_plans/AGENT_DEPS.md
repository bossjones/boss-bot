# Boss-Bot LangGraph Multi-Agent Dependencies

This document outlines all dependencies required to successfully build and deploy the Boss-Bot LangGraph multi-agent system. Dependencies are organized by category with detailed descriptions and purposes within the Boss-Bot architecture.

## Dependency Overview

| **Category** | **Package Count** | **Purpose** |
|--------------|-------------------|-------------|
| Core Framework | 8 | LangGraph workflow orchestration and execution |
| Model Providers | 6 | AI model integrations (OpenAI, Anthropic, Google, etc.) |
| Data & Storage | 3 | Persistence, checkpointing, and vector storage |
| Evaluation & Testing | 3 | Agent performance evaluation and debugging |
| Media Processing | 3 | Video, image, and audio processing capabilities |
| Specialized Tools | 3 | Enhanced reliability and utility functions |

---

## Core LangGraph/LangChain Framework

| **Package** | **Description** | **Purpose in Boss-Bot** | **Installation** |
|-------------|-----------------|-------------------------|------------------|
| **[langgraph](https://github.com/langchain-ai/langgraph)** | Core LangGraph library for building stateful, multi-actor applications with LLMs | Primary framework for orchestrating the hybrid hierarchical-swarm architecture | `uv add langgraph` |
| **[langgraph-cli[inmem]](https://github.com/langchain-ai/langgraph)** | CLI tools for LangGraph development with in-memory graph execution | Develop and test Boss-Bot agent workflows locally with hot-reload capabilities | `uv tool install 'langgraph-cli[inmem]'` |
| **[langgraph-sdk](https://github.com/langchain-ai/langgraph)** | Software development kit with APIs, primitives, and utilities for LangGraph applications | Core SDK for building Boss-Bot's custom agent workflows and state management | `uv add langgraph-sdk` |
| **[langgraph-gen](https://github.com/langchain-ai/langgraph-gen-py)** | CLI tool for auto-generating LangGraph stubs from YAML specifications | Generate initial Boss-Bot agent code from our spec.yml configuration | `uv add langgraph-gen` |
| **[langgraph-swarm-py](https://github.com/langchain-ai/langgraph-swarm-py)** | LangGraph implementation of swarm-style multi-agent orchestration patterns | Enable swarm coordination patterns for distributed agent collaboration in Boss-Bot | `uv add git+https://github.com/langchain-ai/langgraph-swarm-py` |
| **[langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py)** | Supervisor pattern implementation for hierarchical agent management | Implement hierarchical supervision in Boss-Bot's hybrid agent architecture | `uv add git+https://github.com/langchain-ai/langgraph-supervisor-py` |
| **[langgraph-checkpoint-sqlite](https://github.com/langchain-ai/langgraph)** | Checkpointing and state persistence for LangGraph applications using SQLite | Enable state persistence across Discord sessions and agent handoffs | `uv add langgraph-checkpoint-sqlite` |
| **[langchain-core](https://github.com/langchain-ai/langchain)** | Core abstractions and interfaces for LangChain ecosystem | Foundation for all LangChain integrations in Boss-Bot | `uv add langchain-core` |

---

## Model Provider Integrations

| **Package** | **Description** | **Purpose in Boss-Bot** | **Installation** |
|-------------|-----------------|-------------------------|------------------|
| **[langchain-openai](https://github.com/langchain-ai/langchain)** | Integration with OpenAI models (GPT-4, GPT-3.5, DALL-E) | Primary LLM provider for content analysis, strategy selection, and user interaction | `uv add langchain-openai` |
| **[langchain-anthropic](https://github.com/langchain-ai/langchain)** | Integration with Anthropic's Claude models | Alternative LLM provider for enhanced reasoning and content analysis | `uv add langchain-anthropic` |
| **[langchain-google-genai](https://github.com/langchain-ai/langchain)** | Integration with Google's Generative AI models (Gemini) | Additional model option for multimodal content analysis | `uv add langchain-google-genai` |
| **[langchain-groq](https://github.com/langchain-ai/langchain)** | Integration with Groq's high-speed LLM inference hardware | Fast inference option for real-time Discord interactions | `uv add langchain-groq` |
| **[langchain-aws](https://github.com/langchain-ai/langchain)** | Integration with AWS services (Bedrock, S3, Lambda) | Cloud infrastructure integration for scalable deployments | `uv add langchain-aws` |
| **[langchain-mcp-adapters](https://github.com/langchain-ai/langchain)** | Model Context Protocol adapters for standardized tool access | Unified interface for external tools and APIs in agent workflows | `uv add langchain-mcp-adapters` |

---

## Data Storage & Persistence

| **Package** | **Description** | **Purpose in Boss-Bot** | **Installation** |
|-------------|-----------------|-------------------------|------------------|
| **[langchain-postgres](https://github.com/langchain-ai/langchain-postgres)** | PostgreSQL integration for structured and vector data storage | Store user preferences, download history, and agent memory data | `uv add langchain-postgres` |
| **[langchain-text-splitters](https://github.com/langchain-ai/langchain-text-splitters)** | Utilities for splitting large text into manageable chunks | Process large content descriptions and documentation for analysis | `uv add langchain-text-splitters` |
| **[langmem](https://github.com/langchain-ai/langmem)** | Agent memory management with short-term and long-term memory support | Maintain user context and preferences across Discord sessions | `uv add langmem` |

---

## Evaluation & Testing

| **Package** | **Description** | **Purpose in Boss-Bot** | **Installation** |
|-------------|-----------------|-------------------------|------------------|
| **[langsmith[pytest]](https://github.com/langchain-ai/langsmith)** | Platform for inspecting, monitoring, evaluating, and debugging LLM applications | Monitor agent performance, track errors, and debug multi-agent workflows | `uv add langsmith[pytest]` |
| **[agentevals](https://github.com/langchain-ai/agentevals)** | Specialized evaluation toolkit for AI agent trajectories and decision-making processes | Evaluate Boss-Bot's multi-step download and processing workflows | `uv add git+https://github.com/langchain-ai/agentevals` |
| **[openevals](https://github.com/langchain-ai/openevals)** | General-purpose evaluation toolkit for LLM outputs with prebuilt evaluators | Assess content analysis quality, strategy selection accuracy, and response generation | `uv add git+https://github.com/langchain-ai/openevals` |
| **[pytest-recording](https://github.com/kiwicom/pytest-recording)** | Integration testing framework with VCR.py for recording/replaying HTTP interactions | Record real API interactions for deterministic agent testing without live API calls | `uv add pytest-recording` |

---

## Media Processing

| **Package** | **Description** | **Purpose in Boss-Bot** | **Installation** |
|-------------|-----------------|-------------------------|------------------|
| **[ffmpeg](https://github.com/FFmpeg/FFmpeg)** | Powerful multimedia framework for video/audio conversion and processing | Core video processing: transcoding, quality optimization, thumbnail generation | System: `apt install ffmpeg` / `brew install ffmpeg` |
| **[pillow](https://github.com/python-pillow/Pillow)** | Python Imaging Library for opening, manipulating, and saving image files | Image processing: resizing, cropping, format conversion for Discord optimization | `uv add pillow` |
| **[imagemagick](https://github.com/ImageMagick/ImageMagick)** | Command-line image processing suite for batch operations and transformations | Advanced image processing and batch operations for media optimization | System: `apt install imagemagick` / `brew install imagemagick` |

---

## Specialized Tools & Utilities

| **Package** | **Description** | **Purpose in Boss-Bot** | **Installation** |
|-------------|-----------------|-------------------------|------------------|
| **[trustcall](https://github.com/hinthornw/trustcall)** | Reliable structured data extraction with JSON patch operations and validation | Enhance agent tool calling reliability and structured output validation | `uv add git+https://github.com/hinthornw/trustcall` |
| **[langchain-community](https://github.com/langchain-ai/langchain)** | Community-contributed integrations and utilities for LangChain ecosystem | Access to additional tools, retrievers, and utility functions | `uv add langchain-community` |
| **[langchainhub](https://github.com/langchain-ai/langchainhub)** | Repository for sharing and discovering LangChain prompts, chains, and agents | Access to pre-built prompts and agent templates for content analysis | `uv add langchainhub` |

---

## Complete Installation Commands

### Core Python Dependencies
```bash
# Core LangGraph/LangChain Framework
uv add langgraph langgraph-sdk langgraph-gen langgraph-checkpoint-sqlite langchain-core
uv add git+https://github.com/langchain-ai/langgraph-swarm-py
uv add git+https://github.com/langchain-ai/langgraph-supervisor-py

# LangGraph CLI Tools (installed as tool due to dependency conflicts)
uv tool install 'langgraph-cli[inmem]'

# Model Provider Integrations
uv add langchain-openai langchain-anthropic langchain-google-genai langchain-groq langchain-aws langchain-mcp-adapters

# Data Storage & Persistence
uv add langchain-postgres langchain-text-splitters langmem

# Evaluation & Testing
uv add langsmith[pytest] pytest-recording
uv add git+https://github.com/langchain-ai/agentevals
uv add git+https://github.com/langchain-ai/openevals

# Media Processing (Python components)
uv add pillow

# Specialized Tools
uv add git+https://github.com/hinthornw/trustcall
uv add langchain-community langchainhub
```

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg imagemagick

# macOS
brew install ffmpeg imagemagick

# Windows (using Chocolatey)
choco install ffmpeg imagemagick
```

### Alternative: LangChain Meta-Package
```bash
# Install LangChain with multiple provider support
uv add 'langchain[anthropic,community,huggingface,openai,perplexity,xai]'
```

---

## Environment Configuration

### Required Environment Variables
```bash
# AI Model API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
export GROQ_API_KEY="your-groq-key"

# LangSmith Configuration
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your-langsmith-key"
export LANGCHAIN_PROJECT="boss-bot-agents"

# Database Configuration (if using PostgreSQL)
export POSTGRES_CONNECTION_STRING="postgresql://user:pass@localhost:5432/bossbot"

# Boss-Bot Specific
export BOSS_BOT_AI_ENABLED=true
export BOSS_BOT_AGENT_MODE="hybrid-hierarchical-swarm"
```

---

## Platform-Specific Notes

### Discord.py Integration
- Ensure compatibility with Boss-Bot's existing Discord.py version
- LangGraph agents will integrate with existing cog system
- Async/await patterns must align with Discord.py event loop

### Epic 5 Strategy Pattern Integration
- LangGraph agents enhance existing download strategies
- Fallback mechanisms maintain compatibility with CLI/API patterns
- Feature flags control gradual AI rollout

### Integration Testing with pytest-recording
- Record real API interactions for reproducible tests
- Avoid live API calls during CI/CD pipeline execution
- See [LangChain Testing Guide](https://python.langchain.com/docs/contributing/how_to/testing/) for best practices

### Performance Considerations
- SQLite checkpointing for development/small deployments
- PostgreSQL recommended for production with multiple users
- Consider Redis for high-performance state management
- Media processing libraries may require significant system resources

---

## Version Compatibility Matrix

| **Component** | **Minimum Version** | **Recommended Version** | **Notes** |
|---------------|-------------------|------------------------|-----------|
| Python | 3.9+ | 3.11+ | Required for LangGraph async features |
| LangGraph | 0.2.0+ | Latest | Core framework dependency |
| LangChain | 0.3.0+ | Latest | Compatible with LangGraph |
| Discord.py | 2.0+ | Current Boss-Bot version | Maintain existing compatibility |
| FFmpeg | 4.0+ | 6.0+ | Video processing capabilities |
| PostgreSQL | 12+ | 15+ | If using persistent storage |

---

## Development vs Production Dependencies

### Development Only
```bash
uv add pytest pytest-asyncio pytest-mock dpytest
uv add black ruff mypy pre-commit
uv add jupyter notebook  # For agent development and testing
```

### Production Additions
```bash
uv add uvicorn fastapi  # If exposing LangGraph API
uv add prometheus-client  # For metrics integration
uv add sentry-sdk  # For error tracking
```

This dependency list ensures Boss-Bot's LangGraph multi-agent system has all required components for successful development, testing, and deployment while maintaining integration with the existing architecture.
