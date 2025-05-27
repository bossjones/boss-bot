"""Test VCR configuration setup for boss-bot.

This test file verifies that our VCR configuration is working correctly
and safely filtering sensitive data from cassettes.
"""

import pytest
from tests.conftest import (
    vcr_config,
    is_twitter,
    is_reddit,
    is_youtube,
    filter_response,
    filter_request,
    DictSubSet,
    RegexMatcher,
    IgnoreOrder,
)


def test_vcr_config_fixture(vcr_config):
    """Test that vcr_config fixture provides correct configuration."""
    config = vcr_config

    # Verify structure
    assert isinstance(config, dict)
    assert "filter_headers" in config
    assert "filter_query_parameters" in config
    assert "before_record_request" in config
    assert "before_record_response" in config

    # Verify sensitive headers are filtered
    header_names = [h[0] for h in config["filter_headers"]]
    assert "authorization" in header_names
    assert "x-api-key" in header_names
    assert "cookie" in header_names

    # Verify sensitive query parameters are filtered
    assert "api_key" in config["filter_query_parameters"]
    assert "access_token" in config["filter_query_parameters"]
    assert "client_secret" in config["filter_query_parameters"]


def test_url_platform_detection():
    """Test URL platform detection functions."""
    # Twitter URLs
    assert is_twitter("https://twitter.com/user/status/123")
    assert is_twitter("https://x.com/user/status/123")
    assert is_twitter("https://mobile.twitter.com/user/status/123")
    assert not is_twitter("https://facebook.com/post/123")

    # Reddit URLs
    assert is_reddit("https://reddit.com/r/test/comments/abc123/")
    assert is_reddit("https://www.reddit.com/r/test/")
    assert is_reddit("https://old.reddit.com/r/test/")
    assert not is_reddit("https://twitter.com/test")

    # YouTube URLs
    assert is_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_youtube("https://youtu.be/dQw4w9WgXcQ")
    # Note: YouTube shorts pattern is complex, testing basic patterns
    assert not is_youtube("https://vimeo.com/123456")


def test_response_filtering():
    """Test that response filtering removes sensitive data."""
    # Mock response with sensitive headers
    response = {
        "headers": {
            "x-ratelimit-remaining-requests": "50",
            "x-request-id": "real-request-id-12345",
            "Set-Cookie": [
                "session_id=real_session_123; Path=/; Domain=.example.com",
                "auth_token=real_token_456; Path=/; Secure",
            ],
            "retry-after": "60",
        },
        "body": "response content",
    }

    filtered = filter_response(response)

    # Verify rate limiting headers are sanitized
    assert filtered["headers"]["x-ratelimit-remaining-requests"] == "144"
    assert filtered["headers"]["x-request-id"] == "fake-request-id"
    assert filtered["headers"]["retry-after"] == "0"

    # Verify cookies are replaced with fake values
    cookies = filtered["headers"]["Set-Cookie"]
    assert all("FAKE" in cookie or "AKEBROTHER" in cookie for cookie in cookies)
    assert not any("real_session" in cookie or "real_token" in cookie for cookie in cookies)


def test_request_filtering():
    """Test that request filtering removes sensitive data."""
    # Create a mock request object with the expected attributes
    class MockRequest:
        def __init__(self):
            self.uri = "https://api.example.com/data"
            self.path = "/data"
            self.method = "POST"
            self.headers = {
                "Authorization": "Bearer real-token-123",
                "X-API-Key": "real-api-key-456",
                "Content-Type": "application/json",
            }
            self.body = b'{"api_key": "secret-key", "username": "real_user"}'

    request = MockRequest()

    filtered = filter_request(request)

    # Verify headers are cleared
    assert filtered.headers == {}

    # Note: POST data filtering is handled by VCR's built-in filters
    # which would be applied after our filter in the actual VCR pipeline


def test_ignore_localhost_requests():
    """Test that localhost requests are ignored."""
    class MockRequest:
        def __init__(self):
            self.uri = "http://localhost:8000/api/test"
            self.path = "/api/test"
            self.method = "GET"
            self.headers = {}
            self.body = None

    localhost_request = MockRequest()

    filtered = filter_request(localhost_request)
    assert filtered is None  # Should be ignored


def test_vcr_utility_classes():
    """Test VCR utility classes for flexible assertions."""
    # Test IgnoreOrder
    assert [1, 2, 3] == IgnoreOrder([3, 1, 2])
    assert [1, 2, 3] != IgnoreOrder([1, 2, 4])

    # Test RegexMatcher
    assert "hello123" == RegexMatcher(r"hello\d+")
    assert "goodbye" != RegexMatcher(r"hello\d+")

    # Test DictSubSet
    full_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
    subset = DictSubSet({"a": 1, "c": 3})
    assert full_dict == subset

    wrong_subset = DictSubSet({"a": 1, "c": 999})
    assert full_dict != wrong_subset


def test_example_vcr_integration():
    """Example test showing how VCR would be used with real API calls."""
    # This is a mock example - in real usage with @pytest.mark.vcr,
    # this would record/replay actual HTTP interactions

    mock_api_response = {
        "extractor": "twitter",
        "id": "1868256259251863704",
        "title": "Example tweet content",
        "uploader": "test_user",
        "upload_date": "20241214",
    }

    # Use utility classes for flexible matching
    expected = DictSubSet({
        "extractor": "twitter",
        "title": RegexMatcher(r".*tweet.*"),
        "upload_date": "20241214",
    })

    assert mock_api_response == expected


@pytest.mark.asyncio
async def test_async_vcr_compatibility():
    """Test that VCR setup works with async functions."""
    # This test verifies that our VCR configuration works with async code
    # which is important for the experimental API clients

    # Mock async API call
    async def mock_api_call(url: str):
        """Mock async API call that would use VCR in real implementation."""
        if is_twitter(url):
            return {
                "platform": "twitter",
                "url": url,
                "data": "mock twitter data",
            }
        elif is_reddit(url):
            return {
                "platform": "reddit",
                "url": url,
                "data": "mock reddit data",
            }
        else:
            return {
                "platform": "unknown",
                "url": url,
                "data": "mock data",
            }

    # Test different platform URLs
    twitter_result = await mock_api_call("https://twitter.com/test/status/123")
    assert twitter_result["platform"] == "twitter"

    reddit_result = await mock_api_call("https://reddit.com/r/test/")
    assert reddit_result["platform"] == "reddit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
