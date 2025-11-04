"""MCP server implementation for OpenSpec."""

import os
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from .core import FileSystemManager, ChangeManager, SpecManager, Validator, InitManager
from .utils import logger, OpenSpecError


class OpenSpecMCPServer:
    """OpenSpec MCP Server."""

    def __init__(self, working_dir: str | None = None):
        """Initialize OpenSpec MCP server.
        
        Args:
            working_dir: Working directory (default: current directory)
        """
        self.working_dir = working_dir or os.getenv("OPENSPEC_WORKING_DIR", ".")
        self.fs = FileSystemManager(self.working_dir)
        self.change_manager = ChangeManager(self.fs)
        self.spec_manager = SpecManager(self.fs)
        self.validator = Validator(self.fs)
        self.init_manager = InitManager(self.fs)
        
        self.server = Server("openspec-mcp")
        self._register_handlers()
        
        logger.info(f"OpenSpec MCP Server initialized in {self.working_dir}")

    def _register_handlers(self) -> None:
        """Register MCP tool handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available OpenSpec tools."""
            return [
                Tool(
                    name="init_openspec",
                    description="Initialize OpenSpec project structure in the current directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "working_dir": {
                                "type": "string",
                                "description": "Working directory path (optional, defaults to current directory)",
                            }
                        },
                    },
                ),
                Tool(
                    name="create_proposal",
                    description="Create a new change proposal with the specified ID and description",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "change_id": {
                                "type": "string",
                                "description": "Change ID in kebab-case (e.g., 'add-two-factor-auth')",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the change",
                            },
                            "capabilities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of affected capabilities (optional)",
                            },
                        },
                        "required": ["change_id", "description"],
                    },
                ),
                Tool(
                    name="list_changes",
                    description="List all active changes with their task progress",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="show_change",
                    description="Show detailed information about a specific change including proposal, tasks, and spec deltas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "change_id": {
                                "type": "string",
                                "description": "Change ID to show",
                            }
                        },
                        "required": ["change_id"],
                    },
                ),
                Tool(
                    name="list_specs",
                    description="List all specification documents with requirement counts",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="read_spec",
                    description="Read a specification document by its ID (capability name)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spec_id": {
                                "type": "string",
                                "description": "Spec ID (capability name)",
                            }
                        },
                        "required": ["spec_id"],
                    },
                ),
                Tool(
                    name="read_tasks",
                    description="Read tasks for a specific change with completion status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "change_id": {
                                "type": "string",
                                "description": "Change ID",
                            }
                        },
                        "required": ["change_id"],
                    },
                ),
                Tool(
                    name="update_task_status",
                    description="Update the completion status of a task in a change",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "change_id": {
                                "type": "string",
                                "description": "Change ID",
                            },
                            "task_id": {
                                "type": "string",
                                "description": "Task ID (number)",
                            },
                            "completed": {
                                "type": "boolean",
                                "description": "Whether the task is completed",
                            },
                        },
                        "required": ["change_id", "task_id", "completed"],
                    },
                ),
                Tool(
                    name="validate_change",
                    description="Validate a change and its documents for format compliance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "change_id": {
                                "type": "string",
                                "description": "Change ID to validate",
                            },
                            "strict": {
                                "type": "boolean",
                                "description": "Use strict validation mode (default: true)",
                            },
                        },
                        "required": ["change_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            try:
                logger.debug(f"Tool called: {name} with arguments: {arguments}")
                
                if name == "init_openspec":
                    result = self._handle_init_openspec(arguments)
                elif name == "create_proposal":
                    result = self._handle_create_proposal(arguments)
                elif name == "list_changes":
                    result = self._handle_list_changes(arguments)
                elif name == "show_change":
                    result = self._handle_show_change(arguments)
                elif name == "list_specs":
                    result = self._handle_list_specs(arguments)
                elif name == "read_spec":
                    result = self._handle_read_spec(arguments)
                elif name == "read_tasks":
                    result = self._handle_read_tasks(arguments)
                elif name == "update_task_status":
                    result = self._handle_update_task_status(arguments)
                elif name == "validate_change":
                    result = self._handle_validate_change(arguments)
                else:
                    result = {
                        "success": False,
                        "error": "UNKNOWN_TOOL",
                        "message": f"Unknown tool: {name}",
                    }
                
                return [TextContent(type="text", text=self._format_result(result))]
                
            except OpenSpecError as e:
                logger.error(f"OpenSpec error in {name}: {e.message}")
                error_result = {
                    "success": False,
                    "error": e.code.value,
                    "message": e.message,
                    "data": e.details,
                }
                return [TextContent(type="text", text=self._format_result(error_result))]
            except Exception as e:
                logger.exception(f"Unexpected error in {name}: {e}")
                error_result = {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Internal error: {str(e)}",
                }
                return [TextContent(type="text", text=self._format_result(error_result))]

    def _format_result(self, result: dict) -> str:
        """Format result as readable text.
        
        Args:
            result: Result dictionary
            
        Returns:
            Formatted text
        """
        import json
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _handle_init_openspec(self, arguments: dict) -> dict:
        """Handle init_openspec tool call."""
        result = self.init_manager.init_project()
        
        if result.get("already_initialized"):
            return {
                "success": True,
                "message": "OpenSpec is already initialized",
                "data": result,
            }
        
        return {
            "success": True,
            "message": "OpenSpec initialized successfully",
            "data": result,
        }

    def _handle_create_proposal(self, arguments: dict) -> dict:
        """Handle create_proposal tool call."""
        change_id = arguments["change_id"]
        description = arguments["description"]
        capabilities = arguments.get("capabilities")
        
        result = self.change_manager.create_change(change_id, description, capabilities)
        
        return {
            "success": True,
            "message": f"Change proposal '{change_id}' created successfully",
            "data": result,
        }

    def _handle_list_changes(self, arguments: dict) -> dict:
        """Handle list_changes tool call."""
        changes = self.change_manager.list_changes()
        
        return {
            "success": True,
            "message": f"Found {len(changes)} active change(s)",
            "data": {"changes": changes},
        }

    def _handle_show_change(self, arguments: dict) -> dict:
        """Handle show_change tool call."""
        change_id = arguments["change_id"]
        result = self.change_manager.show_change(change_id)
        
        return {
            "success": True,
            "message": f"Change '{change_id}' details retrieved",
            "data": result,
        }

    def _handle_list_specs(self, arguments: dict) -> dict:
        """Handle list_specs tool call."""
        specs = self.spec_manager.list_specs()
        
        return {
            "success": True,
            "message": f"Found {len(specs)} spec(s)",
            "data": {"specs": specs},
        }

    def _handle_read_spec(self, arguments: dict) -> dict:
        """Handle read_spec tool call."""
        spec_id = arguments["spec_id"]
        result = self.spec_manager.read_spec(spec_id)
        
        return {
            "success": True,
            "message": f"Spec '{spec_id}' retrieved",
            "data": result,
        }

    def _handle_read_tasks(self, arguments: dict) -> dict:
        """Handle read_tasks tool call."""
        change_id = arguments["change_id"]
        result = self.change_manager.read_tasks(change_id)
        
        return {
            "success": True,
            "message": f"Tasks for change '{change_id}' retrieved",
            "data": result,
        }

    def _handle_update_task_status(self, arguments: dict) -> dict:
        """Handle update_task_status tool call."""
        change_id = arguments["change_id"]
        task_id = arguments["task_id"]
        completed = arguments["completed"]
        
        result = self.change_manager.update_task_status(change_id, task_id, completed)
        
        return {
            "success": True,
            "message": f"Task {task_id} updated to {'completed' if completed else 'incomplete'}",
            "data": result,
        }

    def _handle_validate_change(self, arguments: dict) -> dict:
        """Handle validate_change tool call."""
        change_id = arguments["change_id"]
        strict = arguments.get("strict", True)
        
        validation_result = self.validator.validate_change(change_id, strict)
        
        issues_data = [
            {
                "level": issue.level.value,
                "file": issue.file,
                "message": issue.message,
                "line": issue.line,
            }
            for issue in validation_result.issues
        ]
        
        if validation_result.valid:
            return {
                "success": True,
                "message": f"Change '{change_id}' validation passed",
                "data": {"valid": True, "issues": issues_data},
            }
        else:
            return {
                "success": False,
                "message": f"Change '{change_id}' validation failed",
                "data": {"valid": False, "issues": issues_data},
            }

    def run(self) -> None:
        """Run the MCP server."""
        import asyncio
        from mcp.server.stdio import stdio_server
        
        async def arun():
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
        
        asyncio.run(arun())
