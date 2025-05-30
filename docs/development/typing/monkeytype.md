# PYTEST.md

A comprehensive guide to using MonkeyType with pytest to automatically generate type annotations for any Python repository.

## Overview

MonkeyType can trace your pytest test runs to collect runtime type information and automatically generate type annotations. This is particularly useful for adding types to existing codebases or discovering type issues.

## Prerequisites

Ensure you have MonkeyType and pytest installed:

```bash
uv add monkeytype pytest
```

## Basic Workflow

### 1. Run Tests with MonkeyType Tracing

Trace your entire test suite to collect type information:

```bash
# Basic tracing
uv run monkeytype run pytest

# Trace with specific pytest options
uv run monkeytype run pytest tests/ -v

# Trace specific test files
uv run monkeytype run pytest tests/test_mymodule.py

# Trace with pytest markers
uv run monkeytype run pytest -m "not slow"
```

This creates a `monkeytype.sqlite3` database file containing type traces.

### 2. Generate Type Stubs

View the collected type information:

```bash
# Generate stub for a specific module
uv run monkeytype stub mymodule

# Generate stub for a package
uv run monkeytype stub mypackage.submodule
```

### 3. Apply Type Annotations

Apply the discovered types directly to your source code:

```bash
# Apply types to a module
uv run monkeytype apply mymodule

# Apply types to multiple modules
uv run monkeytype apply mypackage.module1 mypackage.module2
```

### 4. Verify with Type Checker

Check your newly annotated code:

```bash
# Type check with mypy
uv run mypy .

# Type check specific files
uv run mypy src/mymodule.py
```

## Advanced Usage

### Custom Configuration

Create a `monkeytype_config.py` file in your project root:

```python
from monkeytype.config import DefaultConfig
from monkeytype.db.sqlite import SQLiteStore

class MyConfig(DefaultConfig):
    def trace_store(self):
        return SQLiteStore.make_store("custom_traces.sqlite3")

    def code_filter(self):
        # Only trace your own code, not dependencies
        def filter_fn(code):
            return code.co_filename.startswith('/path/to/your/project')
        return filter_fn
```

Use the custom config:

```bash
uv run monkeytype -c monkeytype_config run pytest
```

### Targeting Specific Code

#### Filter by Module Path
```bash
# Only trace specific modules during test runs
uv run monkeytype run pytest --tb=short
uv run monkeytype stub myapp.models
uv run monkeytype apply myapp.models
```

#### Trace Specific Test Categories
```bash
# Trace only integration tests
uv run monkeytype run pytest tests/integration/

# Trace only unit tests for a component
uv run monkeytype run pytest tests/unit/test_database.py
```

### Working with Test Data

#### Clean Slate Approach
```bash
# Remove old traces
rm monkeytype.sqlite3

# Run comprehensive test suite
uv run monkeytype run pytest --maxfail=1

# Apply all discovered types
uv run monkeytype list-modules | xargs -I {} uv run monkeytype apply {}
```

#### Incremental Approach
```bash
# Add more traces to existing data
uv run monkeytype run pytest tests/new_feature/

# Check what modules have traces
uv run monkeytype list-modules

# Apply types to newly traced modules
uv run monkeytype apply new_feature.handlers
```

## Integration Patterns

### With CI/CD

Create a script to check type coverage:

```bash
#!/bin/bash
# scripts/check_types.sh

# Run tests with tracing
uv run monkeytype run pytest

# Generate stubs for review
for module in $(uv run monkeytype list-modules); do
    echo "=== $module ==="
    uv run monkeytype stub "$module"
done

# Type check current code
uv run mypy . --ignore-missing-imports
```

### With Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: monkeytype-check
        name: MonkeyType type consistency
        entry: bash -c 'uv run monkeytype run pytest && uv run mypy .'
        language: system
        pass_filenames: false
```

### With tox

Add to `tox.ini`:

```ini
[testenv:types]
deps =
    monkeytype
    mypy
    pytest
commands =
    monkeytype run pytest
    mypy src/
```

## Best Practices

### 1. Comprehensive Test Coverage
- Ensure your tests exercise all code paths
- Include edge cases and error conditions
- Test with realistic data types

### 2. Iterative Refinement
```bash
# Initial pass
uv run monkeytype run pytest
uv run monkeytype apply mymodule

# Review and fix issues
uv run mypy mymodule.py

# Re-trace after fixes
rm monkeytype.sqlite3
uv run monkeytype run pytest
uv run monkeytype apply mymodule
```

### 3. Module-by-Module Approach
```bash
# Focus on one module at a time
uv run monkeytype run pytest tests/test_auth.py
uv run monkeytype stub auth
# Review output, then apply
uv run monkeytype apply auth
```

### 4. Handling Complex Types
- Use parametrized tests to capture type variations
- Include tests with different data shapes
- Test both success and failure cases

## Common Issues and Solutions

### Issue: Too Many Generic Types
**Problem**: MonkeyType generates `Any` or overly generic types.

**Solution**: Add more specific test cases:
```python
def test_user_creation_with_various_types():
    # This helps MonkeyType see concrete types
    user1 = create_user(name="John", age=30, active=True)
    user2 = create_user(name="Jane", age=25, active=False)
    assert isinstance(user1.age, int)
```

### Issue: Missing Type Information
**Problem**: Some functions aren't getting traced.

**Solution**: Ensure they're called during tests:
```bash
# Check what was traced
uv run monkeytype list-modules

# Add tests for missing functions
# Re-run tracing
```

### Issue: Conflicting Type Information
**Problem**: Different test runs produce different types.

**Solution**: Clean slate approach:
```bash
rm monkeytype.sqlite3
uv run monkeytype run pytest -x  # Stop on first failure
```

## Example Workflow for New Project

```bash
# 1. Set up environment
uv add monkeytype pytest mypy

# 2. Run existing tests with tracing
uv run monkeytype run pytest

# 3. See what modules were traced
uv run monkeytype list-modules

# 4. Start with core modules
uv run monkeytype stub myapp.models
uv run monkeytype apply myapp.models

# 5. Check for type errors
uv run mypy myapp/models.py

# 6. Fix any issues and repeat
# 7. Continue with other modules
uv run monkeytype apply myapp.handlers
uv run mypy myapp/handlers.py

# 8. Full project type check
uv run mypy .
```

This workflow helps you systematically add type annotations to any Python project using pytest as the execution vehicle for MonkeyType's runtime type collection.
