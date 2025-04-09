# Pytest Fixtures Recommended State - Class Diagram

## Overview
Shows the recommended state of pytest fixtures after consolidation and proper organization.

## Source
Based on analysis of current fixtures in:
- tests/conftest.py
- tests/test_bot/test_help.py
- tests/test_bot/test_download_cog.py
- tests/test_downloaders/test_base.py
- tests/test_core/test_queue_manager.py
- tests/test_bot/test_cogs/test_downloads.py

## Diagram
```mermaid
classDiagram
    class Fixture {
        <<interface>>
        +name: str
        +scope: str
        +file: str
    }

    class bot {
        +scope: function
        +file: conftest.py
        +description: "Test bot instance with mocked Discord.py methods"
        +is_mock: bool
        +configure_mock()
    }

    class ctx {
        +scope: function
        +file: conftest.py
        +description: "Mock Discord context for testing"
        +bot: Bot
    }

    class queue_manager {
        +scope: function
        +file: conftest.py
        +description: "Test queue manager instance"
        +reset_state()
    }

    class download_manager {
        +scope: function
        +file: conftest.py
        +description: "Test download manager instance"
        +reset_state()
    }

    class help_command {
        +scope: function
        +file: conftest.py
        +description: "Help command instance for testing"
        +bot: Bot
    }

    class cog {
        +scope: function
        +file: conftest.py
        +description: "Downloads cog instance for testing"
        +bot: Bot
        +download_manager: DownloadManager
    }

    class mock_env_vars {
        +scope: function
        +file: conftest.py
        +description: "Mock environment variables"
    }

    class mock_settings {
        +scope: function
        +file: conftest.py
        +description: "Standardized test settings"
    }

    Fixture <|-- bot
    Fixture <|-- ctx
    Fixture <|-- queue_manager
    Fixture <|-- download_manager
    Fixture <|-- help_command
    Fixture <|-- cog
    Fixture <|-- mock_env_vars
    Fixture <|-- mock_settings

    bot <-- ctx : uses
    bot <-- help_command : uses
    bot <-- cog : uses
    download_manager <-- cog : uses
    mock_settings <-- bot : configures
    mock_env_vars <-- mock_settings : uses

    note for bot "Consolidated bot fixture with mock configuration"
    note for queue_manager "Single source of truth in conftest.py"
    note for download_manager "Single source of truth in conftest.py"
```

## Notes
1. Key improvements:
   - All fixtures consolidated in conftest.py
   - Clear dependency hierarchy
   - Consistent mocking strategy
   - State management with reset methods
   - Proper scope isolation

2. Implementation recommendations:
   - Move all fixture definitions to conftest.py
   - Add reset_state() methods to stateful fixtures
   - Use bot.is_mock flag to control mock behavior
   - Ensure proper cleanup between tests
   - Document fixture dependencies clearly

3. Migration steps:
   - Delete duplicate fixtures from individual test files
   - Update tests to use consolidated fixtures
   - Add proper teardown/cleanup in conftest.py
   - Add type hints and docstrings to all fixtures
