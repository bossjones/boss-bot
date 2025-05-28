"""VCR test for the fetch function in CLI main module."""

import pytest
import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from boss_bot.cli.main import fetch, _download_urls_async
from boss_bot.core.env import BossSettings


class TestFetchVcr:
    """Test class for fetch function with VCR integration."""

    @pytest.mark.asyncio
    @pytest.mark.vcr(cassette_name="test_fetch_twitter_helldiver_alert.yaml")
    async def test_fetch_twitter_helldiver_alert(self, tmp_path: Path, mocker):
        """Test fetching from X.com/Twitter URL using VCR.

        This test downloads content from:
        https://x.com/HelldiversAlert/status/1927338030467002589
        """
        # Setup output directory
        output_dir = tmp_path / "downloads"
        output_dir.mkdir(exist_ok=True)

        # Mock the console print functions to avoid output during tests
        mock_cprint = mocker.patch("boss_bot.cli.main.cprint")

        # Test URL
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Test the async download function directly
        await _download_urls_async([url], output_dir, verbose=False, dry_run=False)

        # Verify that cprint was called (indicating the function ran)
        assert mock_cprint.call_count > 0

        # Verify function completed without exceptions
        # (The actual file download behavior will be mocked by VCR)

    @pytest.mark.asyncio
    @pytest.mark.vcr(cassette_name="test_fetch_twitter_helldiver_alert_dry_run.yaml")
    async def test_fetch_twitter_helldiver_alert_dry_run(self, tmp_path: Path, mocker):
        """Test fetching from X.com/Twitter URL in dry run mode using VCR."""
        # Setup output directory
        output_dir = tmp_path / "downloads"
        output_dir.mkdir(exist_ok=True)

        # Mock the console print functions
        mock_cprint = mocker.patch("boss_bot.cli.main.cprint")

        # Test URL
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Test the async download function in dry run mode
        await _download_urls_async([url], output_dir, verbose=True, dry_run=True)

        # Verify that cprint was called with dry run message
        assert mock_cprint.call_count > 0

        # Check that dry run mode was indicated in the output
        call_args = [call[0][0] for call in mock_cprint.call_args_list if call[0]]
        dry_run_calls = [arg for arg in call_args if "Would use" in str(arg)]
        assert len(dry_run_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.vcr(cassette_name="test_fetch_twitter_tool_selection.yaml")
    async def test_fetch_tool_selection(self, tmp_path: Path, mocker):
        """Test that the correct download tool is selected for Twitter URLs using VCR."""
        from boss_bot.cli.main import _determine_download_tool

        # Test URL
        url = "https://x.com/HelldiversAlert/status/1927338030467002589"

        # Test tool determination
        tool, reason = _determine_download_tool(url)

        # Twitter/X URLs should use gallery-dl
        assert tool == "gallery-dl"
        assert "x.com" in reason.lower() or "twitter" in reason.lower()

    @pytest.mark.asyncio
    @pytest.mark.vcr(cassette_name="test_fetch_error_handling.yaml")
    async def test_fetch_error_handling(self, tmp_path: Path, mocker):
        """Test error handling in fetch function using VCR."""
        # Setup output directory
        output_dir = tmp_path / "downloads"
        output_dir.mkdir(exist_ok=True)

        # Mock the console print functions
        mock_cprint = mocker.patch("boss_bot.cli.main.cprint")

        # Mock AsyncGalleryDL to raise an exception
        with patch("boss_bot.core.downloads.clients.aio_gallery_dl.AsyncGalleryDL") as mock_gallery_dl:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_gallery_dl.return_value = mock_client

            # Make the download method raise an exception
            async def mock_download(*args, **kwargs):
                raise Exception("Network error")
                yield  # This makes it an async generator

            mock_client.download = mock_download

            # Test URL
            url = "https://x.com/HelldiversAlert/status/1927338030467002589"

            # Test the async download function with error
            await _download_urls_async([url], output_dir, verbose=True, dry_run=False)

            # Verify error handling was triggered
            assert mock_cprint.call_count > 0

            # Check that error message was printed
            call_args = [str(call[0][0]) for call in mock_cprint.call_args_list if call[0]]
            error_calls = [arg for arg in call_args if "❌" in arg or "Error" in arg or "Failed" in arg]
            assert len(error_calls) > 0

    @pytest.mark.asyncio
    @pytest.mark.vcr(cassette_name="test_fetch_multiple_urls.yaml")
    async def test_fetch_multiple_urls(self, tmp_path: Path, mocker):
        """Test fetching multiple URLs including the Twitter one using VCR."""
        # Setup output directory
        output_dir = tmp_path / "downloads"
        output_dir.mkdir(exist_ok=True)

        # Mock the console print functions
        mock_cprint = mocker.patch("boss_bot.cli.main.cprint")

        # Test URLs including our target Twitter URL
        urls = [
            "https://x.com/HelldiversAlert/status/1927338030467002589",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Different platform for tool selection test
        ]

        # Test the async download function with multiple URLs
        await _download_urls_async(urls, output_dir, verbose=False, dry_run=True)  # Use dry_run to avoid actual downloads

        # Verify that cprint was called for each URL
        assert mock_cprint.call_count > 0

        # Check that both URLs were processed
        call_args = [str(call[0][0]) for call in mock_cprint.call_args_list if call[0]]
        url_processing_calls = [arg for arg in call_args if "Processing URL" in arg]
        assert len(url_processing_calls) >= len(urls)

    @pytest.mark.vcr(cassette_name="test_fetch_command_integration.yaml")
    def test_fetch_command_integration(self, tmp_path: Path, mocker):
        """Test the full fetch command using VCR."""
        # Mock the console print functions
        mock_cprint = mocker.patch("boss_bot.cli.main.cprint")

        # Mock asyncio.run to capture the async call
        mock_asyncio_run = mocker.patch("boss_bot.cli.main.asyncio.run")

        # Setup test parameters
        output_dir = str(tmp_path / "downloads")
        urls = ["https://x.com/HelldiversAlert/status/1927338030467002589"]

        # Call the fetch function
        fetch(urls=urls, output_dir=output_dir, verbose=False, dry_run=True)

        # Verify that asyncio.run was called
        assert mock_asyncio_run.call_count == 1

        # Verify the cprint was called for setup messages
        assert mock_cprint.call_count > 0

        # Check that the async function was called with correct parameters
        called_args = mock_asyncio_run.call_args[0][0]
        # This should be a coroutine from _download_urls_async
        assert asyncio.iscoroutine(called_args)
