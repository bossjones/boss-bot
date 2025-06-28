# Configuration Options & Usage Examples

This memory file contains all configuration options and usage examples for Boss-Bot.

**When to include this context:**
- When helping users configure the bot
- When explaining environment variables
- When demonstrating bot usage (Discord or CLI)
- When troubleshooting configuration issues
- When documenting new configuration options

## Configuration Options & Usage Examples

### Environment Variables for Strategy & AI Control
Control download strategy and AI behavior using these environment variables:

```bash
# Download Strategy Feature Flags - Enable API-direct mode per platform
export TWITTER_USE_API_CLIENT=true          # Enable API-direct for Twitter/X
export REDDIT_USE_API_CLIENT=true           # Enable API-direct for Reddit
export INSTAGRAM_USE_API_CLIENT=true        # Enable API-direct for Instagram
export YOUTUBE_USE_API_CLIENT=true          # Enable API-direct for YouTube

# AI Enhancement Feature Flags - Enable AI capabilities (NEW!)
export AI_STRATEGY_SELECTION_ENABLED=true   # Enable AI-powered strategy selection
export AI_CONTENT_ANALYSIS_ENABLED=true     # Enable AI content analysis and insights
export AI_WORKFLOW_ORCHESTRATION_ENABLED=true  # Enable LangGraph workflow coordination

# LLM Model Provider Configuration (choose one)
export OPENAI_API_KEY="your-openai-api-key"        # For GPT-4, GPT-3.5 models
export ANTHROPIC_API_KEY="your-anthropic-api-key"  # For Claude models
export GOOGLE_API_KEY="your-google-api-key"        # For Gemini models

# Fallback Control
export DOWNLOAD_API_FALLBACK_TO_CLI=true    # Auto-fallback to CLI on API errors (recommended)

# Download Configuration
export BOSS_BOT_DOWNLOAD_DIR="./downloads"  # Download directory (default: .downloads/)
```

### Discord Bot Usage
The Discord bot now includes AI-powered commands alongside traditional functionality:

#### **Traditional Commands (Enhanced with AI when enabled)**
```bash
# Basic download command (now uses AI strategy selection when enabled)
$download https://twitter.com/user/status/123456789

# Get metadata without downloading (enhanced with AI insights when enabled)
$metadata https://reddit.com/r/pics/comments/abc123/title/

# Check current strategy & AI configuration
$strategies

# View download status
$status
```

#### **NEW: AI-Powered Commands** 🤖
```bash
# AI-powered content analysis with advanced insights
$smart-analyze https://twitter.com/user/status/123456789
$smart-analyze https://youtube.com/watch?v=VIDEO_ID

# AI-enhanced download with strategy optimization
$smart-download https://twitter.com/user/status/123456789
$smart-download https://youtube.com/watch?v=VIDEO_ID false

# Show AI agent status and performance metrics
$ai-status
```

#### **Enhanced Commands with AI Integration**
```bash
# Download with AI strategy selection (when AI enabled)
$download https://instagram.com/p/POST_ID/
# Shows: "🤖 AI selected Instagram strategy (confidence: 95%)"

# Metadata with AI content analysis (when AI enabled)
$metadata https://youtube.com/watch?v=VIDEO_ID
# Shows: "📊 AI Enhanced Content Info" with quality scores and insights
```

### CLI Usage Examples
The CLI commands now use the strategy pattern with enhanced features:

```bash
# Twitter/X downloads with strategy pattern
bossctl download twitter https://twitter.com/user/status/123456789
bossctl download twitter https://x.com/user --metadata-only

# Reddit downloads with config support
bossctl download reddit https://reddit.com/r/pics/comments/abc123/title/
bossctl download reddit <url> --cookies cookies.txt --config custom.json

# Instagram downloads with experimental features
bossctl download instagram https://instagram.com/p/ABC123/
bossctl download instagram <url> --cookies-browser Chrome --user-agent "Custom Agent"

# YouTube downloads with quality control
bossctl download youtube https://youtube.com/watch?v=VIDEO_ID --quality 720p
bossctl download youtube <url> --audio-only

# Show strategy configuration
bossctl download strategies

# Show platform info
bossctl download info
```

### Strategy Status Messages
Both Discord and CLI interfaces show the current strategy mode:

- 🚀 **API-Direct Mode**: Using experimental direct API integration
- 🖥️ **CLI Mode**: Using stable subprocess-based approach (default)
- 🔄 **Auto-Fallback**: API failures automatically fallback to CLI when enabled

### Gradual Rollout Configuration
Enable experimental features gradually per platform:

```bash
# Conservative rollout - Enable one platform at a time
export TWITTER_USE_API_CLIENT=true
export DOWNLOAD_API_FALLBACK_TO_CLI=true

# Aggressive rollout - Enable all platforms
export TWITTER_USE_API_CLIENT=true
export REDDIT_USE_API_CLIENT=true
export INSTAGRAM_USE_API_CLIENT=true
export YOUTUBE_USE_API_CLIENT=true
export DOWNLOAD_API_FALLBACK_TO_CLI=false  # No fallback for testing
```

### Configuration Validation
The system validates configuration at startup:

```python
from boss_bot.core.env import BossSettings
from boss_bot.core.downloads.feature_flags import DownloadFeatureFlags

# Settings are validated via Pydantic
settings = BossSettings()
feature_flags = DownloadFeatureFlags(settings)

# Check strategy status
info = feature_flags.get_strategy_info()
print(f"Twitter API enabled: {info['twitter_api']}")
print(f"AI strategy selection enabled: {info['ai_strategy_selection']}")
print(f"AI content analysis enabled: {info['ai_content_analysis']}")
```
