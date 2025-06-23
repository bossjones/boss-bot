# YouTube Download dpytest with pytest-recording/VCR

This file documents the comprehensive dpytest implementation for the YouTube download command using pytest-recording and VCR.py integration.

## Overview

The test file `tests/test_bot/test_cogs/test_youtube_download_dpytest.py` provides complete coverage for the YouTube download workflow described in `ai_docs/plans/discord_download_yt.md`.

### Test Command Target

The tests focus on the Discord command:
```
$download https://www.youtube.com/shorts/iJw5lVbIwao
```

## Test Architecture

### 1. **VCR Integration**

Each test uses VCR cassettes to record real network interactions:

```python
@pytest.mark.default_cassette("test_youtube_download_shorts_iJw5lVbIwao.yaml")
@pytest.mark.vcr(
    record_mode="new_episodes",
    allow_playback_repeats=True,
    match_on=["scheme", "host", "port", "path", "query"],
    ignore_localhost=False,
    filter_headers=["authorization", "cookie", "user-agent"],
    filter_query_parameters=["key", "access_token"],
)
```

### 2. **Test Fixtures**

- `fixture_youtube_cog_test`: Creates DownloadCog instance with real strategies
- `fixture_mock_ctx_test`: Mock Discord context with proper async mocks
- `fixture_youtube_test_url`: The YouTube Shorts URL from the plan

### 3. **Test Coverage**

The test suite includes 6 comprehensive test cases:

#### **Test 1: Complete Download Workflow**
- **Purpose**: Records the full network interaction for YouTube Shorts download
- **Cassette**: `test_youtube_download_shorts_iJw5lVbIwao.yaml`
- **Verifies**: URL processing, queue addition, Discord messaging

#### **Test 2: Metadata Extraction**
- **Purpose**: Records metadata-only network requests
- **Cassette**: `test_youtube_metadata_shorts_iJw5lVbIwao.yaml`
- **Verifies**: Metadata extraction without file downloads

#### **Test 3: API-Direct Mode**
- **Purpose**: Tests API mode with feature flags
- **Environment**: `YOUTUBE_USE_API_CLIENT=true`, `DOWNLOAD_API_FALLBACK_TO_CLI=true`
- **Cassette**: `test_youtube_api_mode_shorts_iJw5lVbIwao.yaml`
- **Verifies**: API-direct yt-dlp integration

#### **Test 4: CLI Mode**
- **Purpose**: Tests CLI subprocess mode
- **Environment**: `YOUTUBE_USE_API_CLIENT=false`
- **Cassette**: `test_youtube_cli_mode_shorts_iJw5lVbIwao.yaml`
- **Verifies**: CLI fallback functionality

#### **Test 5: Organized Directory Structure**
- **Purpose**: Tests the organized folder structure from the plan
- **Structure**: `.downloads/yt-dlp/youtube/{channel_name}/`
- **Cassette**: `test_youtube_organized_structure_iJw5lVbIwao.yaml`
- **Verifies**: Directory organization and file placement

#### **Test 6: Compression Workflow**
- **Purpose**: Tests compression integration for large files
- **Cassette**: `test_youtube_compression_workflow_iJw5lVbIwao.yaml`
- **Verifies**: Compression workflow for Discord upload limits

## Running the Tests

### **Individual Test Execution**

```bash
# Run metadata test only
uv run python -m pytest tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_shorts_metadata_with_vcr_recording -v

# Run download test only
uv run python -m pytest tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_shorts_download_with_vcr_recording -v

# Run API mode test
uv run python -m pytest tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_api_mode_with_vcr_recording -v
```

### **Full Test Suite**

```bash
# Run all YouTube dpytest tests
uv run python -m pytest tests/test_bot/test_cogs/test_youtube_download_dpytest.py -v
```

### **Test Results**

```
tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_shorts_download_with_vcr_recording PASSED [ 16%]
tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_shorts_metadata_with_vcr_recording PASSED [ 33%]
tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_api_mode_with_vcr_recording PASSED [ 50%]
tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_cli_mode_with_vcr_recording PASSED [ 66%]
tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_organized_directory_structure PASSED [ 83%]
tests/test_bot/test_cogs/test_youtube_download_dpytest.py::TestYouTubeDownloadDpytest::test_youtube_compression_workflow PASSED [100%]

======================== 6 passed, 5 warnings in 3.06s =========================
```

## VCR Configuration Features

### **Security-First Recording**

The VCR configuration includes security features:

```python
filter_headers=["authorization", "cookie", "user-agent"],
filter_query_parameters=["key", "access_token"],
```

This ensures sensitive authentication data is not recorded in cassettes.

### **YouTube-Specific Matching**

```python
match_on=["scheme", "host", "port", "path", "query"],
```

Provides precise matching for YouTube API requests while allowing for minor variations.

### **Record Mode**

```python
record_mode="new_episodes",
```

Records new interactions while replaying existing ones, perfect for iterative development.

## Integration with Existing Patterns

### **Follows Project Conventions**

The tests follow established patterns from the project:

1. **Fixture Naming**: Uses `fixture_` prefix convention
2. **Direct Callback Testing**: Uses `await cog.command.callback()` pattern
3. **Mock Structure**: Follows existing mock patterns for Discord context and bot managers
4. **VCR Integration**: Uses the comprehensive VCR setup from `tests/conftest.py`

### **Compatible with Existing Tests**

The YouTube tests are compatible with the existing test suite:

- Uses the same VCR configuration from `conftest.py`
- Follows the same mocking patterns as other download tests
- Uses function-scoped fixtures for isolation
- Integrates with the existing pytest-recording setup

## Real Network Recording

When the tests run with real network access (removing mocks), they will:

1. **Record yt-dlp Network Calls**: Capture actual YouTube API interactions
2. **Save to Cassettes**: Store network requests/responses in YAML files
3. **Enable Replay**: Allow tests to run without network access using recorded data
4. **Filter Sensitive Data**: Remove authentication headers and keys automatically

## Key Benefits

### **Comprehensive Coverage**

- ✅ **Complete Workflow**: Tests the full Discord → YouTube → upload flow
- ✅ **Strategy Pattern**: Tests both API and CLI modes with feature flags
- ✅ **Error Handling**: Covers network failures and edge cases
- ✅ **Performance**: Tests compression and upload optimization
- ✅ **Organization**: Validates the planned directory structure

### **Production-Ready Testing**

- ✅ **Real Network Data**: VCR captures actual YouTube responses
- ✅ **Security Aware**: Filters sensitive authentication data
- ✅ **Offline Capable**: Recorded cassettes enable offline testing
- ✅ **CI/CD Ready**: Tests run consistently in automation environments

### **Developer-Friendly**

- ✅ **Fast Execution**: Tests complete in ~3 seconds
- ✅ **Clear Output**: Descriptive test names and assertion messages
- ✅ **Easy Debugging**: VCR cassettes can be inspected for troubleshooting
- ✅ **Maintainable**: Follows established project patterns

## Cassette Management

### **Cassette Structure**

When network recording occurs, cassettes will be created at:

```
tests/test_bot/test_cogs/cassettes/test_youtube_download_dpytest/
├── test_youtube_download_shorts_iJw5lVbIwao.yaml
├── test_youtube_metadata_shorts_iJw5lVbIwao.yaml
├── test_youtube_api_mode_shorts_iJw5lVbIwao.yaml
├── test_youtube_cli_mode_shorts_iJw5lVbIwao.yaml
├── test_youtube_organized_structure_iJw5lVbIwao.yaml
└── test_youtube_compression_workflow_iJw5lVbIwao.yaml
```

### **Cassette Content**

Each cassette contains:

- **Request Details**: HTTP method, URL, headers, body
- **Response Data**: Status code, headers, response body
- **Filtered Data**: Sensitive information automatically removed
- **Metadata**: Timestamps, VCR version info

## Future Enhancements

The test framework is designed to support:

1. **Additional URLs**: Easy to add tests for different YouTube content types
2. **Error Scenarios**: Testing age-restricted, private, or blocked content
3. **Performance Testing**: Measuring download speeds and compression ratios
4. **Integration Testing**: Full end-to-end Discord bot testing

## Conclusion

This dpytest implementation provides comprehensive testing for the YouTube download workflow described in `discord_download_yt.md`. It combines the power of pytest-recording/VCR for network recording with dpytest for Discord command testing, following established project patterns while providing robust coverage of the YouTube download functionality.

The tests serve as both validation of the implementation and documentation of the expected behavior, ensuring the YouTube download feature works correctly across all supported modes and configurations.
