# """Test to determine which exception handler is registered during pytest execution."""

# import sys
# import inspect
# import pytest


# def test_print_exception_handler():
#     """Print information about the current exception handler during pytest."""
#     current_hook = sys.excepthook
#     original_hook = sys.__excepthook__

#     print("\n" + "=" * 60)
#     print("PYTEST EXCEPTION HANDLER ANALYSIS")
#     print("=" * 60)

#     # Current exception hook
#     print("\nCurrent Exception Hook:")
#     print(f"  Function: {current_hook}")
#     print(f"  Module: {getattr(current_hook, '__module__', 'N/A')}")
#     print(f"  Name: {getattr(current_hook, '__name__', 'N/A')}")
#     print(f"  Qualname: {getattr(current_hook, '__qualname__', 'N/A')}")

#     # Original exception hook
#     print("\nOriginal Exception Hook:")
#     print(f"  Function: {original_hook}")
#     print(f"  Module: {getattr(original_hook, '__module__', 'N/A')}")
#     print(f"  Name: {getattr(original_hook, '__name__', 'N/A')}")

#     # Check if hooks are modified
#     is_modified = current_hook != original_hook
#     print(f"\nHook Modified: {is_modified}")

#     # Try to get source code
#     if is_modified and hasattr(current_hook, '__code__'):
#         try:
#             source = inspect.getsource(current_hook)
#             print(f"\nException Hook Source (first 500 chars):")
#             print("-" * 40)
#             print(source[:500] + "..." if len(source) > 500 else source)
#         except (OSError, TypeError) as e:
#             print(f"\nCould not retrieve source: {e}")

#     # Check for common exception libraries
#     print("\nException Library Detection:")

#     # Check for better-exceptions
#     try:
#         import better_exceptions
#         print(f"  better-exceptions: INSTALLED (v{getattr(better_exceptions, '__version__', 'unknown')})")
#         if hasattr(better_exceptions, 'hook'):
#             print(f"    Hook match: {current_hook == better_exceptions.hook}")
#     except ImportError:
#         print("  better-exceptions: NOT INSTALLED")

#     # Check for rich
#     try:
#         import rich
#         print(f"  rich: INSTALLED (v{getattr(rich, '__version__', 'unknown')})")
#         import rich.traceback
#         print(f"    rich.traceback available: True")
#     except ImportError:
#         print("  rich: NOT INSTALLED")

#     # Check for pytest's own exception handling
#     try:
#         import _pytest.debugging
#         if hasattr(_pytest.debugging, 'pytestPDB'):
#             print(f"  pytest debugging: AVAILABLE")
#     except ImportError:
#         pass

#     # Check for pytest-timeout
#     try:
#         import pytest_timeout
#         print(f"  pytest-timeout: INSTALLED")
#     except ImportError:
#         print("  pytest-timeout: NOT INSTALLED")

#     print("=" * 60)

#     # Always pass the test
#     assert True


# def test_exception_handler_with_actual_exception():
#     """Test what happens when an actual exception occurs."""
#     print("\n" + "=" * 60)
#     print("TESTING ACTUAL EXCEPTION HANDLING")
#     print("=" * 60)

#     # Capture the exception handler before the exception
#     pre_exception_hook = sys.excepthook
#     print(f"Pre-exception hook: {pre_exception_hook}")

#     # This will be caught by pytest, but we can see what happens
#     with pytest.raises(ValueError):
#         raise ValueError("Test exception to see handler behavior")

#     # Check if hook changed after exception
#     post_exception_hook = sys.excepthook
#     print(f"Post-exception hook: {post_exception_hook}")
#     print(f"Hook changed: {pre_exception_hook != post_exception_hook}")


# @pytest.fixture(scope="session", autouse=True)
# def report_session_exception_handler():
#     """Report exception handler at session start."""
#     print("\n" + "=" * 60)
#     print("PYTEST SESSION START - EXCEPTION HANDLER")
#     print("=" * 60)
#     print(f"sys.excepthook: {sys.excepthook}")
#     print(f"Module: {getattr(sys.excepthook, '__module__', 'N/A')}")
#     print(f"Name: {getattr(sys.excepthook, '__name__', 'N/A')}")
#     yield
#     print("\n" + "=" * 60)
#     print("PYTEST SESSION END - EXCEPTION HANDLER")
#     print("=" * 60)
#     print(f"sys.excepthook: {sys.excepthook}")
