# Discord RAG Bot PRD Generation Prompts

## Prompt 1: Initial Project Scope and MVP Features
```
Let's follow the @workflow-agile-manual to create a PRD for a Discord RAG bot project. The MVP will focus on implementing a basic RAG system with Redis as the vector store and OpenAI for embeddings and LLM.

Key MVP Features:
- Discord bot integration with discord.py
- RAG implementation using LangChain and LangGraph
- Redis vector store integration
- Basic document ingestion and query commands
- Modular architecture with clear separation of concerns

Future enhancements will include:
- Media download capabilities (yt-dlp and gallery_dl)
- Advanced RAG features and optimizations
- Extended command set through Discord Cogs
- CLI interface using Typer

Please help me create a detailed PRD that emphasizes clean code principles, modularity (max 120 lines per module), and follows Python best practices. The target audience is a junior developer who needs to understand both the architecture and implementation details.
```

## Prompt 2: Technical Architecture and Dependencies
```
Let's create the technical architecture section of our Discord RAG bot PRD. We need to detail:

1. Core Dependencies:
   - Python 3.12 with uv package manager
   - LangChain and LangGraph for RAG
   - Redis vector store
   - OpenAI for embeddings and LLM
   - discord.py for Discord integration
   - Typer for CLI
   - loguru for logging
   - pydantic-settings for configuration
   - pytest for testing

2. Architecture Requirements:
   - Modular design with clear boundaries
   - Maximum 120 lines per module
   - DRY and YAGNI principles
   - Clear separation between:
     * Discord bot interface
     * RAG system
     * Vector store management
     * Media download utilities
     * CLI interface

Please help me define the technical architecture that will support both MVP and future features while maintaining clean code principles and scalability.
```

## Prompt 3: Implementation Strategy and Timeline
```
Let's define the implementation strategy and timeline for our Discord RAG bot PRD. We need to break down the development into clear phases:

Phase 1 (MVP):
- Core RAG system setup
- Discord bot integration
- Basic command structure
- Redis vector store implementation

Phase 2 (Enhanced Features):
- Media download capabilities
- Advanced RAG optimizations
- CLI interface
- Extended Discord commands

For each phase, we need to:
1. Define clear acceptance criteria
2. Establish testing requirements
3. Set up monitoring and logging
4. Plan for documentation
5. Consider scalability and performance metrics

Please help me create a detailed implementation plan that follows our modular architecture (120 lines per module max) and emphasizes maintainable, well-tested code.
```

## Prompt 4: RAG System and Document Processing
```
Let's detail the RAG system specifications for our Discord bot PRD:

Document Processing Requirements:
1. Supported Formats:
   - Initial: text files, PDFs, markdown, code snippets, images
   - Future: audio and video support

2. Processing Modes:
   - Real-time processing for online users
   - Batch processing capability for offline processing
   - Stateless conversation model (with future provision for history)

3. Vector Store Configuration:
   - Redis as primary vector store
   - OpenAI embeddings integration
   - Efficient document chunking and storage strategies

Please help me define the detailed specifications for the RAG system that ensures efficient document processing while maintaining modularity.
```

## Prompt 5: Discord Integration and Media Management
```
Let's specify the Discord integration and media handling requirements:

1. Discord Bot Configuration:
   - Required Intents:
     * message_content, guilds, members, bans
     * emojis, voice_states, messages, reactions
   - Support for both channel and DM interactions
   - Simple permission model (expandable)

2. Media Download Features:
   - Supported Platforms:
     * YouTube (via yt-dlp)
     * Reddit, Twitter, Instagram, TikTok (via gallery_dl)
   - Download Constraints:
     * Max file size: 50MB (Discord limit)
     * Temporary storage in temp directory
   - Single download processing (future queue system)

3. Error Handling and Logging:
   - Async-safe logging with loguru
   - Stdout logging configuration
   - Comprehensive error handling

Please help me define the integration specifications that ensure robust Discord functionality and efficient media handling.
```

## Notes for PRD Generation
- Each prompt should be used in sequence
- Iterate on the responses to refine the PRD
- Ensure all technical requirements are clearly documented
- Focus on maintainability and scalability
- Consider junior developer understanding
- Document all assumptions and constraints
- Start with minimal viable features, with clear paths for future enhancements
- Prioritize robustness and reliability over feature completeness
- Ensure proper error handling and logging from the start
- Keep security in mind with proper credentials management via .env and pydantic-settings
