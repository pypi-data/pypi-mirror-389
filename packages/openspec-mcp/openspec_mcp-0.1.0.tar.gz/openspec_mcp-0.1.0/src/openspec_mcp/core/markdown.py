"""Markdown parsing and generation for OpenSpec documents."""

import re
from typing import Optional
from ..models import Task, TaskProgress
from ..utils import logger


class MarkdownParser:
    """Parser for OpenSpec markdown documents."""

    # Task patterns matching OpenSpec format
    TASK_PATTERN = re.compile(r"^[-*]\s+\[([ x])\]\s+(.+)$", re.IGNORECASE)
    COMPLETED_PATTERN = re.compile(r"^[-*]\s+\[x\]", re.IGNORECASE)

    @staticmethod
    def parse_tasks(content: str) -> list[Task]:
        """Parse tasks from tasks.md content.
        
        Args:
            content: Content of tasks.md file
            
        Returns:
            List of Task objects
        """
        tasks = []
        lines = content.split("\n")
        
        for line in lines:
            match = MarkdownParser.TASK_PATTERN.match(line.strip())
            if match:
                completed = match.group(1).lower() == "x"
                description = match.group(2).strip()
                
                # Generate simple task ID based on position
                task_id = str(len(tasks) + 1)
                
                tasks.append(Task(
                    id=task_id,
                    description=description,
                    completed=completed,
                    subtasks=[]
                ))
        
        logger.debug(f"Parsed {len(tasks)} tasks from content")
        return tasks

    @staticmethod
    def count_tasks(content: str) -> TaskProgress:
        """Count total and completed tasks.
        
        Args:
            content: Content of tasks.md file
            
        Returns:
            TaskProgress with counts
        """
        lines = content.split("\n")
        total = 0
        completed = 0
        
        for line in lines:
            if MarkdownParser.TASK_PATTERN.match(line.strip()):
                total += 1
                if MarkdownParser.COMPLETED_PATTERN.match(line.strip()):
                    completed += 1
        
        return TaskProgress(completed=completed, total=total)

    @staticmethod
    def update_task_status(content: str, task_id: str, completed: bool) -> str:
        """Update task completion status in tasks.md content.
        
        Args:
            content: Original tasks.md content
            task_id: Task ID to update
            completed: New completion status
            
        Returns:
            Updated content
        """
        lines = content.split("\n")
        task_index = 0
        
        for i, line in enumerate(lines):
            if MarkdownParser.TASK_PATTERN.match(line.strip()):
                task_index += 1
                if str(task_index) == task_id:
                    # Update the checkbox
                    checkbox = "[x]" if completed else "[ ]"
                    # Preserve the line format (- or *)
                    prefix = "-" if line.strip().startswith("-") else "*"
                    match = MarkdownParser.TASK_PATTERN.match(line.strip())
                    if match:
                        description = match.group(2)
                        # Preserve original indentation
                        indent = len(line) - len(line.lstrip())
                        lines[i] = " " * indent + f"{prefix} {checkbox} {description}"
                        logger.debug(f"Updated task {task_id} to completed={completed}")
                    break
        
        return "\n".join(lines)

    @staticmethod
    def format_task_status(progress: TaskProgress) -> str:
        """Format task progress as a status string.
        
        Args:
            progress: Task progress
            
        Returns:
            Formatted status string
        """
        if progress.total == 0:
            return "No tasks"
        if progress.completed == progress.total:
            return "✓ Complete"
        return f"{progress.completed}/{progress.total} tasks"

    @staticmethod
    def parse_requirements_count(content: str) -> int:
        """Count requirements in a spec document.
        
        Args:
            content: Spec content
            
        Returns:
            Number of requirements
        """
        # Count "### Requirement:" headers
        pattern = re.compile(r"^###\s+Requirement:", re.MULTILINE)
        matches = pattern.findall(content)
        return len(matches)

    @staticmethod
    def extract_purpose(content: str) -> str:
        """Extract purpose section from spec.
        
        Args:
            content: Spec content
            
        Returns:
            Purpose text or empty string
        """
        # Look for ## Purpose section
        pattern = re.compile(r"##\s+Purpose\s*\n(.*?)(?=\n##|\Z)", re.DOTALL)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def generate_proposal_template(change_id: str, description: str) -> str:
        """Generate proposal.md template.
        
        Args:
            change_id: Change identifier
            description: Change description
            
        Returns:
            Proposal template content
        """
        return f"""# {change_id}

## Why

{description}

## What

<!-- Describe what will be changed -->

## How

<!-- Describe how the change will be implemented -->

## Impact

<!-- Describe the impact of this change -->
"""

    @staticmethod
    def generate_tasks_template() -> str:
        """Generate tasks.md template.
        
        Returns:
            Tasks template content
        """
        return """# Tasks

## 1. Implementation

- [ ] Task 1
- [ ] Task 2

## 2. Testing

- [ ] Write tests
- [ ] Manual testing

## 3. Documentation

- [ ] Update documentation
"""

    @staticmethod
    def generate_spec_template(capability: str) -> str:
        """Generate spec.md template for a capability.
        
        Args:
            capability: Capability name
            
        Returns:
            Spec template content
        """
        return f"""# {capability.title()} Specification

## Purpose

<!-- Describe the purpose of this capability -->

## Requirements

### Requirement: Example Requirement

**User Story:** As a user, I want to...

#### Acceptance Criteria

1. WHEN condition THEN system SHALL behavior
2. IF condition THEN system SHALL behavior

#### Scenario: Happy Path

1. User does X
2. System does Y
3. Result is Z
"""
