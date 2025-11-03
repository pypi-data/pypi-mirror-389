"""
Pytest configuration and fixtures
"""

import warnings

import pytest

from vibecontrols_sdk import VibecontrolsSDK, VibecontrolsSDKConfig

# Suppress specific async mock warnings
warnings.filterwarnings(
    "ignore", message="coroutine 'AsyncMockMixin._execute_mock_call' was never awaited"
)
warnings.filterwarnings("ignore", category=RuntimeWarning, module=".*")


@pytest.fixture
def sdk_config():
    """Basic SDK configuration for testing"""
    return VibecontrolsSDKConfig(
        endpoint="https://api.test.com/graphql", api_key="test-api-key"
    )


@pytest.fixture
def sdk(sdk_config):
    """SDK instance for testing"""
    return VibecontrolsSDK(sdk_config)


@pytest.fixture
async def async_sdk(sdk_config):
    """Async SDK instance with proper cleanup"""
    sdk = VibecontrolsSDK(sdk_config)
    yield sdk
    await sdk.client.close()
