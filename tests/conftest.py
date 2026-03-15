"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Provide a temporary cache directory for tests."""
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    return cache_dir
