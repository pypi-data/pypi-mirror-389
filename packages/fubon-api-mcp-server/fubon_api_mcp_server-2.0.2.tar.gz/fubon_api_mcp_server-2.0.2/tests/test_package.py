"""
Tests for fubon_api_mcp_server package.
"""

import pytest

from fubon_api_mcp_server import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_package_import():
    """Test that package can be imported."""
    import fubon_api_mcp_server

    assert fubon_api_mcp_server is not None


def test_config_import():
    """Test that config module can be imported."""
    from fubon_api_mcp_server import config

    assert config is not None


def test_server_import():
    """Test that server module can be imported."""
    from fubon_api_mcp_server import server

    assert server is not None
