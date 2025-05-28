# BossBot CLI (bossctl) Documentation

The BossBot CLI tool `bossctl` provides a comprehensive command-line interface for managing and using the BossBot Discord bot functionality. It supports media downloads from various platforms using the experimental strategy pattern with API-direct and CLI-based modes.

## Installation & Usage

```bash
# Run any bossctl command
bossctl <command> [options]

# Or using uv (recommended during development)
uv run python -m boss_bot.cli.main <command> [options]
```

## Main Commands

### Version & Information Commands

#### `version`
Display the current version of boss_bot.

```bash
bossctl version
```

**Output:** `boss_bot version: X.X.X`

#### `deps`
Show dependency versions for all major components.

```bash
bossctl deps
```

**Output:** Displays versions for:
- boss_bot
- langchain packages (core, community, openai, text_splitters)
- chromadb
- langsmith
- pydantic packages
- ruff

#### `about`
Show basic information about BossBot CLI.

```bash
bossctl about
```

### Configuration Commands

#### `config`
Show comprehensive BossSettings configuration and environment variables status.

```bash
bossctl config
```

**Features:**
- Displays all configuration fields with their values
- Masks sensitive information (tokens, secrets)
- Shows environment variable status (set/not set)
- Checks core settings, feature flags, download settings, and monitoring options

**Environment Variables Checked:**
- **Core:** `DISCORD_TOKEN`, `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, `PREFIX`, `DEBUG`, `LOG_LEVEL`, `ENVIRONMENT`
- **Features:** `ENABLE_AI`, `ENABLE_REDIS`, `ENABLE_SENTRY`
- **Downloads:** `MAX_QUEUE_SIZE`, `MAX_CONCURRENT_DOWNLOADS`, `STORAGE_ROOT`, `MAX_FILE_SIZE_MB`
- **Strategy Flags:** `TWITTER_USE_API_CLIENT`, `REDDIT_USE_API_CLIENT`, `INSTAGRAM_USE_API_CLIENT`, `YOUTUBE_USE_API_CLIENT`, `DOWNLOAD_API_FALLBACK_TO_CLI`
- **Monitoring:** `ENABLE_METRICS`, `METRICS_PORT`, `ENABLE_HEALTH_CHECK`, `HEALTH_CHECK_PORT`

#### `setup-config`
Create a dummy gallery-dl configuration file at `~/.gallery-dl.conf` with comprehensive platform settings.

```bash
bossctl setup-config [options]
```

**Options:**
- `--force`: Skip confirmation prompt and create config file
- `--dry-run`: Show what would be changed without making modifications

**Features:**
- **Automatic Backup**: Creates timestamped backups of existing config files (e.g., `.gallery-dl.conf.backup_20241215_143021`)
- **User Confirmation**: Prompts before replacing existing files with backup preview
- **Comprehensive Config**: Includes settings for 20+ platforms (Twitter, Instagram, Reddit, YouTube, etc.)
- **Placeholder Values**: Uses `<CHANGEME>` and `<REDACT>` for credentials that need user input
- **Safety**: Error handling with automatic cleanup on failures

**Dry-Run Features:**
- **Diff Visualization**: Shows unified diff with color coding when existing config is found
  - 🟢 Green: Lines that would be added
  - 🔴 Red: Lines that would be removed
  - 🔵 Blue: File headers and context
- **New File Preview**: Shows syntax-highlighted preview of config that would be created
  - Line numbers and JSON syntax highlighting
  - File size and statistics
  - Platform summary
- **No Modifications**: Guarantees no files are created or modified in dry-run mode

**Examples:**
```bash
# Interactive mode - prompts for confirmation
bossctl setup-config

# See what would change without modifying files
bossctl setup-config --dry-run

# Force creation without prompts
bossctl setup-config --force

# Preview changes to existing config
bossctl setup-config --dry-run  # Shows diff if config exists
```

**Generated Config Includes:**
- **Platform Extractors**: Twitter, Instagram, Reddit, YouTube, DeviantArt, Pixiv, Tumblr, Pinterest, and 15+ more
- **Download Settings**: File handling, retries, timeouts, user agents
- **Output Configuration**: Progress indicators, logging, file naming
- **Authentication Placeholders**: Cookie settings, API keys, usernames/passwords marked for user input

**Next Steps After Setup:**
1. Edit `~/.gallery-dl.conf` to replace `<CHANGEME>` values with actual credentials
2. Test configuration with `bossctl check-config`
3. View configuration with `bossctl show-configs`

#### `show-configs`
Display gallery-dl and yt-dlp configuration files with sensitive data masked.

```bash
bossctl show-configs
```

**Features:**
- Locates and displays configuration files from common locations
- Masks sensitive configuration values (passwords, tokens, keys)
- Shows JSON and text-based configurations
- Provides help for configuration file locations

#### `check-config`
Check and validate gallery-dl configuration using gallery-dl's config.load and GalleryDLConfig validation.

```bash
bossctl check-config
```

**Features:**
- Uses gallery-dl's internal config loading mechanism
- Validates configuration with GalleryDLConfig schema
- Shows configuration sections and platform-specific settings
- Reports configuration file locations and status
- Provides detailed error messages for invalid configurations

#### `doctor`
Run health checks to verify repository requirements and configurations.

```bash
bossctl doctor
```

**Health Checks:**
- Gallery-dl configuration validation
- Configuration file accessibility
- JSON syntax validation
- Required sections verification

### Bot Management

#### `go`
Start the Discord bot.

```bash
bossctl go
```

**Description:** Launches the BossBot Discord bot using the configured settings.

#### `show`
Show basic bot information.

```bash
bossctl show
```

### Generic Download Command

#### `fetch`
Download media from URLs using appropriate API client (gallery-dl or yt-dlp).

```bash
bossctl fetch <url1> [url2 ...] [options]
```

**Arguments:**
- `urls` (required): One or more URLs to download

**Options:**
- `--output`, `-o`: Output directory for downloads (default: `./downloads`)
- `--verbose`, `-v`: Enable verbose output
- `--dry-run`: Show what would be downloaded without actually downloading

**Examples:**
```bash
# Download from multiple URLs
bossctl fetch https://twitter.com/user/status/123 https://youtube.com/watch?v=abc

# Custom output directory
bossctl fetch https://reddit.com/r/pics/comments/abc123/ -o ./my-downloads

# Dry run to see what would be downloaded
bossctl fetch https://instagram.com/p/ABC123/ --dry-run

# Verbose output for debugging
bossctl fetch https://youtu.be/VIDEO_ID --verbose
```

**Features:**
- Automatic tool selection based on URL patterns
- Uses yt-dlp for video platforms (YouTube, Twitch, Vimeo, TikTok)
- Uses gallery-dl for gallery platforms (Twitter, Instagram, Reddit, Imgur)
- Async download processing
- Download success/failure reporting

## Download Commands

The download commands use the experimental strategy pattern with feature flag support for API-direct or CLI modes.

### Platform-Specific Commands

#### `download twitter`
Download Twitter/X content with comprehensive options.

```bash
bossctl download twitter <url> [options]
```

**Arguments:**
- `url` (required): Twitter/X URL to download

**Options:**
- `--output-dir`, `-o`: Directory to save downloads
- `--async`: Use async download mode
- `--metadata-only`, `-m`: Extract metadata only, don't download files
- `--verbose`, `-v`: Show verbose output

**Supported URL Formats:**
- `https://twitter.com/username/status/123456789`
- `https://x.com/username/status/123456789`
- `https://twitter.com/username`
- `https://x.com/username`

**Examples:**
```bash
# Download a specific tweet
bossctl download twitter https://twitter.com/username/status/123456789

# Download to custom directory
bossctl download twitter https://x.com/username/status/123456789 --output-dir ./downloads

# Extract metadata only
bossctl download twitter https://twitter.com/username --metadata-only

# Verbose output with async mode
bossctl download twitter https://x.com/username --async --verbose
```

#### `download reddit`
Download Reddit content with config and authentication support.

```bash
bossctl download reddit <url> [options]
```

**Arguments:**
- `url` (required): Reddit URL to download

**Options:**
- `--output-dir`, `-o`: Directory to save downloads
- `--async`: Use async download mode
- `--metadata-only`, `-m`: Extract metadata only, don't download files
- `--verbose`, `-v`: Show verbose output
- `--config`: Custom gallery-dl config file
- `--cookies`: Browser cookies file

**Supported URL Formats:**
- `https://reddit.com/r/subreddit/comments/abc123/title/`
- `https://www.reddit.com/r/subreddit/comments/abc123/title/`
- `https://old.reddit.com/r/subreddit/comments/abc123/title/`

**Examples:**
```bash
# Download Reddit post
bossctl download reddit https://reddit.com/r/pics/comments/abc123/title/

# Use custom config and cookies
bossctl download reddit <url> --output-dir ./downloads --cookies cookies.txt

# Metadata only with custom config
bossctl download reddit <url> --metadata-only --config reddit-config.json
```

#### `download instagram`
Download Instagram content with experimental features.

```bash
bossctl download instagram <url> [options]
```

**Arguments:**
- `url` (required): Instagram URL to download

**Options:**
- `--output-dir`, `-o`: Directory to save downloads
- `--async`: Use async download mode
- `--metadata-only`, `-m`: Extract metadata only, don't download files
- `--verbose`, `-v`: Show verbose output
- `--cookies-browser`: Browser to extract cookies from (default: Firefox)
- `--user-agent`: Custom user agent string (default: Wget/1.21.1)

**Supported URL Formats:**
- `https://instagram.com/p/ABC123/`
- `https://www.instagram.com/p/ABC123/`
- `https://instagram.com/username/`
- `https://www.instagram.com/username/`

**Examples:**
```bash
# Download Instagram post
bossctl download instagram https://instagram.com/p/ABC123/

# Use Chrome cookies and custom user agent
bossctl download instagram <url> --cookies-browser Chrome --user-agent "Custom Agent 1.0"

# Download profile with Firefox cookies
bossctl download instagram https://instagram.com/username/ --output-dir ./downloads
```

#### `download youtube`
Download YouTube content with quality and format control.

```bash
bossctl download youtube <url> [options]
```

**Arguments:**
- `url` (required): YouTube URL to download

**Options:**
- `--output-dir`, `-o`: Directory to save downloads
- `--async`: Use async download mode
- `--metadata-only`, `-m`: Extract metadata only, don't download files
- `--verbose`, `-v`: Show verbose output
- `--quality`, `-q`: Video quality (e.g., 720p, 1080p, best) (default: best)
- `--audio-only`, `-a`: Download audio only

**Supported URL Formats:**
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/playlist?list=PLAYLIST_ID`

**Examples:**
```bash
# Download video with best quality
bossctl download youtube https://youtube.com/watch?v=VIDEO_ID

# Download with specific quality
bossctl download youtube https://youtu.be/VIDEO_ID --quality 720p

# Download audio only
bossctl download youtube <url> --audio-only --output-dir ./downloads

# Extract metadata only
bossctl download youtube <url> --metadata-only
```

### Download Information Commands

#### `download info`
Show comprehensive information about download capabilities.

```bash
bossctl download info
```

**Output includes:**
- Supported platforms and their capabilities
- Available commands
- Strategy features (API-Direct, CLI Mode, Auto-Fallback)
- Usage examples

#### `download strategies`
Show current download strategy configuration.

```bash
bossctl download strategies
```

**Features:**
- Shows API-direct vs CLI mode status for each platform
- Displays auto-fallback configuration
- Provides tips for enabling experimental features

## Strategy Pattern Features

### Modes

- **🚀 API-Direct Mode**: Experimental direct API integration for faster performance
- **🖥️ CLI Mode**: Stable subprocess-based approach (default)
- **🔄 Auto-Fallback**: API failures automatically fallback to CLI when enabled

### Feature Flags

Control strategy behavior using environment variables:

```bash
# Enable API-direct mode per platform
export TWITTER_USE_API_CLIENT=true
export REDDIT_USE_API_CLIENT=true
export INSTAGRAM_USE_API_CLIENT=true
export YOUTUBE_USE_API_CLIENT=true

# Control auto-fallback
export DOWNLOAD_API_FALLBACK_TO_CLI=true
```

### Status Indicators

Commands show the current strategy mode:
- 🚀 **API-Direct Mode**: Using experimental direct API integration
- 🖥️ **CLI Mode**: Using stable subprocess-based approach
- 🔄 **Auto-Fallback**: API failures automatically fallback to CLI

## Output & Error Handling

### Success Output
- ✅ Download completion status
- 📄 List of downloaded files
- 🚀/🖥️ Method used (API/CLI)
- Metadata display (when using `--verbose` or `--metadata-only`)

### Error Handling
- ❌ Clear error messages
- 🔄 Automatic fallback when enabled
- Detailed tracebacks with `--verbose`
- URL validation with helpful format examples

### Progress Indicators
- Spinner progress bars during downloads
- Real-time status updates
- Download summary with success/failure counts

## Environment Setup

### Required Environment Variables
```bash
# Core Discord bot functionality
DISCORD_TOKEN=your_discord_token

# Optional but recommended
OPENAI_API_KEY=your_openai_key
LANGCHAIN_API_KEY=your_langchain_key
```

### Download Configuration
```bash
# Download directory (default: .downloads/)
BOSS_BOT_DOWNLOAD_DIR="./downloads"

# Queue and concurrency limits
MAX_QUEUE_SIZE=10
MAX_CONCURRENT_DOWNLOADS=3
MAX_FILE_SIZE_MB=100
```

### Debug and Development
```bash
# Enable debug mode
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Enable verbose logging
VERBOSE=true
```

## Common Usage Patterns

### Quick Downloads
```bash
# Single URL download
bossctl fetch https://twitter.com/user/status/123

# Multiple URLs
bossctl fetch url1 url2 url3 --output ./downloads
```

### Platform-Specific Downloads
```bash
# Twitter with metadata
bossctl download twitter <url> --metadata-only --verbose

# Reddit with authentication
bossctl download reddit <url> --cookies cookies.txt --config config.json

# YouTube with quality control
bossctl download youtube <url> --quality 720p --audio-only
```

### Configuration Management
```bash
# Create initial gallery-dl configuration
bossctl setup-config

# Preview configuration changes
bossctl setup-config --dry-run

# Check current configuration
bossctl config

# Show download tool configs
bossctl show-configs

# Validate gallery-dl configuration
bossctl check-config

# Run health checks
bossctl doctor

# Check strategy status
bossctl download strategies
```

### Bot Management
```bash
# Start the bot
bossctl go

# Check version and dependencies
bossctl version
bossctl deps
```

## Troubleshooting

### Common Issues

1. **URL Validation Errors**: Ensure URLs match supported formats shown in error messages
2. **Download Failures**: Use `--verbose` for detailed error information
3. **Authentication Issues**: Check cookie files and configuration for private content
4. **Strategy Issues**: Verify environment variables for API-direct mode

### Debug Commands
```bash
# Verbose output for debugging
bossctl download <platform> <url> --verbose

# Dry run to test without downloading
bossctl fetch <url> --dry-run

# Preview config changes
bossctl setup-config --dry-run

# Check configuration status
bossctl config
bossctl show-configs
bossctl check-config
bossctl doctor
```

### Getting Help
```bash
# General help
bossctl --help

# Command-specific help
bossctl download --help
bossctl download twitter --help
```
