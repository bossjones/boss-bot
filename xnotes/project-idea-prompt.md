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

## Prompt 6: Test-Driven Development Strategy
```
Let's define our TDD strategy for the Discord RAG bot project, following the Red-Green-Refactor cycle:

1. Testing Infrastructure:
   - pytest as primary testing framework
   - Directory structure:
     * tests/unit/ - Unit tests for individual components
     * tests/integration/ - Integration tests for component interactions
     * tests/fixtures/ - Reusable test data and configurations
     * tests/conftest.py - Shared pytest fixtures

2. Core Testing Areas:
   a) RAG System Testing:
      - Mock vector store interactions
      - Test document processing pipeline
      - Validate embedding generation
      - Test query/response accuracy
      - Fixtures for sample documents

   b) Discord Bot Testing:
      - Mock Discord.py interactions
      - Test command parsing
      - Validate permission checks
      - Test response formatting
      - Fixtures for Discord events

   c) Media Download Testing:
      - Mock download operations
      - Test file size validation
      - Validate temporary storage
      - Test cleanup operations
      - Fixtures for media URLs

3. TDD Implementation Flow:
   - Write failing test first
   - Implement minimal code to pass
   - Refactor while maintaining test coverage
   - Document test cases and fixtures
   - Use parameterized tests for edge cases

4. LLM-Specific Testing:
   - Create curated test datasets
   - Define evaluation metrics
   - Test response consistency
   - Validate RAG accuracy
   - Mock LLM interactions for fast tests

Please help me establish a robust TDD workflow that ensures code quality and maintainability while following pytest best practices.
```

## Prompt 7: Test Case Examples and Fixtures
```
Let's define example test cases and fixtures for our core components:

1. RAG System Tests:
```python
@pytest.fixture
def sample_documents():
    return [
        {"content": "Test document 1", "metadata": {"type": "text"}},
        {"content": "Test document 2", "metadata": {"type": "pdf"}}
    ]

def test_document_ingestion(sample_documents):
    # Red: Write failing test for document ingestion
    result = rag_system.ingest_documents(sample_documents)
    assert len(result.processed) == 2
    assert result.failed == 0

@pytest.mark.asyncio
async def test_query_processing():
    # Red: Write failing test for query processing
    response = await rag_system.process_query("test query")
    assert response.answer is not None
    assert response.sources >= 1
```

2. Discord Command Tests:
```python
@pytest.fixture
def mock_discord_message():
    return {
        "content": "!query test question",
        "author": {"id": "123"},
        "channel": {"id": "456"}
    }

@pytest.mark.asyncio
async def test_query_command(mock_discord_message):
    # Red: Write failing test for Discord command
    response = await bot.process_command(mock_discord_message)
    assert response.content is not None
    assert response.error is None
```

Please help me develop comprehensive test cases that cover our core functionality while following TDD principles.
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
- Follow TDD principles strictly: Red-Green-Refactor
- Write tests before implementing features
- Use pytest fixtures for reusable test components
- Implement comprehensive test coverage
- Mock external dependencies for faster tests
- Document test cases and their purposes
- Use parameterized tests for edge cases
- Include both positive and negative test scenarios
