# Smoke testing commands

# Run bot smoke test for 30 seconds
[group('smoke-test')]
smoke-test:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🚀 Starting bot smoke test (30 seconds)..."
    if timeout 30s uv run bossctl go; then
        echo "✅ Bot exited cleanly within 30 seconds"
        exit 0
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo "✅ Smoke test completed - bot ran for 30 seconds and was terminated"
            exit 0
        else
            echo "❌ Bot failed with exit code: $exit_code"
            exit $exit_code
        fi
    fi
