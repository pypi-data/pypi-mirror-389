"""Initialization operations for OpenSpec projects."""

from .filesystem import FileSystemManager
from ..utils import logger


class InitManager:
    """Manages OpenSpec project initialization."""

    def __init__(self, fs: FileSystemManager):
        """Initialize init manager.
        
        Args:
            fs: Filesystem manager instance
        """
        self.fs = fs

    def init_project(self) -> dict:
        """Initialize OpenSpec project structure.
        
        Returns:
            Dictionary with initialization details
        """
        if self.fs.is_initialized():
            logger.info("OpenSpec already initialized")
            return {
                "already_initialized": True,
                "message": "OpenSpec is already initialized in this directory",
            }
        
        # Create directory structure
        created_dirs = []
        
        self.fs.create_directory(self.fs.openspec_path)
        created_dirs.append("openspec")
        
        self.fs.create_directory(self.fs.specs_path)
        created_dirs.append("openspec/specs")
        
        self.fs.create_directory(self.fs.changes_path)
        created_dirs.append("openspec/changes")
        
        self.fs.create_directory(self.fs.archive_path)
        created_dirs.append("openspec/changes/archive")
        
        # Create project.md
        project_content = self._generate_project_template()
        project_path = self.fs.openspec_path / "project.md"
        self.fs.write_file(project_path, project_content)
        
        # Create AGENTS.md
        agents_content = self._generate_agents_template()
        agents_path = self.fs.openspec_path / "AGENTS.md"
        self.fs.write_file(agents_path, agents_content)
        
        logger.info("Initialized OpenSpec project")
        
        return {
            "already_initialized": False,
            "created_dirs": created_dirs,
            "created_files": ["openspec/project.md", "openspec/AGENTS.md"],
        }

    def _generate_project_template(self) -> str:
        """Generate project.md template.
        
        Returns:
            Project template content
        """
        return """# Project Context

## Overview

<!-- Describe your project here -->

## Tech Stack

<!-- List your technologies, frameworks, and tools -->

## Conventions

<!-- Document your coding conventions and standards -->

## Architecture

<!-- Describe your system architecture -->

## Development Workflow

<!-- Describe your development process -->
"""

    def _generate_agents_template(self) -> str:
        """Generate AGENTS.md template.
        
        Returns:
            AGENTS template content
        """
        return """# OpenSpec Workflow

This project uses OpenSpec for spec-driven development.

## Workflow

1. **Create Change Proposal**: Start with a change proposal describing what you want to build
2. **Define Specs**: Create or update specification documents with requirements
3. **Track Tasks**: Break down work into tasks and track progress
4. **Implement**: Build according to the specs
5. **Validate**: Ensure specs are followed
6. **Archive**: Archive completed changes

## Commands

- Create a change: "Create an OpenSpec change proposal for [feature]"
- List changes: "Show me all OpenSpec changes"
- View change: "Show me the details of change [change-id]"
- Update tasks: "Mark task [task-id] as complete in change [change-id]"
- Validate: "Validate the OpenSpec change [change-id]"
- Archive: "Archive the OpenSpec change [change-id]"

## File Structure

```
openspec/
├── project.md          # Project context and conventions
├── AGENTS.md           # This file
├── specs/              # Specification documents
│   └── [capability]/
│       └── spec.md
└── changes/            # Active changes
    ├── [change-id]/
    │   ├── proposal.md
    │   ├── tasks.md
    │   ├── design.md (optional)
    │   └── specs/
    │       └── [capability]/
    │           └── spec.md
    └── archive/        # Completed changes
```

## Best Practices

1. Always start with a clear change proposal
2. Define requirements before implementation
3. Keep specs up to date
4. Track progress with tasks
5. Validate before archiving
"""
