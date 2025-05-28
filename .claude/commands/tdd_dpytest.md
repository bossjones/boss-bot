# TDD dpytest Discord Bot Development
> Execute each task in the order given to implement Test-Driven Development with dpytest for Discord bot features.

**Arguments:** `$ARGUMENTS`

## Task 1: Analyze Feature Requirements

First, analyze the feature requirements from `$ARGUMENTS` and create a test specification:

- **Parse the feature request** - Extract the command name, expected behavior, and edge cases
- **Identify test scenarios** - Break down into happy path, error cases, and edge conditions
- **Map to bot architecture** - Determine if this is a cog, command, strategy, or handler test
- **Review existing patterns** - Check `docs/contributors/dpytest_example.md` for similar test patterns

**Output**: Clear understanding of what needs to be tested and why.

## Task 2: Create Test File Structure

Create the appropriate test file following boss-bot conventions:

- **Determine test location** - Use proper directory structure under `tests/`
- **Create test file** - Follow naming convention `test_[feature_name].py`
- **Add required imports** - Include pytest, dpytest, and boss-bot specific imports
- **Set up docstring** - Describe the test module purpose and scope

**Example structure**:
```python
"""Test [feature_name] functionality with dpytest.

This module tests [description] using both dpytest integration
and direct command callback testing approaches.
"""

import pytest
import pytest_asyncio
import discord.ext.test as dpytest

# Boss-bot imports
from boss_bot.bot.cogs.[cog_name] import [CogClass]
from boss_bot.core.downloads.strategies import [StrategyClass]
```

## Task 3: Write Failing Tests First (RED)

Following TDD principles, write failing tests before implementation:

### Sub-task 3a: Basic Command Test
```python
@pytest.mark.asyncio
async def test_[command_name]_command_success(mock_bot, sample_urls):
    """Test [command_name] command succeeds with valid input."""
    # This test will fail initially - that's expected in TDD
    await dpytest.message("![command_name] [valid_input]")

    # Assert expected behavior
    assert dpytest.verify().message().contains().content("expected_success_message")
```

### Sub-task 3b: Error Handling Test
```python
@pytest.mark.asyncio
async def test_[command_name]_command_handles_invalid_input(mock_bot):
    """Test [command_name] command handles invalid input gracefully."""
    await dpytest.message("![command_name] invalid_input")

    # Assert error is handled properly
    assert dpytest.verify().message().contains().content("error_message")
```

### Sub-task 3c: Edge Case Tests
```python
@pytest.mark.asyncio
async def test_[command_name]_command_edge_case(mock_bot):
    """Test [command_name] command handles edge cases."""
    # Test empty input, malformed input, permission issues, etc.
    pass
```

**Verify**: Run tests and confirm they fail as expected: `just check-test "path/to/test_file.py"`

## Task 4: Mock External Dependencies

Set up comprehensive mocking before implementing:

### Sub-task 4a: Mock Strategy Dependencies
```python
@pytest.fixture(scope="function")
def mock_[strategy_name]_strategy(mocker):
    """Mock [strategy] for testing without external API calls."""
    mock_strategy = mocker.Mock(spec=[StrategyClass])
    mock_strategy.download = AsyncMock()
    mock_strategy.get_metadata = AsyncMock()
    mock_strategy.supports_url.return_value = True
    return mock_strategy
```

### Sub-task 4b: Mock External APIs
```python
@pytest.fixture(scope="function")
def mock_external_api(mocker):
    """Mock external API calls to prevent network dependencies."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"status": "success", "data": "test_data"}
    return mocker.patch('requests.get', return_value=mock_response)
```

### Sub-task 4c: Configure Test Data
```python
@pytest.fixture(scope="function")
def test_[feature]_data():
    """Provide test data for [feature] testing."""
    return {
        "valid_input": "test_valid_input",
        "invalid_input": "test_invalid_input",
        "expected_output": "expected_result"
    }
```

## Task 5: Implement Minimum Code (GREEN)

Now implement the minimum code to make tests pass:

### Sub-task 5a: Create Command Structure
- **Add command to appropriate cog** - Implement basic command skeleton
- **Handle required parameters** - Add parameter validation and parsing
- **Implement core logic** - Add the minimal logic to pass the first test

### Sub-task 5b: Add Error Handling
- **Validate inputs** - Check for required parameters and format
- **Handle exceptions** - Wrap risky operations in try/catch blocks
- **Return appropriate responses** - Send success/error messages to Discord

### Sub-task 5c: Verify Tests Pass
Run tests and ensure they now pass: `just check-test "path/to/test_file.py"`

**Checkpoint**: All tests should be GREEN before proceeding.

## Task 6: Refactor and Enhance (REFACTOR)

Improve the code while keeping tests passing:

### Sub-task 6a: Extract Helper Methods
```python
def _validate_[input_type](self, input_value: str) -> bool:
    """Validate [input_type] format and constraints."""
    # Extract validation logic into reusable method
    pass

def _format_response(self, data: dict) -> str:
    """Format response data for Discord display."""
    # Extract formatting logic
    pass
```

### Sub-task 6b: Add Integration Tests
```python
@pytest.mark.asyncio
async def test_[command_name]_integration_with_[component](mock_bot):
    """Test [command_name] integrates properly with [component]."""
    # Test actual integration between components
    pass
```

### Sub-task 6c: Add Performance Tests
```python
@pytest.mark.asyncio
async def test_[command_name]_performance(mock_bot):
    """Test [command_name] performs within acceptable limits."""
    import time
    start_time = time.time()

    await dpytest.message("![command_name] test_input")

    end_time = time.time()
    assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
```

## Task 7: Add Advanced Test Scenarios

Enhance test coverage with advanced scenarios:

### Sub-task 7a: Concurrent Usage Tests
```python
@pytest.mark.asyncio
async def test_[command_name]_concurrent_usage(mock_bot):
    """Test [command_name] handles concurrent usage correctly."""
    import asyncio

    # Simulate multiple users using command simultaneously
    tasks = [
        dpytest.message("![command_name] input1"),
        dpytest.message("![command_name] input2"),
        dpytest.message("![command_name] input3")
    ]

    await asyncio.gather(*tasks)

    # Verify all requests handled properly
    messages = dpytest.sent_queue
    assert len(messages) >= 3
```

### Sub-task 7b: Permission Tests
```python
@pytest.mark.asyncio
async def test_[command_name]_permission_handling(mock_bot):
    """Test [command_name] respects Discord permissions."""
    # Test with different permission levels
    admin_member = await dpytest.member_join(permissions=discord.Permissions.all())
    regular_member = await dpytest.member_join()

    # Test admin access
    await dpytest.message("![command_name] test", member=admin_member)
    # Assert admin can use command

    # Test regular user access
    await dpytest.message("![command_name] test", member=regular_member)
    # Assert appropriate response based on permissions
```

### Sub-task 7c: State Management Tests
```python
@pytest.mark.asyncio
async def test_[command_name]_state_management(mock_bot):
    """Test [command_name] manages state correctly across interactions."""
    # Test command maintains proper state between calls
    # Test cleanup after completion
    # Test state isolation between users
    pass
```

## Task 8: Validate Complete TDD Cycle

Final validation of the TDD implementation:

### Sub-task 8a: Run Full Test Suite
```bash
# Run all tests to ensure nothing broke
just ci

# Run specific feature tests
just check-test "tests/test_[feature]/"
```

### Sub-task 8b: Code Quality Check
```bash
# Type checking
just check-type "tests/test_[feature]/"
```

### Sub-task 8c: Integration Verification
- **Test with real bot instance** - Verify command works in actual Discord environment (if possible)
- **Review test isolation** - Ensure tests don't interfere with each other
- **Validate mock accuracy** - Confirm mocks represent real behavior accurately

## Task 9: Document and Review

Complete the TDD cycle with documentation:

### Sub-task 9a: Update Documentation
- **Add to dpytest examples** - Include new test patterns in `docs/contributors/dpytest_example.md`
- **Document command usage** - Add command help and examples
- **Update architecture docs** - Reflect any new patterns or components

### Sub-task 9b: Code Review Checklist
- ✅ All tests pass consistently
- ✅ Code coverage meets project standards (65%+)
- ✅ No external dependencies in tests (all mocked)
- ✅ Proper async/await patterns used
- ✅ Discord permissions properly handled
- ✅ Error cases thoroughly tested
- ✅ Performance acceptable under load
- ✅ Code follows boss-bot conventions

### Sub-task 9c: Prepare for Integration
- **Create feature branch** - Follow git workflow for feature development
- **Test integration points** - Verify feature works with existing system
- **Plan deployment** - Consider feature flags and gradual rollout

## Success Criteria

✅ **RED**: Tests written first and initially fail
✅ **GREEN**: Minimum implementation makes tests pass
✅ **REFACTOR**: Code improved while maintaining test success
✅ **COVERAGE**: Comprehensive test scenarios implemented
✅ **QUALITY**: All code quality checks pass
✅ **DOCUMENTATION**: Feature properly documented

## Example Usage

```bash
# Start TDD cycle for a new download platform
/project:tdd_dpytest "new download command for TikTok platform with URL validation and metadata extraction"

# Add error handling to existing command
/project:tdd_dpytest "enhance download command to handle rate limiting and network timeouts gracefully"

# Test complex interaction patterns
/project:tdd_dpytest "multi-step command workflow for bulk download management with progress tracking"
```

## Project Context

This command leverages the boss-bot project structure:
- **Testing Framework**: pytest + dpytest + pytest-asyncio
- **Bot Architecture**: Discord.py cogs with strategy pattern
- **Coverage Target**: 65%+ test coverage
- **Quality Standards**: Type checking, linting, comprehensive mocking
- **Documentation**: Integration with existing dpytest guide

Generate production-ready, test-driven code that follows TDD principles and boss-bot development standards.
