"""File system operations for OpenSpec."""

import os
from pathlib import Path
from typing import Optional

from ..utils import logger, FileSystemError


class FileSystemManager:
    """Manages file system operations for OpenSpec."""

    OPENSPEC_DIR = "openspec"
    SPECS_DIR = "specs"
    CHANGES_DIR = "changes"
    ARCHIVE_DIR = "archive"

    def __init__(self, working_dir: str = "."):
        """Initialize filesystem manager.
        
        Args:
            working_dir: Working directory path
        """
        self.working_dir = Path(working_dir).resolve()
        self.openspec_path = self.working_dir / self.OPENSPEC_DIR
        self.specs_path = self.openspec_path / self.SPECS_DIR
        self.changes_path = self.openspec_path / self.CHANGES_DIR
        self.archive_path = self.changes_path / self.ARCHIVE_DIR

    def is_initialized(self) -> bool:
        """Check if OpenSpec is initialized in the working directory."""
        return self.openspec_path.exists() and self.openspec_path.is_dir()

    def ensure_initialized(self) -> None:
        """Ensure OpenSpec is initialized, raise error if not."""
        from ..utils import NotInitializedError

        if not self.is_initialized():
            raise NotInitializedError(str(self.working_dir))

    def create_directory(self, path: Path) -> None:
        """Create a directory if it doesn't exist.
        
        Args:
            path: Directory path to create
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise FileSystemError(f"Failed to create directory: {e}", str(path))

    def read_file(self, path: Path) -> str:
        """Read file content.
        
        Args:
            path: File path to read
            
        Returns:
            File content as string
        """
        try:
            content = path.read_text(encoding="utf-8")
            logger.debug(f"Read file: {path}")
            return content
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            raise FileSystemError(f"File not found", str(path))
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise FileSystemError(f"Failed to read file: {e}", str(path))

    def write_file(self, path: Path, content: str) -> None:
        """Write content to file.
        
        Args:
            path: File path to write
            content: Content to write
        """
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.debug(f"Wrote file: {path}")
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise FileSystemError(f"Failed to write file: {e}", str(path))

    def file_exists(self, path: Path) -> bool:
        """Check if file exists.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists
        """
        return path.exists() and path.is_file()

    def directory_exists(self, path: Path) -> bool:
        """Check if directory exists.
        
        Args:
            path: Directory path to check
            
        Returns:
            True if directory exists
        """
        return path.exists() and path.is_dir()

    def list_directories(self, path: Path) -> list[str]:
        """List subdirectories in a directory.
        
        Args:
            path: Directory path to list
            
        Returns:
            List of directory names
        """
        try:
            if not path.exists():
                return []
            return [d.name for d in path.iterdir() if d.is_dir()]
        except Exception as e:
            logger.error(f"Failed to list directories in {path}: {e}")
            raise FileSystemError(f"Failed to list directories: {e}", str(path))

    def get_change_path(self, change_id: str) -> Path:
        """Get path to a change directory.
        
        Args:
            change_id: Change identifier
            
        Returns:
            Path to change directory
        """
        return self.changes_path / change_id

    def get_spec_path(self, spec_id: str) -> Path:
        """Get path to a spec file.
        
        Args:
            spec_id: Spec identifier (capability name)
            
        Returns:
            Path to spec file
        """
        return self.specs_path / spec_id / "spec.md"

    def change_exists(self, change_id: str) -> bool:
        """Check if a change exists.
        
        Args:
            change_id: Change identifier
            
        Returns:
            True if change exists
        """
        change_path = self.get_change_path(change_id)
        return self.directory_exists(change_path)

    def spec_exists(self, spec_id: str) -> bool:
        """Check if a spec exists.
        
        Args:
            spec_id: Spec identifier
            
        Returns:
            True if spec exists
        """
        spec_path = self.get_spec_path(spec_id)
        return self.file_exists(spec_path)

    def list_changes(self) -> list[str]:
        """List all active changes.
        
        Returns:
            List of change IDs
        """
        self.ensure_initialized()
        if not self.changes_path.exists():
            return []
        
        changes = self.list_directories(self.changes_path)
        # Exclude archive directory
        return [c for c in changes if c != self.ARCHIVE_DIR]

    def list_specs(self) -> list[str]:
        """List all specs.
        
        Returns:
            List of spec IDs
        """
        self.ensure_initialized()
        if not self.specs_path.exists():
            return []
        
        return self.list_directories(self.specs_path)
