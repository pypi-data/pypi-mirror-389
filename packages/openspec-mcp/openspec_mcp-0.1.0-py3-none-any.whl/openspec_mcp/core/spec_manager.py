"""Specification management operations for OpenSpec."""

from .filesystem import FileSystemManager
from .markdown import MarkdownParser
from ..utils import logger, SpecNotFoundError


class SpecManager:
    """Manages OpenSpec specifications."""

    def __init__(self, fs: FileSystemManager):
        """Initialize spec manager.
        
        Args:
            fs: Filesystem manager instance
        """
        self.fs = fs
        self.parser = MarkdownParser()

    def list_specs(self) -> list[dict]:
        """List all specifications.
        
        Returns:
            List of spec information dictionaries
        """
        self.fs.ensure_initialized()
        
        spec_ids = self.fs.list_specs()
        specs = []
        
        for spec_id in sorted(spec_ids):
            spec_path = self.fs.get_spec_path(spec_id)
            requirements_count = 0
            
            if self.fs.file_exists(spec_path):
                try:
                    content = self.fs.read_file(spec_path)
                    requirements_count = self.parser.parse_requirements_count(content)
                except Exception as e:
                    logger.warning(f"Failed to parse spec {spec_id}: {e}")
            
            specs.append({
                "id": spec_id,
                "requirements_count": requirements_count,
            })
        
        logger.debug(f"Listed {len(specs)} specs")
        return specs

    def read_spec(self, spec_id: str) -> dict:
        """Read a specification document.
        
        Args:
            spec_id: Spec identifier (capability name)
            
        Returns:
            Dictionary with spec details
        """
        self.fs.ensure_initialized()
        
        if not self.fs.spec_exists(spec_id):
            raise SpecNotFoundError(spec_id)
        
        spec_path = self.fs.get_spec_path(spec_id)
        content = self.fs.read_file(spec_path)
        requirements_count = self.parser.parse_requirements_count(content)
        
        logger.debug(f"Read spec: {spec_id}")
        
        return {
            "spec_id": spec_id,
            "content": content,
            "requirements_count": requirements_count,
        }
