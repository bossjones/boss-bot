# LangGraph Assistant Configuration Examples

This directory contains example YAML configurations for different types of LangGraph assistants in the Boss-Bot system.

## General Purpose Assistants

### `high_quality_assistant.yaml`
- **Use Case**: Archival and maximum quality downloads
- **Features**: All AI features enabled, extended timeouts, best quality settings
- **Best For**: Important content that needs to be preserved with maximum fidelity
- **Trade-offs**: Slower downloads but highest quality

### `fast_assistant.yaml`
- **Use Case**: Quick downloads and real-time scenarios
- **Features**: AI disabled, minimal processing, reduced timeouts
- **Best For**: Bulk downloads or when speed is critical
- **Trade-offs**: Lower quality and fewer features but much faster

### `ai_enhanced_assistant.yaml`
- **Use Case**: General-purpose downloads with smart features
- **Features**: Balanced AI settings, intelligent content analysis
- **Best For**: Daily use with smart quality/speed balance
- **Trade-offs**: Good balance of speed and quality

## Platform-Specific Assistants

### YouTube (`platform_specific/youtube_assistant.yaml`)
- **Optimized For**: Video content, subtitles, metadata preservation
- **Key Features**: 4K quality, subtitle extraction, comprehensive metadata
- **Best For**: YouTube video archival and educational content

### Twitter/X (`platform_specific/twitter_assistant.yaml`)
- **Optimized For**: Tweet threads, social media content
- **Key Features**: Thread preservation, media variants, context analysis
- **Best For**: Social media monitoring and content archival

### Instagram (`platform_specific/instagram_assistant.yaml`)
- **Optimized For**: Visual content, stories, reels
- **Key Features**: Story preservation, high-quality images, carousel handling
- **Best For**: Visual content collection and brand monitoring

### Reddit (`platform_specific/reddit_assistant.yaml`)
- **Optimized For**: Discussion threads, community content
- **Key Features**: Comment threading, discussion analysis, community context
- **Best For**: Research and community discussion archival

## Configuration Schema

Each YAML file follows this structure:

```yaml
name: "Assistant Name"
description: "Description of the assistant's purpose"
graph_id: "download_workflow"
config:
  configurable:
    # AI Features
    enable_ai_strategy_selection: true/false
    enable_content_analysis: true/false
    ai_model: "gpt-4" | "gpt-3.5-turbo"
    ai_temperature: 0.0-1.0

    # Download Settings
    max_retries: 1-10
    timeout_seconds: 60-900
    download_quality: "best" | "high" | "good" | "fast"

    # Platform Specific Settings
    youtube_quality: "4k" | "1080p" | "720p" | "480p"
    twitter_include_replies: true/false
    instagram_include_stories: true/false
    reddit_include_comments: true/false

    # Advanced Settings
    preserve_original_filenames: true/false
    include_metadata_files: true/false
    verify_downloads: true/false

metadata:
  version: "1.0.0"
  author: "boss-bot-team"
  use_case: "description"
  performance_profile: "speed|quality|balanced"
  tags: ["tag1", "tag2"]
  created_at: "2024-01-01"
  notes: "Additional information"
```

## Usage Examples

### Create an Assistant
```bash
bossctl assistants create ai_docs/plans/examples/high_quality_assistant.yaml
```

### List All Assistants
```bash
bossctl assistants list
```

### Use an Assistant for Download
```bash
bossctl download --assistant <assistant-id> https://example.com/content
```

## Customization Guidelines

1. **Start with a base**: Choose the example that closest matches your use case
2. **Modify settings**: Adjust timeout, quality, and feature flags as needed
3. **Test incrementally**: Start with safe settings and gradually optimize
4. **Document changes**: Update the metadata section with your modifications
5. **Version control**: Keep your custom configurations in git

## Performance Profiles

- **Speed**: Fast downloads, minimal processing, basic quality
- **Quality**: Maximum quality, all features, longer timeouts
- **Balanced**: Good compromise between speed and quality
- **Specialized**: Optimized for specific platforms or content types

## Best Practices

1. **Name descriptively**: Use clear names that indicate the assistant's purpose
2. **Document thoroughly**: Include detailed descriptions and use cases
3. **Test before production**: Validate configurations with test content
4. **Monitor performance**: Track success rates and adjust as needed
5. **Keep backups**: Save working configurations before making changes

## Troubleshooting

- **Validation errors**: Check YAML syntax and required fields
- **Timeout issues**: Increase `timeout_seconds` for large content
- **Quality problems**: Enable AI features or increase quality settings
- **Speed issues**: Disable AI features or reduce quality settings
- **Platform errors**: Check platform-specific settings and credentials
