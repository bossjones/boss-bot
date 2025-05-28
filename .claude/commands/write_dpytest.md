# Write dpytest Discord Bot Test

Generate comprehensive dpytest test code for Discord bot commands and cogs based on the patterns established in `docs/contributors/dpytest_example.md`.

## Usage
`/project:write_dpytest [test_type] [command_name] [options]`

**Arguments:** `$ARGUMENTS`

## Test Types Available:
- `basic` - Basic command test with message simulation
- `cog` - Test an entire Discord cog with mocking
- `direct` - Direct command callback testing without dpytest
- `error` - Error handling and edge case testing
- `fixture` - Generate conftest.py fixtures
- `integration` - Full integration test with bot setup

## Examples:
- `/project:write_dpytest basic ping` - Test a simple ping command
- `/project:write_dpytest cog downloads` - Test the downloads cog
- `/project:write_dpytest error download network_failure` - Test network error handling
- `/project:write_dpytest fixture bot_with_strategies` - Create bot fixture with strategies

## Instructions:

Based on the test type and command specified in `$ARGUMENTS`, generate appropriate dpytest test code following these patterns:

### For Basic Command Tests:
```python
@pytest.mark.asyncio
async def test_[command_name](mock_bot):
    \"\"\"Test [command_name] command.\"\"\"
    await dpytest.message("![command_name]")
    assert dpytest.verify().message().contains().content("expected_response")
```

### For Cog Tests:
- Import the appropriate cog from `boss_bot.bot.cogs`
- Mock external dependencies (download managers, APIs, etc.)
- Test both success and failure scenarios
- Use proper async mocking with `AsyncMock()`

### For Direct Command Tests:
```python
@pytest.mark.asyncio
async def test_[command_name]_callback_direct(ctx_mock):
    \"\"\"Test [command_name] command callback directly.\"\"\"
    cog = CommandCog(mock_bot)
    await cog.[command_name].callback(cog, ctx_mock, *args)
    assert ctx_mock.send.called
```

### For Error Handling Tests:
- Test network failures with `ConnectionError`
- Test invalid inputs and edge cases
- Test permission errors with `discord.Forbidden`
- Use `side_effect` to simulate exceptions

### For Fixtures:
Generate fixtures in conftest.py format with proper:
- `@pytest_asyncio.fixture(scope="function")` decorators
- Mock setup for bot dependencies
- dpytest configuration with `dpytest.configure(bot)`
- Cleanup with `await dpytest.empty_queue()`

## Requirements:
1. Follow the patterns from `docs/contributors/dpytest_example.md`
2. Use proper imports for boss-bot project structure
3. Include comprehensive docstrings
4. Mock external dependencies appropriately
5. Include both success and failure test cases
6. Use appropriate pytest markers (`@pytest.mark.asyncio`)
7. Follow boss-bot naming conventions (fixture_*_test, etc.)

## Project Context:
This is the boss-bot Discord bot project with:
- Main bot class: `BossBot` in `boss_bot.bot.client`
- Settings: `BossSettings` in `boss_bot.core.env`
- Download strategies in `boss_bot.core.downloads.strategies`
- Cogs in `boss_bot.bot.cogs` (downloads, queue, etc.)
- Feature flags: `DownloadFeatureFlags`

Generate production-ready test code that matches the existing codebase patterns and follows dpytest best practices as documented in the guide.
