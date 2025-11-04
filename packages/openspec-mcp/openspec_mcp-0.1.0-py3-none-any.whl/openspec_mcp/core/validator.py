"""Validation logic for OpenSpec documents."""

import re
from pathlib import Path

from .filesystem import FileSystemManager
from ..models import ValidationResult, ValidationIssue, IssueLevel
from ..utils import logger, ChangeNotFoundError


class Validator:
    """Validates OpenSpec documents."""

    def __init__(self, fs: FileSystemManager):
        """Initialize validator.
        
        Args:
            fs: Filesystem manager instance
        """
        self.fs = fs

    def validate_change(self, change_id: str, strict: bool = True) -> ValidationResult:
        """Validate a change and its documents.
        
        Args:
            change_id: Change identifier
            strict: Use strict validation mode
            
        Returns:
            ValidationResult object
        """
        self.fs.ensure_initialized()
        
        if not self.fs.change_exists(change_id):
            raise ChangeNotFoundError(change_id)
        
        issues = []
        change_path = self.fs.get_change_path(change_id)
        
        # Check required files
        required_files = ["proposal.md", "tasks.md"]
        for filename in required_files:
            file_path = change_path / filename
            if not self.fs.file_exists(file_path):
                issues.append(
                    ValidationIssue(
                        level=IssueLevel.ERROR,
                        file=filename,
                        message=f"Required file '{filename}' is missing",
                    )
                )
        
        # Validate proposal.md
        proposal_path = change_path / "proposal.md"
        if self.fs.file_exists(proposal_path):
            content = self.fs.read_file(proposal_path)
            issues.extend(self._validate_proposal(content, "proposal.md", strict))
        
        # Validate tasks.md
        tasks_path = change_path / "tasks.md"
        if self.fs.file_exists(tasks_path):
            content = self.fs.read_file(tasks_path)
            issues.extend(self._validate_tasks(content, "tasks.md", strict))
        
        # Validate spec deltas
        specs_dir = change_path / "specs"
        if self.fs.directory_exists(specs_dir):
            for capability_dir in specs_dir.iterdir():
                if capability_dir.is_dir():
                    spec_file = capability_dir / "spec.md"
                    if self.fs.file_exists(spec_file):
                        content = self.fs.read_file(spec_file)
                        rel_path = f"specs/{capability_dir.name}/spec.md"
                        issues.extend(self._validate_spec(content, rel_path, strict))
        
        valid = not any(issue.level == IssueLevel.ERROR for issue in issues)
        
        logger.debug(f"Validated change {change_id}: valid={valid}, issues={len(issues)}")
        
        return ValidationResult(valid=valid, issues=issues)

    def _validate_proposal(self, content: str, filename: str, strict: bool) -> list[ValidationIssue]:
        """Validate proposal.md content.
        
        Args:
            content: Proposal content
            filename: File name for error reporting
            strict: Use strict validation
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for required sections
        required_sections = ["## Why", "## What", "## How"]
        for section in required_sections:
            if section not in content:
                level = IssueLevel.ERROR if strict else IssueLevel.WARNING
                issues.append(
                    ValidationIssue(
                        level=level,
                        file=filename,
                        message=f"Missing required section: {section}",
                    )
                )
        
        # Check if sections have content
        for section in required_sections:
            if section in content:
                # Extract content after section header
                pattern = re.compile(rf"{re.escape(section)}\s*\n(.*?)(?=\n##|\Z)", re.DOTALL)
                match = pattern.search(content)
                if match:
                    section_content = match.group(1).strip()
                    # Check if it's just a comment or empty
                    if not section_content or section_content.startswith("<!--"):
                        level = IssueLevel.WARNING
                        issues.append(
                            ValidationIssue(
                                level=level,
                                file=filename,
                                message=f"Section {section} appears to be empty or placeholder",
                            )
                        )
        
        return issues

    def _validate_tasks(self, content: str, filename: str, strict: bool) -> list[ValidationIssue]:
        """Validate tasks.md content.
        
        Args:
            content: Tasks content
            filename: File name for error reporting
            strict: Use strict validation
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for at least one task
        task_pattern = re.compile(r"^[-*]\s+\[([ x])\]", re.MULTILINE | re.IGNORECASE)
        tasks = task_pattern.findall(content)
        
        if not tasks:
            level = IssueLevel.WARNING
            issues.append(
                ValidationIssue(
                    level=level,
                    file=filename,
                    message="No tasks found in tasks.md",
                )
            )
        
        return issues

    def _validate_spec(self, content: str, filename: str, strict: bool) -> list[ValidationIssue]:
        """Validate spec.md content.
        
        Args:
            content: Spec content
            filename: File name for error reporting
            strict: Use strict validation
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for Purpose section
        if "## Purpose" not in content:
            level = IssueLevel.ERROR if strict else IssueLevel.WARNING
            issues.append(
                ValidationIssue(
                    level=level,
                    file=filename,
                    message="Missing required section: ## Purpose",
                )
            )
        
        # Check for Requirements section
        if "## Requirements" not in content:
            level = IssueLevel.ERROR if strict else IssueLevel.WARNING
            issues.append(
                ValidationIssue(
                    level=level,
                    file=filename,
                    message="Missing required section: ## Requirements",
                )
            )
        
        # Check for at least one requirement
        req_pattern = re.compile(r"^###\s+Requirement:", re.MULTILINE)
        requirements = req_pattern.findall(content)
        
        if not requirements:
            level = IssueLevel.WARNING
            issues.append(
                ValidationIssue(
                    level=level,
                    file=filename,
                    message="No requirements found in spec",
                )
            )
        
        # Check each requirement has acceptance criteria
        req_blocks = re.split(r"^###\s+Requirement:", content, flags=re.MULTILINE)[1:]
        for i, block in enumerate(req_blocks, 1):
            if "#### Acceptance Criteria" not in block:
                level = IssueLevel.WARNING if not strict else IssueLevel.ERROR
                issues.append(
                    ValidationIssue(
                        level=level,
                        file=filename,
                        message=f"Requirement {i} missing Acceptance Criteria section",
                    )
                )
        
        return issues
