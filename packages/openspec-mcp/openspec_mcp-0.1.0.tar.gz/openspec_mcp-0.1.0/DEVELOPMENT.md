# Development Guide

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Fission-AI/OpenSpec
cd OpenSpec/openspec-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=openspec_mcp --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_filesystem.py
```

Run with verbose output:
```bash
pytest -v
```

## Code Quality

Format code with Black:
```bash
black src tests
```

Lint with Ruff:
```bash
ruff check src tests
```

Type check with mypy:
```bash
mypy src
```

## Testing the MCP Server

### Using MCP Inspector

The MCP Inspector is a great tool for testing MCP servers:

```bash
npx @modelcontextprotocol/inspector uvx openspec-mcp
```

This will open a web interface where you can:
- See all available tools
- Test tool calls with different parameters
- View responses and errors

### Manual Testing

1. Start the server:
```bash
python -m openspec_mcp
```

2. The server communicates via stdio, so you'll need an MCP client to interact with it.

### Testing in Cursor

1. Add the configuration to `.kiro/settings/mcp.json`:
```json
{
  "mcpServers": {
    "openspec-dev": {
      "command": "python",
      "args": ["-m", "openspec_mcp"],
      "env": {
        "OPENSPEC_DEBUG": "true",
        "PYTHONPATH": "/path/to/openspec-mcp/src"
      },
      "disabled": false
    }
  }
}
```

2. Restart Cursor and test the tools.

## Project Structure

```
openspec-mcp/
├── src/
│   └── openspec_mcp/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── server.py            # MCP server implementation
│       ├── core/                # Core business logic
│       │   ├── filesystem.py    # File system operations
│       │   ├── markdown.py      # Markdown parsing
│       │   ├── change_manager.py
│       │   ├── spec_manager.py
│       │   ├── validator.py
│       │   └── init.py
│       ├── models/              # Data models
│       │   ├── change.py
│       │   ├── spec.py
│       │   └── validation.py
│       └── utils/               # Utilities
│           ├── errors.py
│           └── logger.py
├── tests/                       # Test files
├── examples/                    # Configuration examples
├── pyproject.toml              # Project configuration
└── README.md                   # User documentation
```

## Adding New Tools

1. Add the tool definition in `server.py` `list_tools()` method
2. Add the handler method (e.g., `_handle_new_tool`)
3. Add the tool call routing in `call_tool()` method
4. Write tests in `tests/`

Example:

```python
# In list_tools()
Tool(
    name="new_tool",
    description="Description of the new tool",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "Parameter description",
            }
        },
        "required": ["param"],
    },
)

# In call_tool()
elif name == "new_tool":
    result = self._handle_new_tool(arguments)

# Add handler method
def _handle_new_tool(self, arguments: dict) -> dict:
    param = arguments["param"]
    # Implementation
    return {
        "success": True,
        "message": "Tool executed successfully",
        "data": {"result": "value"},
    }
```

## Debugging

Enable debug logging:
```bash
export OPENSPEC_DEBUG=true
export OPENSPEC_LOG_LEVEL=DEBUG
python -m openspec_mcp
```

Logs are written to stderr to avoid interfering with stdio MCP communication.

## Publishing

1. Update version in `pyproject.toml`
2. Build the package:
```bash
python -m build
```

3. Upload to PyPI:
```bash
python -m twine upload dist/*
```

## Common Issues

### Import Errors

Make sure you're in the virtual environment and have installed the package:
```bash
pip install -e ".[dev]"
```

### MCP Connection Issues

Check that:
- The server is running
- The configuration file is correct
- The working directory is correct
- Logs for any error messages (check stderr)

### Test Failures

Run tests with verbose output to see details:
```bash
pytest -vv
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run code quality checks
5. Submit a pull request

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [OpenSpec Documentation](https://github.com/Fission-AI/OpenSpec)
