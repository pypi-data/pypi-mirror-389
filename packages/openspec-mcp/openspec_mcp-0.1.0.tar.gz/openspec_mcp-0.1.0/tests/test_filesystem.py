"""Tests for FileSystemManager."""

import pytest
from openspec_mcp.core import FileSystemManager
from openspec_mcp.utils import NotInitializedError


def test_is_initialized_false(temp_dir):
    """Test is_initialized returns False for uninitialized directory."""
    fs = FileSystemManager(str(temp_dir))
    assert not fs.is_initialized()


def test_is_initialized_true(initialized_project):
    """Test is_initialized returns True for initialized directory."""
    fs = FileSystemManager(str(initialized_project))
    assert fs.is_initialized()


def test_ensure_initialized_raises(temp_dir):
    """Test ensure_initialized raises error for uninitialized directory."""
    fs = FileSystemManager(str(temp_dir))
    with pytest.raises(NotInitializedError):
        fs.ensure_initialized()


def test_ensure_initialized_success(initialized_project):
    """Test ensure_initialized succeeds for initialized directory."""
    fs = FileSystemManager(str(initialized_project))
    fs.ensure_initialized()  # Should not raise


def test_create_directory(temp_dir):
    """Test directory creation."""
    fs = FileSystemManager(str(temp_dir))
    test_dir = temp_dir / "test"
    fs.create_directory(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()


def test_read_write_file(temp_dir):
    """Test file read and write operations."""
    fs = FileSystemManager(str(temp_dir))
    test_file = temp_dir / "test.txt"
    content = "Hello, World!"
    
    fs.write_file(test_file, content)
    assert test_file.exists()
    
    read_content = fs.read_file(test_file)
    assert read_content == content


def test_file_exists(temp_dir):
    """Test file existence check."""
    fs = FileSystemManager(str(temp_dir))
    test_file = temp_dir / "test.txt"
    
    assert not fs.file_exists(test_file)
    
    fs.write_file(test_file, "content")
    assert fs.file_exists(test_file)


def test_list_changes(initialized_project):
    """Test listing changes."""
    fs = FileSystemManager(str(initialized_project))
    
    # Create some test changes
    (fs.changes_path / "change-1").mkdir()
    (fs.changes_path / "change-2").mkdir()
    (fs.changes_path / "archive").mkdir(exist_ok=True)  # Should be excluded
    
    changes = fs.list_changes()
    assert len(changes) == 2
    assert "change-1" in changes
    assert "change-2" in changes
    assert "archive" not in changes


def test_list_specs(initialized_project):
    """Test listing specs."""
    fs = FileSystemManager(str(initialized_project))
    
    # Create some test specs
    (fs.specs_path / "auth").mkdir()
    (fs.specs_path / "payment").mkdir()
    
    specs = fs.list_specs()
    assert len(specs) == 2
    assert "auth" in specs
    assert "payment" in specs
