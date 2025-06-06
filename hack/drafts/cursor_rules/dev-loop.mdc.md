---
description:
globs:
alwaysApply: false
---

# Development Process (QA every edit)

## Project Stack

The project uses the following tools and technologies:

- **uv** - Python package management and virtual environments
- **ruff** - Fast Python linter and formatter
- **py.test** - Testing framework
  - **pytest-watcher** - Continuous test runner
- **mypy** - Static type checking
- **doctest** - Testing code examples in documentation

## 1. Start with Formatting

Format your code first:

```
uv run ruff format .
```

## 2. Run Tests

Verify that your changes pass the tests:

```
uv run py.test
```

For continuous testing during development, use pytest-watcher:

```
# Watch all tests
uv run ptw .

# Watch and run tests immediately, including doctests
uv run ptw . --now --doctest-modules

# Watch specific files or directories
uv run ptw . --now --doctest-modules src/libtmux/_internal/
```

## 3. Commit Initial Changes

Make an atomic commit for your changes using conventional commits.
Use `@git-commits.mdc` for assistance with commit message standards.

## 4. Run Linting and Type Checking

Check and fix linting issues:

```
uv run ruff check . --fix --show-fixes
```

Check typings:

```
uv run mypy
```

## 5. Verify Tests Again

Ensure tests still pass after linting and type fixes:

```
uv run py.test
```

## 6. Final Commit

Make a final commit with any linting/typing fixes.
Use `@git-commits.mdc` for assistance with commit message standards.

## Development Loop Guidelines

If there are any failures at any step due to your edits, fix them before proceeding to the next step.

## Python Code Standards

### Docstring Guidelines

For `src/**/*.py` files, follow these docstring guidelines:

1. **Use reStructuredText format** for all docstrings.
   ```python
   """Short description of the function or class.

   Detailed description using reStructuredText format.

   Parameters
   ----------
   param1 : type
       Description of param1
   param2 : type
       Description of param2

   Returns
   -------
   type
       Description of return value
   """
   ```

2. **Keep the main description on the first line** after the opening `"""`.

3. **Use NumPy docstyle** for parameter and return value documentation.

### Doctest Guidelines

For doctests in `src/**/*.py` files:

1. **Use narrative descriptions** for test sections rather than inline comments:
   ```python
   """Example function.

   Examples
   --------
   Create an instance:

   >>> obj = ExampleClass()

   Verify a property:

   >>> obj.property
   'expected value'
   """
   ```

2. **Move complex examples** to dedicated test files at `tests/examples/<path_to_module>/test_<example>.py` if they require elaborate setup or multiple steps.

3. **Utilize pytest fixtures** via `doctest_namespace` for more complex test scenarios:
   ```python
   """Example with fixture.

   Examples
   --------
   >>> # doctest_namespace contains all pytest fixtures from conftest.py
   >>> example_fixture = getfixture('example_fixture')
   >>> example_fixture.method()
   'expected result'
   """
   ```

4. **Keep doctests simple and focused** on demonstrating usage rather than comprehensive testing.

5. **Add blank lines between test sections** for improved readability.

6. **Test your doctests continuously** using pytest-watcher during development:
   ```
   # Watch specific modules for doctest changes
   uv run ptw . --now --doctest-modules src/path/to/module.py
   ```

### Pytest Testing Guidelines

1. **Use existing fixtures over mocks**:
   - Use fixtures from conftest.py instead of `monkeypatch` and `MagicMock` when available
   - For instance, if using libtmux, use provided fixtures: `server`, `session`, `window`, and `pane`
   - Document in test docstrings why standard fixtures weren't used for exceptional cases

2. **Preferred pytest patterns**:
   - Use `tmp_path` (pathlib.Path) fixture over Python's `tempfile`
   - Use `monkeypatch` fixture over `unittest.mock`

### Import Guidelines

1. **Prefer namespace imports**:
   - Import modules and access attributes through the namespace instead of importing specific symbols
   - Example: Use `import enum` and access `enum.Enum` instead of `from enum import Enum`
   - This applies to standard library modules like `pathlib`, `os`, and similar cases

2. **Standard aliases**:
   - For `typing` module, use `import typing as t`
   - Access typing elements via the namespace: `t.NamedTuple`, `t.TypedDict`, etc.
   - Note primitive types like unions can be done via `|` pipes and primitive types like list and dict can be done via `list` and `dict` directly.

3. **Benefits of namespace imports**:
   - Improves code readability by making the source of symbols clear
   - Reduces potential naming conflicts
   - Makes import statements more maintainable
