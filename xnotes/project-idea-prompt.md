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
   - pytest as primary testing framework with pytest-asyncio
   - dpytest for Discord.py testing
   - Directory structure:
     * tests/
       - conftest.py - Shared pytest fixtures
       - unit/ - Unit tests for individual components
       - integration/ - Integration tests
       - fixtures/ - Test data and configurations

2. Core Testing Areas:
   a) Discord Bot Testing (using dpytest):
      - Mock Discord.py interactions
      - Test command parsing and responses
      - Validate message handling
      - Test permission checks
      - Fixtures for Discord events
      Example:
      ```python
      @pytest_asyncio.fixture
      async def bot():
          intents = discord.Intents.default()
          intents.members = True
          intents.message_content = True
          b = commands.Bot(command_prefix="!", intents=intents)
          await b._async_setup_hook()
          dpytest.configure(b)
          yield b
          await dpytest.empty_queue()  # Cleanup

      @pytest.mark.asyncio
      async def test_rag_query(bot):
          await dpytest.message("!query What is Python?")
          assert dpytest.verify().message().contains().content("Python is")
      ```

   b) RAG System Testing:
      - Mock vector store interactions
      - Test document processing pipeline
      - Validate embedding generation
      - Test query/response accuracy
      - Fixtures for sample documents

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

Please help me establish a robust TDD workflow that ensures code quality and maintainability while following pytest and dpytest best practices.
```

## Prompt 7: Test Case Examples and Fixtures
```
Let's define example test cases and fixtures for our core components:

1. Discord Bot Tests (with dpytest):
```python
import pytest
import pytest_asyncio
import discord.ext.test as dpytest
from discord.ext import commands

@pytest_asyncio.fixture
async def bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    await bot._async_setup_hook()
    dpytest.configure(bot)
    yield bot
    await dpytest.empty_queue()

@pytest.mark.asyncio
async def test_document_ingestion(bot):
    await dpytest.message("!ingest sample.pdf")
    assert dpytest.verify().message().contains().content("Document ingested")

@pytest.mark.asyncio
async def test_rag_query(bot):
    await dpytest.message("!query What is RAG?")
    assert dpytest.verify().message().contains().content("response")
```

2. RAG System Tests:
```python
@pytest.fixture
def sample_documents():
    return [
        {"content": "Test document 1", "metadata": {"type": "text"}},
        {"content": "Test document 2", "metadata": {"type": "pdf"}}
    ]

@pytest.mark.asyncio
async def test_document_processing(sample_documents):
    result = await rag_system.process_documents(sample_documents)
    assert len(result.processed) == 2
    assert result.failed == 0

@pytest.mark.asyncio
async def test_query_processing():
    response = await rag_system.process_query("test query")
    assert response.answer is not None
    assert len(response.sources) >= 1
```

3. Media Download Tests:
```python
@pytest.fixture
def mock_download_url():
    return "https://example.com/video.mp4"

@pytest.mark.asyncio
async def test_media_download(bot, mock_download_url):
    await dpytest.message(f"!download {mock_download_url}")
    assert dpytest.verify().message().contains().content("Download complete")
    assert dpytest.verify().message().contains().content("File size:")
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
- Use dpytest for Discord.py testing
- Use pytest fixtures for reusable test components
- Implement comprehensive test coverage
- Mock external dependencies for faster tests
- Document test cases and their purposes
- Use parameterized tests for edge cases
- Include both positive and negative test scenarios
- Clean up test resources properly using fixtures
- Use dpytest's message verification for Discord interactions
