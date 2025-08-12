#!/bin/bash

# MCP Server Rename Script
# Removes servers with long names and re-adds them with shorter names
# to prevent potential 64-character tool name limit issues
# Compatible with bash 3.x (macOS default)

# Parse command line arguments
DRY_RUN=false
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    echo "MCP Server Rename Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be changed without making actual changes"
    echo "  -h, --help   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run    # Preview changes without executing"
    echo "  $0              # Execute the rename operation"
    exit 0
fi

# Set mode messaging
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN MODE - No changes will be made"
    MODE_PREFIX="[DRY RUN]"
else
    echo "🔧 EXECUTION MODE - Changes will be applied"
    MODE_PREFIX=""
fi

echo ""
echo "$MODE_PREFIX Starting MCP Server Rename Process..."

# Define servers to rename using parallel arrays (bash 3.x compatible)
ORIGINAL_NAMES=(
    "mcp-server-langgraph-supervisor-py"
    "mcp-server-langchain-postgres"
    "mcp-server-social-media-agent"
    "mcp-server-better-exceptions"
    "mcp-server-pytest-recording"
    "mcp-server-pydantic-settings"
    "mcp-server-langgraph-builder"
    "mcp-server-langgraph-gen-py"
    "mcp-server-langgraph-swarm-py"
    "mcp-server-democracy-exe"
    "mcp-server-langchain-google"
    "mcp-server-langsmith-sdk"
)

NEW_NAMES=(
    "langgraph-supervisor"
    "langchain-postgres"
    "social-media"
    "better-exceptions"
    "pytest-recording"
    "pydantic-settings"
    "langgraph-builder"
    "langgraph-gen"
    "langgraph-swarm"
    "democracy-exe"
    "langchain-google"
    "langsmith-sdk"
)

SERVER_URLS=(
    "https://gitmcp.io/langchain-ai/langgraph-supervisor-py"
    "https://gitmcp.io/langchain-ai/langchain-postgres"
    "https://gitmcp.io/langchain-ai/social-media-agent"
    "https://gitmcp.io/Qix-/better-exceptions"
    "https://gitmcp.io/kiwicom/pytest-recording"
    "https://gitmcp.io/pydantic/pydantic-settings"
    "https://gitmcp.io/langchain-ai/langgraph-builder"
    "https://gitmcp.io/langchain-ai/langgraph-gen-py"
    "https://gitmcp.io/langchain-ai/langgraph-swarm-py"
    "https://gitmcp.io/bossjones/democracy-exe"
    "https://gitmcp.io/langchain-ai/langchain-google"
    "https://gitmcp.io/langchain-ai/langsmith-sdk"
)

# Function to calculate tool name length
calculate_max_tool_length() {
    local server_name="$1"
    local longest_tool="search_documentation"  # 20 chars - longest regular GitMCP tool
    local full_name="mcp__${server_name}__${longest_tool}"
    echo ${#full_name}
}

# Function to check if server exists
server_exists() {
    local server_name="$1"
    claude mcp list 2>/dev/null | grep -q "^$server_name:"
    return $?
}

# Function to remove a server
remove_server() {
    local server_name="$1"

    if [ "$DRY_RUN" = true ]; then
        if server_exists "$server_name"; then
            echo "  🗑️  [DRY RUN] Would remove: $server_name ✅ (currently exists)"
            echo "    💭 Command: claude mcp remove \"$server_name\""
        else
            echo "  🗑️  [DRY RUN] Would skip: $server_name ⚠️  (doesn't exist)"
        fi
    else
        echo "  🗑️  Removing: $server_name"
        claude mcp remove "$server_name" 2>/dev/null || echo "    ⚠️  Server $server_name not found (may already be removed)"
    fi
}

# Function to add a server
add_server() {
    local server_name="$1"
    local url="$2"
    local max_length=$(calculate_max_tool_length "$server_name")

    if [ "$DRY_RUN" = true ]; then
        echo "  ➕ [DRY RUN] Would add: $server_name (max tool length: $max_length chars)"
        echo "    💭 Command: claude mcp add \"$server_name\" -s user -- npx -y mcp-remote@v0.1.9 \"$url\" --debug"
        if server_exists "$server_name"; then
            echo "    ⚠️  Warning: Server with this name already exists!"
        fi
    else
        echo "  ➕ Adding: $server_name (max tool length: $max_length chars)"
        claude mcp add "$server_name" -s user -- npx -y mcp-remote@v0.1.9 "$url" --debug

        if [ $? -eq 0 ]; then
            echo "    ✅ Successfully added: $server_name"
        else
            echo "    ❌ Failed to add: $server_name"
        fi
    fi
}

echo ""
echo "📊 Server name length analysis:"

# Check that arrays have same length
if [ ${#ORIGINAL_NAMES[@]} -ne ${#NEW_NAMES[@]} ] || [ ${#ORIGINAL_NAMES[@]} -ne ${#SERVER_URLS[@]} ]; then
    echo "❌ Error: Array length mismatch in script configuration"
    exit 1
fi

# Iterate through arrays using indices
for i in "${!ORIGINAL_NAMES[@]}"; do
    original_name="${ORIGINAL_NAMES[$i]}"
    new_name="${NEW_NAMES[$i]}"

    max_length=$(calculate_max_tool_length "$original_name")
    new_max_length=$(calculate_max_tool_length "$new_name")

    # Check if servers exist
    original_exists=""
    new_exists=""
    if server_exists "$original_name"; then
        original_exists=" ✅"
    else
        original_exists=" ❌"
    fi

    if server_exists "$new_name"; then
        new_exists=" ⚠️ (already exists!)"
    else
        new_exists=""
    fi

    echo "  $original_name$original_exists: $max_length chars → $new_name$new_exists: $new_max_length chars (saves $((max_length - new_max_length)) chars)"
done

echo ""
echo "🔍 Current MCP server status check:"
echo "  Running: claude mcp list"
echo ""

# Show current MCP servers (limited output)
if command -v claude >/dev/null 2>&1; then
    echo "📋 Currently configured MCP servers:"
    claude mcp list 2>/dev/null | head -20

    total_servers=$(claude mcp list 2>/dev/null | wc -l)
    if [ "$total_servers" -gt 20 ]; then
        echo "  ... and $((total_servers - 20)) more servers"
    fi
else
    echo "⚠️  Claude command not found. Make sure Claude Code is installed and in your PATH."
    echo "   You may need to install it or add it to your PATH first."
fi

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN: Here's what would happen..."
else
    read -p "🤔 Do you want to proceed with renaming these servers? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Operation cancelled"
        echo ""
        echo "💡 Tip: Run with --dry-run to see what would change without making modifications"
        exit 1
    fi
fi

echo ""
echo "$MODE_PREFIX Processing server renames..."

# Remove old servers
echo ""
echo "1️⃣ $MODE_PREFIX Removing old servers with long names..."
for i in "${!ORIGINAL_NAMES[@]}"; do
    original_name="${ORIGINAL_NAMES[$i]}"
    remove_server "$original_name"
done

echo ""
echo "2️⃣ $MODE_PREFIX Adding servers with shortened names..."

# Add new servers with short names
for i in "${!ORIGINAL_NAMES[@]}"; do
    new_name="${NEW_NAMES[$i]}"
    url="${SERVER_URLS[$i]}"
    add_server "$new_name" "$url"
done

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN completed - no actual changes were made!"
else
    echo "✅ Server rename process completed!"
fi

echo ""
echo "📋 Summary of changes:"
echo "┌─────────────────────────────────────┬─────────────────────────┬─────────────┬──────────┐"
echo "│ Original Name                       │ New Name                │ Max Length  │ Status   │"
echo "├─────────────────────────────────────┼─────────────────────────┼─────────────┼──────────┤"

for i in "${!ORIGINAL_NAMES[@]}"; do
    original_name="${ORIGINAL_NAMES[$i]}"
    new_name="${NEW_NAMES[$i]}"
    new_max_length=$(calculate_max_tool_length "$new_name")

    # Determine status
    status=""
    if [ "$DRY_RUN" = true ]; then
        if server_exists "$original_name"; then
            if server_exists "$new_name"; then
                status="⚠️ Conflict"
            else
                status="✅ Ready"
            fi
        else
            status="❌ Missing"
        fi
    else
        status="✅ Done"
    fi

    printf "│ %-35s │ %-23s │ %-11s │ %-8s │\n" "$original_name" "$new_name" "${new_max_length} chars" "$status"
done

echo "└─────────────────────────────────────┴─────────────────────────┴─────────────┴──────────┘"

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "🎯 To execute these changes:"
    echo "  Run this script again without --dry-run flag:"
    echo "  $0"
    echo ""
    echo "⚠️  Status Legend:"
    echo "  ✅ Ready    - Original server exists, new name available"
    echo "  ⚠️ Conflict - New server name already exists (will need manual resolution)"
    echo "  ❌ Missing  - Original server doesn't exist (nothing to rename)"
else
    echo "🎯 Next steps:"
    echo "  1. Run 'claude mcp list' to verify the changes"
    echo "  2. Test your renamed servers with Claude Code"
    echo "  3. Update any scripts or documentation that reference the old server names"
fi

echo ""
echo "💡 Character savings example:"
echo "  Old: mcp__mcp-server-langgraph-supervisor-py__search_documentation (62 chars)"
echo "  New: mcp__langgraph-supervisor__search_documentation (44 chars)"
echo "  Savings: 18 characters per tool call!"

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN completed successfully! No changes were made. 👀"
else
    echo "🔧 Script completed successfully! 🎉"
fi
