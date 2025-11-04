"""Change management operations for OpenSpec."""

from pathlib import Path
from typing import Optional
from datetime import datetime

from .filesystem import FileSystemManager
from .markdown import MarkdownParser
from ..models import Change, Task, TaskProgress
from ..utils import logger, ChangeNotFoundError, ChangeExistsError


class ChangeManager:
    """Manages OpenSpec changes."""

    def __init__(self, fs: FileSystemManager):
        """Initialize change manager.
        
        Args:
            fs: Filesystem manager instance
        """
        self.fs = fs
        self.parser = MarkdownParser()

    def create_change(
        self, change_id: str, description: str, capabilities: Optional[list[str]] = None
    ) -> dict:
        """Create a new change proposal.
        
        Args:
            change_id: Change identifier (kebab-case)
            description: Change description
            capabilities: List of affected capabilities
            
        Returns:
            Dictionary with creation details
        """
        self.fs.ensure_initialized()
        
        # Check if change already exists
        if self.fs.change_exists(change_id):
            raise ChangeExistsError(change_id)
        
        # Create change directory structure
        change_path = self.fs.get_change_path(change_id)
        self.fs.create_directory(change_path)
        
        # Create specs directory
        specs_dir = change_path / "specs"
        self.fs.create_directory(specs_dir)
        
        # Generate and write proposal.md
        proposal_content = self.parser.generate_proposal_template(change_id, description)
        self.fs.write_file(change_path / "proposal.md", proposal_content)
        
        # Generate and write tasks.md
        tasks_content = self.parser.generate_tasks_template()
        self.fs.write_file(change_path / "tasks.md", tasks_content)
        
        # Create spec deltas for specified capabilities
        files_created = ["proposal.md", "tasks.md"]
        if capabilities:
            for capability in capabilities:
                capability_dir = specs_dir / capability
                self.fs.create_directory(capability_dir)
                spec_content = self.parser.generate_spec_template(capability)
                self.fs.write_file(capability_dir / "spec.md", spec_content)
                files_created.append(f"specs/{capability}/spec.md")
        
        logger.info(f"Created change: {change_id}")
        
        return {
            "change_id": change_id,
            "path": str(change_path.relative_to(self.fs.working_dir)),
            "files_created": files_created,
        }

    def list_changes(self) -> list[dict]:
        """List all active changes with progress.
        
        Returns:
            List of change information dictionaries
        """
        self.fs.ensure_initialized()
        
        change_ids = self.fs.list_changes()
        changes = []
        
        for change_id in sorted(change_ids):
            progress = self.get_task_progress(change_id)
            changes.append({
                "id": change_id,
                "tasks_completed": progress.completed,
                "tasks_total": progress.total,
                "progress": f"{progress.percentage}%",
            })
        
        logger.debug(f"Listed {len(changes)} changes")
        return changes

    def show_change(self, change_id: str) -> dict:
        """Show detailed information about a change.
        
        Args:
            change_id: Change identifier
            
        Returns:
            Dictionary with change details
        """
        self.fs.ensure_initialized()
        
        if not self.fs.change_exists(change_id):
            raise ChangeNotFoundError(change_id)
        
        change_path = self.fs.get_change_path(change_id)
        
        # Read proposal
        proposal_path = change_path / "proposal.md"
        proposal = self.fs.read_file(proposal_path) if self.fs.file_exists(proposal_path) else ""
        
        # Read tasks
        tasks_path = change_path / "tasks.md"
        tasks = self.fs.read_file(tasks_path) if self.fs.file_exists(tasks_path) else ""
        
        # Read design (optional)
        design_path = change_path / "design.md"
        design = self.fs.read_file(design_path) if self.fs.file_exists(design_path) else None
        
        # Read spec deltas
        spec_deltas = {}
        specs_dir = change_path / "specs"
        if self.fs.directory_exists(specs_dir):
            for capability_dir in specs_dir.iterdir():
                if capability_dir.is_dir():
                    spec_file = capability_dir / "spec.md"
                    if self.fs.file_exists(spec_file):
                        spec_deltas[capability_dir.name] = self.fs.read_file(spec_file)
        
        logger.debug(f"Showed change: {change_id}")
        
        return {
            "change_id": change_id,
            "proposal": proposal,
            "tasks": tasks,
            "design": design,
            "spec_deltas": spec_deltas,
        }

    def get_task_progress(self, change_id: str) -> TaskProgress:
        """Get task progress for a change.
        
        Args:
            change_id: Change identifier
            
        Returns:
            TaskProgress object
        """
        if not self.fs.change_exists(change_id):
            raise ChangeNotFoundError(change_id)
        
        tasks_path = self.fs.get_change_path(change_id) / "tasks.md"
        
        if not self.fs.file_exists(tasks_path):
            return TaskProgress(completed=0, total=0)
        
        content = self.fs.read_file(tasks_path)
        return self.parser.count_tasks(content)

    def read_tasks(self, change_id: str) -> dict:
        """Read tasks for a change.
        
        Args:
            change_id: Change identifier
            
        Returns:
            Dictionary with tasks and progress
        """
        self.fs.ensure_initialized()
        
        if not self.fs.change_exists(change_id):
            raise ChangeNotFoundError(change_id)
        
        tasks_path = self.fs.get_change_path(change_id) / "tasks.md"
        
        if not self.fs.file_exists(tasks_path):
            return {
                "change_id": change_id,
                "tasks": [],
                "progress": {"completed": 0, "total": 0},
            }
        
        content = self.fs.read_file(tasks_path)
        tasks = self.parser.parse_tasks(content)
        progress = self.parser.count_tasks(content)
        
        return {
            "change_id": change_id,
            "tasks": [
                {
                    "id": task.id,
                    "description": task.description,
                    "completed": task.completed,
                }
                for task in tasks
            ],
            "progress": {"completed": progress.completed, "total": progress.total},
        }

    def update_task_status(self, change_id: str, task_id: str, completed: bool) -> dict:
        """Update task completion status.
        
        Args:
            change_id: Change identifier
            task_id: Task identifier
            completed: New completion status
            
        Returns:
            Dictionary with update result
        """
        self.fs.ensure_initialized()
        
        if not self.fs.change_exists(change_id):
            raise ChangeNotFoundError(change_id)
        
        tasks_path = self.fs.get_change_path(change_id) / "tasks.md"
        
        if not self.fs.file_exists(tasks_path):
            raise ChangeNotFoundError(f"tasks.md not found for change {change_id}")
        
        # Read current content
        content = self.fs.read_file(tasks_path)
        
        # Update task status
        updated_content = self.parser.update_task_status(content, task_id, completed)
        
        # Write back
        self.fs.write_file(tasks_path, updated_content)
        
        # Get updated progress
        progress = self.parser.count_tasks(updated_content)
        
        logger.info(f"Updated task {task_id} in change {change_id} to completed={completed}")
        
        return {
            "task_id": task_id,
            "completed": completed,
            "progress": {"completed": progress.completed, "total": progress.total},
        }
