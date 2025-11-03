"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from gitdo.storage import Storage


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_dir):
    """Create a storage instance in a temporary directory."""
    return Storage(base_path=temp_dir)


@pytest.fixture
def initialized_storage(storage):
    """Create and initialize a storage instance."""
    storage.init()
    return storage
