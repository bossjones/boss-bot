#!/usr/bin/env python3
"""
Migration health check script.
Run after each migration phase to verify system integrity.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=True
    )
    return result.returncode, result.stdout, result.stderr

def check_imports() -> dict[str, bool]:
    """Check critical imports work."""
    imports_to_test = [
        "boss_bot",
        "boss_bot.bot.client",
        "boss_bot.core.env",
        "boss_bot.core.queue.manager",
        "boss_bot.cli.main",
        "boss_bot.core.downloads.manager",
        "boss_bot.storage.managers.quota_manager",
        "boss_bot.monitoring.health.checker",
    ]

    results = {}
    for import_path in imports_to_test:
        code = f"import {import_path}"
        exit_code, _, _ = run_command(f"uv run python -c \"{code}\"")
        results[import_path] = exit_code == 0

    return results

def check_deprecation_warnings() -> dict[str, bool]:
    """Check that deprecated import paths show proper warnings."""
    deprecated_imports = [
        "boss_bot.core.core_queue",
        "boss_bot.downloaders.base",
        "boss_bot.storage.quotas_manager",
        "boss_bot.monitoring.health_check",
    ]

    results = {}
    for import_path in deprecated_imports:
        # Use -W error::DeprecationWarning to convert warnings to errors
        code = f"import {import_path}"
        exit_code, stdout, stderr = run_command(f"uv run python -W error::DeprecationWarning -c \"{code}\"")
        # Should fail (exit_code != 0) due to deprecation warning being treated as error
        results[import_path] = exit_code != 0

    return results

def check_tests() -> bool:
    """Check that tests pass."""
    exit_code, _, _ = run_command("uv run pytest tests/ -x")  # -x stops on first failure
    return exit_code == 0

def check_cli() -> bool:
    """Check CLI functionality."""
    exit_code, _, _ = run_command("uv run python -m boss_bot version")
    return exit_code == 0

def main():
    """Run all health checks."""
    print("Running migration health checks...")

    # Check imports
    print("\n1. Testing imports...")
    import_results = check_imports()
    for import_path, success in import_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {import_path}")

    # Check deprecation warnings
    print("\n2. Testing deprecation warnings...")
    deprecation_results = check_deprecation_warnings()
    for import_path, shows_warning in deprecation_results.items():
        status = "✅" if shows_warning else "❌"
        print(f"  {status} {import_path} (deprecated)")

    # Check tests
    print("\n3. Testing test suite...")
    tests_pass = check_tests()
    status = "✅" if tests_pass else "❌"
    print(f"  {status} Test suite")

    # Check CLI
    print("\n4. Testing CLI...")
    cli_works = check_cli()
    status = "✅" if cli_works else "❌"
    print(f"  {status} CLI functionality")

    # Summary
    all_good = (all(import_results.values()) and
                all(deprecation_results.values()) and
                tests_pass and cli_works)
    print("\n" + "="*50)
    if all_good:
        print("✅ All health checks passed!")
        print("✅ Phase 1 migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
