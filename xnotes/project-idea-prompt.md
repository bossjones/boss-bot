# Discord RAG Bot PRD Generation Prompts

## Prompt 1: Initial Project Scope and MVP Features
```
Let's follow the @workflow-agile-manual to create a PRD for a Discord bot project. The MVP will focus on implementing robust media download capabilities with a foundation for future RAG features.

Key MVP Features:
- Discord bot integration with discord.py
- Media download commands ($dlt for Twitter, $dlr for Reddit)
- Download queue management and progress tracking
- File cleanup and temporary storage handling
- Comprehensive test coverage using pytest and dpytest

Future enhancements will include:
- RAG implementation using LangChain and LangGraph
- Redis vector store integration
- Extended command set through Discord Cogs
- CLI interface using Typer

Please help me create a detailed PRD that emphasizes TDD principles, clean code practices, modularity (max 120 lines per module), and follows Python best practices. The target audience is a junior developer who needs to understand both the architecture and implementation details.
```

## Prompt 2: Technical Architecture and Dependencies
```
Let's create the technical architecture section of our Discord bot PRD. We need to detail:

1. Core Dependencies:
   - Python 3.12 with uv package manager
   - discord.py for Discord integration
   - pytest and dpytest for testing
   - gallery-dl for Reddit downloads
   - yt-dlp for Twitter/video downloads
   - loguru for logging
   - pydantic-settings for configuration
   - aiohttp for async HTTP operations
   - tempfile and pathlib for file management

2. Future Dependencies (Post-MVP):
   - LangChain and LangGraph for RAG
   - Redis vector store
   - OpenAI for embeddings and LLM
   - Typer for CLI

3. Architecture Requirements:
   - TDD-first development approach
   - Modular design with clear boundaries
   - Maximum 120 lines per module
   - DRY and YAGNI principles
   - Clear separation between:
     * Discord bot interface
     * Download management
     * File handling utilities
     * Future RAG system

4. Testing Requirements:
   - Minimum 90% test coverage
   - All features must have tests before implementation
   - Comprehensive error case testing
   - Performance and load testing
   - Mock-based testing for external services

Please help me define the technical architecture that prioritizes testability, reliability, and maintainable code while setting a foundation for future RAG capabilities.
```

## Prompt 3: Implementation Strategy and Timeline
```
Let's define the implementation strategy and timeline for our Discord bot PRD. We need to break down the development into clear phases:

Phase 1 (MVP - Discord Core):
- Test infrastructure setup
- Basic Discord bot framework
- Download command implementation
- Queue management system

Phase 2 (MVP - Download Features):
- Enhanced download capabilities
- Progress tracking
- File management
- Error handling

For each phase, we need to:
1. Write comprehensive test suites first
2. Define clear acceptance criteria
3. Implement minimum code to pass tests
4. Refactor while maintaining coverage
5. Document all components

Implementation Plan:
| Task | Status | Deadline |
|------|--------|----------|
| Test Infrastructure Setup | To Do | 2024-05-15 |
| Basic Discord Integration | To Do | 2024-05-22 |
| Download Commands (Twitter) | To Do | 2024-05-29 |
| Download Commands (Reddit) | To Do | 2024-06-05 |
| Queue Management | To Do | 2024-06-12 |
| Progress Tracking | To Do | 2024-06-19 |

Testing Requirements:
- Test coverage >= 90%
- All error cases covered
- Performance tests included
- Integration tests for each feature
- Mock external services

Please help me create a detailed implementation plan that follows our TDD-first approach while maintaining clean code principles and modularity.
```

## Prompt 4: Discord Integration and Download System
```
Let's detail the Discord bot integration and download handling requirements:

1. Discord Bot Configuration:
   - Required Intents:
     * message_content, guilds, members
     * messages, reactions
   - Command Structure:
     * $dlt <url> - Twitter/video downloads
     * $dlr <url> - Reddit downloads
     * $dlq - Show queue status
     * $dlc - Cancel download
   - Permission Model:
     * Role-based access control
     * Download size limits per role
     * Queue priority handling

2. Download System Architecture:
   - Download Manager:
     * Async download queue
     * Progress tracking
     * Rate limiting
     * Concurrent download limits (max 5)
   - File Management:
     * Temporary storage handling
     * Automatic cleanup
     * File size validation
     * Format verification

3. Error Handling and Recovery:
   - Network failure recovery
   - Invalid URL handling
   - File system error management
   - Rate limit handling
   - Queue overflow management

4. Testing Strategy:
   ```python
   # Example test structure
   class TestDownloadCommands:
       @pytest.fixture
       async def setup_bot(self):
           bot = commands.Bot(command_prefix="$")
           await bot._async_setup_hook()
           return bot

       @pytest.mark.asyncio
       async def test_twitter_download(self, setup_bot):
           # Given
           url = "https://twitter.com/example/status/123"
           # When
           await dpytest.message("$dlt " + url)
           # Then
           assert dpytest.verify().message().contains("Download started")
           assert os.path.exists(f"{temp_dir}/download-123.mp4")

       @pytest.mark.asyncio
       async def test_download_queue(self, setup_bot):
           # Given
           urls = ["url1", "url2", "url3"]
           # When
           for url in urls:
               await dpytest.message("$dlt " + url)
           # Then
           assert dpytest.verify().message().contains("Position in queue: 3")
   ```

5. Performance Requirements:
   - Download initiation response: < 1 second
   - Queue status updates: Every 5 seconds
   - Maximum queue size: 50 items
   - Concurrent downloads: 5 max
   - File size limits: 50MB (Discord limit)

Please help me define the integration specifications that ensure robust Discord functionality and efficient download handling while following TDD principles.
```

## Prompt 5: Test-Driven Development Strategy
```
Let's define our TDD strategy for the Discord bot project, focusing on download features first:

1. Test Infrastructure Setup:
   - Core Test Fixtures:
     ```python
     @pytest.fixture
     async def test_bot():
         intents = discord.Intents.default()
         intents.message_content = True
         bot = commands.Bot(command_prefix="$", intents=intents)
         await bot._async_setup_hook()
         dpytest.configure(bot)
         yield bot
         await dpytest.empty_queue()

     @pytest.fixture
     def mock_downloader():
         with patch('bot.download.Downloader') as mock:
             yield mock
     ```

2. Command Testing Strategy:
   a) Download Command Tests:
      ```python
      @pytest.mark.asyncio
      class TestDownloadCommands:
          async def test_valid_twitter_url(self, test_bot, mock_downloader):
              url = "https://twitter.com/user/status/123"
              await dpytest.message(f"$dlt {url}")
              assert dpytest.verify().message().contains()
              mock_downloader.download.assert_called_once_with(url)

          async def test_invalid_url(self, test_bot):
              url = "not_a_url"
              await dpytest.message(f"$dlt {url}")
              assert dpytest.verify().message().contains("Invalid URL")

          async def test_queue_full(self, test_bot, mock_downloader):
              mock_downloader.queue_size.return_value = 50
              url = "https://twitter.com/user/status/123"
              await dpytest.message(f"$dlt {url}")
              assert dpytest.verify().message().contains("Queue full")
      ```

3. Integration Testing:
   ```python
   @pytest.mark.integration
   class TestDownloadFlow:
       async def test_download_to_completion(self, test_bot, mock_downloader):
           # Given
           url = "https://twitter.com/user/status/123"
           mock_downloader.download.return_value = "file.mp4"

           # When
           await dpytest.message(f"$dlt {url}")

           # Then
           assert dpytest.verify().message().contains("Started")
           await asyncio.sleep(1)
           assert dpytest.verify().message().contains("Complete")
           assert os.path.exists("file.mp4")
   ```

4. Error Case Testing:
   ```python
   @pytest.mark.asyncio
   class TestErrorHandling:
       async def test_network_failure(self, test_bot, mock_downloader):
           mock_downloader.download.side_effect = NetworkError
           url = "https://twitter.com/user/status/123"
           await dpytest.message(f"$dlt {url}")
           assert dpytest.verify().message().contains("Network error")

       async def test_rate_limit(self, test_bot, mock_downloader):
           mock_downloader.download.side_effect = RateLimitError
           url = "https://twitter.com/user/status/123"
           await dpytest.message(f"$dlt {url}")
           assert dpytest.verify().message().contains("Rate limited")
   ```

5. Performance Testing:
   ```python
   @pytest.mark.performance
   class TestPerformance:
       async def test_response_time(self, test_bot):
           start = time.time()
           await dpytest.message("$dlt url")
           response_time = time.time() - start
           assert response_time < 1.0

       async def test_concurrent_downloads(self, test_bot):
           urls = [f"url{i}" for i in range(10)]
           tasks = [dpytest.message(f"$dlt {url}") for url in urls]
           await asyncio.gather(*tasks)
           assert mock_downloader.active_downloads <= 5
   ```

Please help me establish a robust TDD workflow that ensures code quality and maintainability while following pytest and dpytest best practices.
```

## Prompt 6: Test Case Examples and Fixtures
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
    b = commands.Bot(command_prefix="!", intents=intents)
    await b._async_setup_hook()
    dpytest.configure(b)
    yield b
    await dpytest.empty_queue()

@pytest.mark.asyncio
async def test_rag_query(bot):
    await dpytest.message("!query What is Python?")
    assert dpytest.verify().message().contains().content("Python is")
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
