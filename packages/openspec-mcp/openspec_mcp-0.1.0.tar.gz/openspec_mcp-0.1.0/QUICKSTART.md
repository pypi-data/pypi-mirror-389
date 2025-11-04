# OpenSpec MCP - Quick Start Guide

## What is OpenSpec MCP?

OpenSpec MCP is a server that lets AI assistants (like Cursor, Claude Desktop) directly interact with your OpenSpec projects. Instead of manually creating files and managing specs, your AI assistant can do it for you!

## Installation

### Option 1: Direct Run (Recommended)

No installation needed! Just configure your AI tool to use:

```bash
uvx openspec-mcp
```

### Option 2: Install Globally

```bash
pip install openspec-mcp
```

## Setup in Cursor

1. Open your project in Cursor

2. Create or edit `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "openspec": {
      "command": "uvx",
      "args": ["openspec-mcp"],
      "disabled": false,
      "autoApprove": [
        "list_changes",
        "list_specs",
        "show_change",
        "read_spec",
        "read_tasks"
      ]
    }
  }
}
```

3. Restart Cursor

4. Test it! Try asking: "List my OpenSpec changes"

## Setup in Claude Desktop

1. Find your config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add OpenSpec MCP:

```json
{
  "mcpServers": {
    "openspec": {
      "command": "uvx",
      "args": ["openspec-mcp"]
    }
  }
}
```

3. Restart Claude Desktop

## First Steps

### 1. Initialize OpenSpec

In your AI assistant, say:

```
Initialize OpenSpec in this project
```

This creates the `openspec/` directory structure.

### 2. Create Your First Change

```
Create an OpenSpec change proposal for adding user authentication
```

The AI will:
- Create a change directory
- Generate proposal.md
- Generate tasks.md
- Set up spec directories

### 3. View Your Changes

```
Show me all OpenSpec changes
```

You'll see a list with task progress for each change.

### 4. Work on the Change

```
Show me the details of the add-user-authentication change
```

The AI can now see your proposal, tasks, and specs.

### 5. Update Task Status

```
Mark task 1 as complete in the add-user-authentication change
```

### 6. Validate Before Archiving

```
Validate the add-user-authentication change
```

The AI will check for any format issues.

## Common Commands

### Project Management
- "Initialize OpenSpec"
- "List all OpenSpec changes"
- "List all OpenSpec specs"

### Change Management
- "Create a change proposal for [feature]"
- "Show me the [change-id] change"
- "What's the progress on [change-id]?"

### Task Management
- "Show me tasks for [change-id]"
- "Mark task [number] as complete in [change-id]"
- "Mark task [number] as incomplete in [change-id]"

### Specification Management
- "Show me the [spec-name] specification"
- "How many requirements are in [spec-name]?"

### Validation
- "Validate the [change-id] change"
- "Check if [change-id] is ready to archive"

## Example Workflow

Here's a complete workflow example:

```
You: Initialize OpenSpec in this project

AI: ✓ OpenSpec initialized successfully
    Created:
    - openspec/specs/
    - openspec/changes/
    - openspec/project.md
    - openspec/AGENTS.md

You: Create a change proposal for adding a payment gateway

AI: ✓ Change proposal created: openspec/changes/add-payment-gateway
    Files created:
    - proposal.md
    - tasks.md
    - specs/payment/spec.md
    
    Would you like me to help fill in the proposal?

You: Yes, help me fill in the proposal

AI: [Reads proposal.md and helps you complete it]

You: Show me the tasks for add-payment-gateway

AI: Tasks for add-payment-gateway:
    1. [ ] Create payment service interface
    2. [ ] Implement Stripe integration
    3. [ ] Add payment webhooks
    4. [ ] Write tests
    5. [ ] Update documentation
    
    Progress: 0/5 tasks (0%)

You: I've completed task 1, mark it as done

AI: ✓ Task 1 marked as complete
    Progress: 1/5 tasks (20%)

You: Validate the change

AI: ✓ Validation passed
    No issues found in add-payment-gateway
```

## Tips

### Auto-Approve Safe Operations

In Cursor, you can auto-approve read-only operations:

```json
"autoApprove": [
  "list_changes",
  "list_specs",
  "show_change",
  "read_spec",
  "read_tasks"
]
```

This makes the AI faster when just reading information.

### Debug Mode

If something isn't working, enable debug mode:

```json
{
  "mcpServers": {
    "openspec": {
      "command": "uvx",
      "args": ["openspec-mcp"],
      "env": {
        "OPENSPEC_DEBUG": "true"
      }
    }
  }
}
```

Check the logs in your AI tool's console.

### Working Directory

By default, OpenSpec MCP works in the current directory. To specify a different directory:

```json
{
  "mcpServers": {
    "openspec": {
      "command": "uvx",
      "args": ["openspec-mcp"],
      "env": {
        "OPENSPEC_WORKING_DIR": "/path/to/project"
      }
    }
  }
}
```

## Troubleshooting

### "OpenSpec not initialized"

Run: "Initialize OpenSpec in this project"

### "Change not found"

Check the change ID. Run: "List all OpenSpec changes"

### "MCP server not responding"

1. Check your configuration file syntax
2. Restart your AI tool
3. Enable debug mode to see logs

### "Permission denied"

Make sure you have write permissions in the project directory.

## What's Next?

1. **Fill in project.md**: Tell the AI about your project context
2. **Create changes**: Start with small, focused changes
3. **Track progress**: Use tasks to break down work
4. **Validate often**: Check your specs before archiving
5. **Archive completed work**: Keep your changes directory clean

## Learn More

- [Full Documentation](README.md)
- [Development Guide](DEVELOPMENT.md)
- [OpenSpec Documentation](https://github.com/Fission-AI/OpenSpec)
- [MCP Protocol](https://modelcontextprotocol.io/)

## Getting Help

- Check the logs (enable debug mode)
- Read the error messages (they include suggestions)
- Ask your AI assistant: "What OpenSpec tools are available?"

## Example Prompts

Try these with your AI assistant:

```
"Explain the OpenSpec workflow to me"

"Create a change proposal for [your feature]"

"Help me break down this change into tasks"

"Show me what specs need to be updated"

"Validate all my changes"

"What's the progress on all my changes?"
```

Happy spec-driven development! 🚀
