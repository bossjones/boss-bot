#!/usr/bin/env python3
"""Example usage of LangGraph Assistant Client.

This script demonstrates how to use the LangGraphAssistantClient
for managing assistants programmatically.

Run with: uv run python examples/assistant_client_example.py
"""

import asyncio
import tempfile
from pathlib import Path

from boss_bot.ai.assistants import (
    LangGraphAssistantClient,
    LangGraphClientConfig,
    create_assistant_client,
)
from boss_bot.ai.assistants.models import create_default_assistant_config
from boss_bot.core.env import BossSettings


async def example_basic_usage():
    """Demonstrate basic client usage."""
    print("🤖 LangGraph Assistant Client Example")
    print("=" * 50)

    # Example 1: Create client with default settings
    print("\n1. Creating client with default settings...")
    try:
        async with LangGraphAssistantClient() as client:
            print(f"   ✓ Connected to: {client.config.deployment_url}")

            # Test health check
            is_healthy = await client.health_check()
            print(f"   ✓ Health check: {'Passed' if is_healthy else 'Failed'}")

    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("   💡 This is expected if LangGraph Cloud is not running locally")


async def example_config_management():
    """Demonstrate configuration management."""
    print("\n2. Configuration Management...")

    # Create a temporary directory for configs
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)

        # Create sample assistant configurations
        configs = [
            create_default_assistant_config(
                name="Download Assistant",
                description="AI-powered download strategy selector",
                graph_id="download_workflow",
                ai={"ai_model": "gpt-4", "ai_temperature": 0.3}
            ),
            create_default_assistant_config(
                name="Content Analyzer",
                description="Intelligent content analysis and quality assessment",
                graph_id="content_analysis_workflow",
                ai={"ai_model": "claude-3", "ai_temperature": 0.2}
            ),
        ]

        # Save configurations to YAML files
        for config in configs:
            safe_name = "".join(c for c in config.name if c.isalnum() or c in "-_").lower()
            config_file = config_dir / f"{safe_name}.yaml"
            config.to_yaml_file(config_file)
            print(f"   ✓ Created config: {config_file}")

        # Load configurations back
        from boss_bot.ai.assistants.models import load_assistant_configs
        loaded_configs = load_assistant_configs(config_dir)
        print(f"   ✓ Loaded {len(loaded_configs)} configurations")

        for config in loaded_configs:
            print(f"     - {config.name}: {config.description}")


async def example_sync_operations():
    """Demonstrate synchronization operations."""
    print("\n3. Synchronization Operations...")

    # Create a client with custom configuration
    client_config = LangGraphClientConfig(
        deployment_url="http://localhost:8000",
        timeout_seconds=30,
        max_retries=2,
    )

    try:
        async with LangGraphAssistantClient(config=client_config) as client:
            print(f"   ✓ Client configured for: {client.config.deployment_url}")

            # Example sync operations (would work with real LangGraph Cloud)
            print("   📋 Sync operations available:")
            print("     - sync_from_yaml(): Upload local configs to cloud")
            print("     - sync_to_yaml(): Download cloud configs to local")
            print("     - create_assistant(): Create new assistant")
            print("     - update_assistant(): Update existing assistant")
            print("     - delete_assistant(): Remove assistant")

    except Exception as e:
        print(f"   ✗ Sync demo failed: {e}")
        print("   💡 This is expected without a running LangGraph Cloud instance")


async def example_helper_functions():
    """Demonstrate helper functions."""
    print("\n4. Helper Functions...")

    # Using helper functions for common operations
    from boss_bot.ai.assistants import export_assistants_to_directory, sync_assistants_from_directory

    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)

        # Create a sample config
        config = create_default_assistant_config(
            name="Helper Example",
            description="Example using helper functions",
        )
        config.to_yaml_file(config_dir / "helper_example.yaml")

        print(f"   ✓ Created example config in: {config_dir}")
        print("   📋 Helper functions available:")
        print("     - sync_assistants_from_directory()")
        print("     - export_assistants_to_directory()")
        print("     - create_assistant_client()")


async def example_environment_integration():
    """Demonstrate environment variable integration."""
    print("\n5. Environment Integration...")

    # Show how client uses environment settings
    settings = BossSettings()

    print("   🔧 Environment Settings:")
    print(f"     - LangGraph URL: {getattr(settings, 'langgraph_deployment_url', 'Not set')}")
    print(f"     - LangChain Endpoint: {getattr(settings, 'langchain_endpoint', 'Not set')}")
    print(f"     - Tracing Enabled: {getattr(settings, 'langchain_tracing_v2', 'Not set')}")

    print("   💡 Set LANGGRAPH_DEPLOYMENT_URL to customize deployment URL")
    print("   💡 Set LANGGRAPH_API_KEY for authentication")


async def main():
    """Run all examples."""
    try:
        await example_basic_usage()
        await example_config_management()
        await example_sync_operations()
        await example_helper_functions()
        await example_environment_integration()

        print("\n" + "=" * 50)
        print("🎉 All examples completed successfully!")
        print("\n📚 Next Steps:")
        print("   1. Set up LangGraph Cloud deployment")
        print("   2. Configure environment variables")
        print("   3. Create and deploy your assistants")
        print("   4. Use CLI commands: uv run python -m boss_bot.cli assistants --help")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
