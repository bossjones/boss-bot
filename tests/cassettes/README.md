# VCR Cassettes

This directory contains VCR cassettes for testing API interactions with external services like Twitter, Reddit, YouTube, etc.

## Security Considerations

All cassettes in this directory are **safe to commit to the repository** because:

1. **Request Filtering**: Sensitive headers like `Authorization`, `Cookie`, `X-API-Key` are replaced with dummy values
2. **Response Sanitization**: Rate limiting headers, request IDs, and cookies are normalized
3. **Body Filtering**: API keys, tokens, usernames, and passwords in request bodies are replaced with dummy values
4. **URL Matching**: Similar requests (e.g., Twitter API calls) are matched by pattern rather than exact URL

## Cassette Structure

```yaml
interactions:
- request:
    body: null
    headers: {}  # All sensitive headers removed
    method: GET
    uri: https://x.com/i/api/graphql/...
  response:
    body:
      string: !!binary |
        # Base64 encoded response (gzipped)
    headers:
      # Sanitized headers with fake values
      x-rate-limit-remaining: "49"
      set-cookie:
      - guest_id=v1%3FAKEBROTHER; Path=/; Domain=.x.com
    status:
      code: 200
      message: OK
```

## Usage in Tests

```python
import pytest

@pytest.mark.vcr
async def test_twitter_download():
    """Test Twitter download with VCR recording."""
    # This will use/create a cassette file automatically
    async with AsyncGalleryDL() as client:
        async for item in client.download("https://twitter.com/example"):
            assert item["extractor"] == "twitter"
```

## Cassette Files

- `test_twitter_api_download.yaml` - Twitter API interactions
- `test_reddit_api_download.yaml` - Reddit API interactions
- `test_youtube_api_download.yaml` - YouTube API interactions
- `test_strategy_fallback.yaml` - Strategy fallback scenarios

## Regenerating Cassettes

To regenerate cassettes with new API responses:

1. Delete the existing cassette file
2. Run the test with real API access
3. The new cassette will be recorded with sanitized data
4. Verify the cassette contains no sensitive information before committing

## Verification Checklist

Before committing cassettes, ensure:

- [ ] No real API keys or tokens in headers
- [ ] No real usernames/passwords in request bodies
- [ ] Cookies are replaced with fake values
- [ ] Rate limiting headers use dummy values
- [ ] Request IDs are anonymized
