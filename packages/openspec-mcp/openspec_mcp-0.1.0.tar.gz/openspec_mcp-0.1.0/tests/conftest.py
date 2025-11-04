"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def initialized_project(temp_dir):
    """Create an initialized OpenSpec project."""
    from openspec_mcp.core import FileSystemManager, InitManager
    
    fs = FileSystemManager(str(temp_dir))
    init_manager = InitManager(fs)
    init_manager.init_project()
    
    return temp_dir
