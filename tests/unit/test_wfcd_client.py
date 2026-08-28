from unittest.mock import MagicMock, patch
import httpx
import pytest

from ai_voice_gaming_assistant.data import wfcd_client


def test_fetch_items_success(sample_items):
    """Test fetching items successfully returns parsed JSON."""
    mock_response = MagicMock()
    mock_response.json.return_value = sample_items
    mock_response.raise_for_status.return_value = None

    with patch("httpx.get", return_value=mock_response) as mock_get:
        items = wfcd_client.fetch_items()
        mock_get.assert_called_once_with(wfcd_client.ALL_ITEMS_URL)
        assert items == sample_items


def test_fetch_items_http_error():
    """Test HTTP errors during fetch raise HTTPStatusError."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=MagicMock(), response=MagicMock(status_code=500)
    )

    with patch("httpx.get", return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            wfcd_client.fetch_items()
