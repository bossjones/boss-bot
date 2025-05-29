

Given the following 2 python files, how can I incorporate them into the boss-bot project? Think using <thinking> tags and <quote> any important implementation details and create a plan with a checklist for how to do this in ai_docs/plans/claude_check_instagram.md

Read /Users/malcolm/dev/bossjones/boss-bot/docs/downloaders_config.md
Read /Users/malcolm/dev/bossjones/boss-bot/docs/downloaders.md

```python
#!/usr/bin/env python3
"""
check_config.py
Config validation script for gallery-dl Instagram downloads
"""

def check_instagram_config():
    """Check that gallery-dl config is properly set for Instagram video downloads"""
    from gallery_dl import config as gdl_config

    # Load the config
    gdl_config.load()

    print("=== Gallery-dl Config Validation for Instagram ===\n")

    # Track validation results
    issues = []

    # Check base extractor settings
    print("📁 Base Extractor Settings:")
    base_dir = gdl_config.get(("extractor", "base-directory"))
    print(f"  base-directory: {base_dir}")
    if base_dir != "./downloads/":
        issues.append("base-directory should be './downloads/'")

    archive = gdl_config.get(("extractor", "archive"))
    print(f"  archive: {archive}")
    if archive != "./downloads/.archive.sqlite3":
        issues.append("archive should be './downloads/.archive.sqlite3'")

    # Check user-agent (command line overrides config)
    user_agent = gdl_config.get(("extractor", "user-agent"))
    print(f"  user-agent: {user_agent}")
    print("  ⚠️  NOTE: Command line --user-agent 'Wget/1.21.1' will override this")

    # Check path settings
    path_restrict = gdl_config.get(("extractor", "path-restrict"))
    print(f"  path-restrict: {path_restrict}")
    if path_restrict != "auto":
        issues.append("path-restrict should be 'auto'")

    path_extended = gdl_config.get(("extractor", "path-extended"))
    print(f"  path-extended: {path_extended}")
    if not path_extended:
        issues.append("path-extended should be true")

    print("\n📷 Instagram-specific Settings:")

    # Check Instagram videos setting
    instagram_videos = gdl_config.get(("extractor", "instagram", "videos"))
    print(f"  videos: {instagram_videos}")
    if not instagram_videos:
        issues.append("Instagram videos should be enabled (true)")

    # Check Instagram include setting
    instagram_include = gdl_config.get(("extractor", "instagram", "include"))
    print(f"  include: {instagram_include}")
    if instagram_include != "all":
        issues.append("Instagram include should be 'all'")

    # Check Instagram filename pattern
    instagram_filename = gdl_config.get(("extractor", "instagram", "filename"))
    print(f"  filename: {instagram_filename}")
    expected_filename = "{username}_{shortcode}_{num}.{extension}"
    if instagram_filename != expected_filename:
        issues.append(f"Instagram filename should be '{expected_filename}'")

    # Check Instagram directory pattern
    instagram_directory = gdl_config.get(("extractor", "instagram", "directory"))
    print(f"  directory: {instagram_directory}")
    expected_directory = ["instagram", "{username}"]
    if instagram_directory != expected_directory:
        issues.append(f"Instagram directory should be {expected_directory}")

    # Check Instagram sleep setting
    instagram_sleep = gdl_config.get(("extractor", "instagram", "sleep-request"))
    print(f"  sleep-request: {instagram_sleep}")
    if instagram_sleep != 8.0:
        issues.append("Instagram sleep-request should be 8.0")

    print("\n⬇️ Downloader Settings:")

    # Check downloader retries
    dl_retries = gdl_config.get(("downloader", "retries"))
    print(f"  retries: {dl_retries}")
    if dl_retries != 4:
        issues.append("downloader retries should be 4")

    # Check downloader timeout
    dl_timeout = gdl_config.get(("downloader", "timeout"))
    print(f"  timeout: {dl_timeout}")
    if dl_timeout != 30.0:
        issues.append("downloader timeout should be 30.0")

    # Check part downloads
    dl_part = gdl_config.get(("downloader", "part"))
    print(f"  part: {dl_part}")
    if not dl_part:
        issues.append("downloader part should be true")

    print("\n📤 Output Settings:")

    # Check output progress
    output_progress = gdl_config.get(("output", "progress"))
    print(f"  progress: {output_progress}")
    if not output_progress:
        issues.append("output progress should be true")

    # Check output mode
    output_mode = gdl_config.get(("output", "mode"))
    print(f"  mode: {output_mode}")
    if output_mode != "auto":
        issues.append("output mode should be 'auto'")

    print("\n🍪 Cookie Settings:")

    # Check cookies setting (should be null since using --cookies-from-browser)
    cookies = gdl_config.get(("extractor", "cookies"))
    instagram_cookies = gdl_config.get(("extractor", "instagram", "cookies"))
    print(f"  global cookies: {cookies}")
    print(f"  instagram cookies: {instagram_cookies}")
    print("  ⚠️  NOTE: Command line --cookies-from-browser Firefox will override these")

    print("\n🔧 Command Line Overrides to Note:")
    print("  --cookies-from-browser Firefox: Will load cookies from Firefox browser")
    print("  --no-mtime: Will disable setting file modification times")
    print("  --user-agent 'Wget/1.21.1': Will override config user-agent")
    print("  -v: Verbose output")
    print("  --write-info-json: Will write metadata JSON files")
    print("  --write-metadata: Will write metadata to files")

    print("\n" + "="*50)

    if issues:
        print(f"❌ Found {len(issues)} configuration issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print("✅ All Instagram configuration settings are correct!")
        return True

if __name__ == "__main__":
    check_instagram_config()
```

```python
"""
validate_config.py
Gallery-dl config validation utilities
"""

def validate_instagram_config():
    """
    Validate gallery-dl config for Instagram video downloads.
    Returns tuple of (is_valid: bool, issues: list)
    """
    from gallery_dl import config as gdl_config

    # Load the config
    gdl_config.load()

    issues = []

    # Expected values based on your config
    expected_values = {
        ("extractor", "base-directory"): "./downloads/",
        ("extractor", "archive"): "./downloads/.archive.sqlite3",
        ("extractor", "path-restrict"): "auto",
        ("extractor", "path-extended"): True,
        ("extractor", "instagram", "videos"): True,
        ("extractor", "instagram", "include"): "all",
        ("extractor", "instagram", "filename"): "{username}_{shortcode}_{num}.{extension}",
        ("extractor", "instagram", "directory"): ["instagram", "{username}"],
        ("extractor", "instagram", "sleep-request"): 8.0,
        ("downloader", "retries"): 4,
        ("downloader", "timeout"): 30.0,
        ("downloader", "part"): True,
        ("output", "progress"): True,
        ("output", "mode"): "auto",
    }

    # Check each expected value
    for config_path, expected in expected_values.items():
        actual = gdl_config.get(config_path)
        if actual != expected:
            path_str = " -> ".join(config_path)
            issues.append(f"{path_str}: expected {expected}, got {actual}")

    return len(issues) == 0, issues

def print_config_summary():
    """Print a summary of current Instagram-related config values"""
    from gallery_dl import config as gdl_config

    gdl_config.load()

    print("Current Instagram Config Values:")
    print(f"  Base directory: {gdl_config.get(('extractor', 'base-directory'))}")
    print(f"  Archive: {gdl_config.get(('extractor', 'archive'))}")
    print(f"  Instagram videos: {gdl_config.get(('extractor', 'instagram', 'videos'))}")
    print(f"  Instagram include: {gdl_config.get(('extractor', 'instagram', 'include'))}")
    print(f"  Instagram filename: {gdl_config.get(('extractor', 'instagram', 'filename'))}")
    print(f"  Instagram directory: {gdl_config.get(('extractor', 'instagram', 'directory'))}")
    print(f"  Sleep request: {gdl_config.get(('extractor', 'instagram', 'sleep-request'))}")

if __name__ == "__main__":
    is_valid, issues = validate_instagram_config()

    if is_valid:
        print("✅ Instagram config validation passed!")
    else:
        print("❌ Instagram config validation failed:")
        for issue in issues:
            print(f"  - {issue}")

    print("\n" + "-" * 40)
    print_config_summary()
```
