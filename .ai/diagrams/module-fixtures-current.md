# Pytest Fixtures Current State - Class Diagram

## Overview
Shows the current state of pytest fixtures in the project, highlighting duplications and potential conflicts.

## Source
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
    }

    class bot_duplicate {
        +scope: function
        +file: test_download_cog.py
        +description: "Create a bot instance for testing"
    }

    class mock_bot {
        +scope: function
        +file: test_downloads.py
        +description: "Create a mocked bot instance"
    }

    class ctx {
        +scope: function
        +file: conftest.py
        +description: "Mock Discord context for testing"
    }

    class queue_manager {
        +scope: function
        +file: conftest.py
        +description: "Test queue manager instance"
    }

    class queue_manager_duplicate {
        +scope: function
        +file: test_queue_manager.py
        +description: "Create a queue manager instance for testing"
    }

    class download_manager {
        +scope: function
        +file: conftest.py
        +description: "Test download manager instance"
    }

    class download_manager_duplicate {
        +scope: function
        +file: test_base.py
        +description: "Create a download manager instance for testing"
    }

    class help_command {
        +scope: function
        +file: test_help.py
        +description: "Help command instance for testing"
    }

    class cog {
        +scope: function
        +file: test_downloads.py
        +description: "Downloads cog instance for testing"
    }

    Fixture <|-- bot
    Fixture <|-- bot_duplicate
    Fixture <|-- mock_bot
    Fixture <|-- ctx
    Fixture <|-- queue_manager
    Fixture <|-- queue_manager_duplicate
    Fixture <|-- download_manager
    Fixture <|-- download_manager_duplicate
    Fixture <|-- help_command
    Fixture <|-- cog

    bot <-- help_command : depends on
    bot <-- ctx : depends on
    mock_bot <-- cog : depends on
    bot .. bot_duplicate : conflicts with
    bot .. mock_bot : similar to
    queue_manager .. queue_manager_duplicate : conflicts with
    download_manager .. download_manager_duplicate : conflicts with
```

## Notes
1. Red flags identified:
   - `bot` fixture is duplicated in test_download_cog.py
   - `queue_manager` fixture is duplicated in test_queue_manager.py
   - `download_manager` fixture is duplicated in test_base.py
   - `mock_bot` is similar to `bot` but with a different name
2. Potential issues:
   - Inconsistent fixture behavior across tests
   - Risk of fixture state bleeding between tests
   - Maintenance overhead from duplicate code
   - Unclear which fixture version should be used
