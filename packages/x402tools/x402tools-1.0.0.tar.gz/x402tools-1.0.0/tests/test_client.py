"""Basic tests for x402tools client."""

import pytest
from x402tools import X402Client, AuthenticationError

def test_client_initialization():
    """Test client initialization."""
    client = X402Client(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.base_url == "https://stakefy-usage-envelope-production.up.railway.app"

def test_client_custom_base_url():
    """Test client with custom base URL."""
    client = X402Client(api_key="test_key", base_url="https://custom.api.com")
    assert client.base_url == "https://custom.api.com"

# Add more tests as needed
