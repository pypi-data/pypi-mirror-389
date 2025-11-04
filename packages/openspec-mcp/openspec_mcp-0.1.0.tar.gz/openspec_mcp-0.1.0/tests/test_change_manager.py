"""Tests for ChangeManager."""

import pytest
from openspec_mcp.core import FileSystemManager, ChangeManager
from openspec_mcp.utils import ChangeNotFoundError, ChangeExistsError


def test_create_change(initialized_project):
    """Test creating a new change."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    result = manager.create_change(
        "add-feature",
        "Add new feature",
        ["auth", "api"]
    )
    
    assert result["change_id"] == "add-feature"
    assert "proposal.md" in result["files_created"]
    assert "tasks.md" in result["files_created"]
    
    # Verify files were created
    change_path = fs.get_change_path("add-feature")
    assert (change_path / "proposal.md").exists()
    assert (change_path / "tasks.md").exists()
    assert (change_path / "specs" / "auth" / "spec.md").exists()
    assert (change_path / "specs" / "api" / "spec.md").exists()


def test_create_change_duplicate(initialized_project):
    """Test creating a duplicate change raises error."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    manager.create_change("add-feature", "Description")
    
    with pytest.raises(ChangeExistsError):
        manager.create_change("add-feature", "Description")


def test_list_changes(initialized_project):
    """Test listing changes."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    manager.create_change("change-1", "Description 1")
    manager.create_change("change-2", "Description 2")
    
    changes = manager.list_changes()
    assert len(changes) == 2
    assert any(c["id"] == "change-1" for c in changes)
    assert any(c["id"] == "change-2" for c in changes)


def test_show_change(initialized_project):
    """Test showing change details."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    manager.create_change("test-change", "Test description", ["auth"])
    
    result = manager.show_change("test-change")
    
    assert result["change_id"] == "test-change"
    assert "## Why" in result["proposal"]
    assert "# Tasks" in result["tasks"]
    assert "auth" in result["spec_deltas"]


def test_show_change_not_found(initialized_project):
    """Test showing non-existent change raises error."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    with pytest.raises(ChangeNotFoundError):
        manager.show_change("non-existent")


def test_read_tasks(initialized_project):
    """Test reading tasks."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    manager.create_change("test-change", "Description")
    
    result = manager.read_tasks("test-change")
    
    assert result["change_id"] == "test-change"
    assert "tasks" in result
    assert "progress" in result


def test_update_task_status(initialized_project):
    """Test updating task status."""
    fs = FileSystemManager(str(initialized_project))
    manager = ChangeManager(fs)
    
    manager.create_change("test-change", "Description")
    
    # Update first task to completed
    result = manager.update_task_status("test-change", "1", True)
    
    assert result["task_id"] == "1"
    assert result["completed"] is True
    assert result["progress"]["completed"] >= 1
