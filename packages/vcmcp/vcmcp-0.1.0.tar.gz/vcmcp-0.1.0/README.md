# VCMCP - Version Control Model Protocol

VCMCP is a Model Context Protocol (MCP) implementation for version control, checkpoint tracking, and restoration. It provides AI agents with standardized tools for saving, restoring, and comparing code checkpoints during development workflows.

## 🎯 Purpose

VCMCP enables AI agents to:
- **Track Progress**: Save checkpoints at key points in development
- **Roll Back**: Restore to previous states when experiments fail
- **Compare Changes**: View diffs between different checkpoints
- **Collaborate**: Multiple agents can coordinate through shared checkpoints

## 🛠 Installation

```bash
pip install vcmcp
```

## 🚀 Usage

### CLI Interface

```bash
# Save a checkpoint
vcmcp save --agent coder --step 1 --desc "Initial implementation"

# List all checkpoints
vcmcp list

# Restore to a specific checkpoint
vcmcp restore vcmcp/coder/step1@20240522T0930

# Compare two checkpoints
vcmcp diff vcmcp/coder/step1 vcmcp/coder/step2
```

### Python API

```python
from vcmcp import save, restore, diff, list_checkpoints

# Save a checkpoint
tag = save(agent="codex", step=1, description="Initial code")
print(f"Checkpoint saved: {tag}")

# List checkpoints
checkpoints = list_checkpoints(agent="codex")
print(f"Available checkpoints: {checkpoints}")

# Restore checkpoint
restore("vcmcp/codex/step1@20240522T0930")

# Compare checkpoints
diff_output = diff("vcmcp/codex/step1", "vcmcp/codex/step2")
print(diff_output)
```

### MCP Server

Start the MCP server for AI agent integration:

```bash
vcmcp serve --host 0.0.0.0 --port 8000
```

The server exposes MCP-compatible endpoints:
- `GET /schema` - Tool schema definition
- `POST /tool/vcmcp` - Execute VCMCP operations
- `POST /save` - Save checkpoint
- `POST /list` - List checkpoints
- `POST /restore` - Restore checkpoint
- `POST /diff` - Compare checkpoints

## 🔧 MCP Integration

VCMCP implements the Model Context Protocol standard, making it compatible with AI systems that support MCP tools.

### Tool Schema

```json
{
  "type": "function",
  "function": {
    "name": "vcmcp",
    "description": "Version Control Model Protocol for checkpoint management",
    "parameters": {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["save", "list", "restore", "diff"],
          "description": "Operation to perform"
        },
        "agent": {
          "type": "string", 
          "description": "Agent identifier"
        },
        "step": {
          "type": "integer",
          "description": "Step number in workflow"
        },
        "description": {
          "type": "string",
          "description": "Checkpoint description"
        },
        "checkpoint": {
          "type": "string",
          "description": "Checkpoint to restore"
        }
      },
      "required": ["action"]
    }
  }
}
```

### Example MCP Call

```python
import requests

# AI agent calls VCMCP via MCP
response = requests.post("http://localhost:8000/tool/vcmcp", json={
    "name": "vcmcp",
    "arguments": {
        "action": "save",
        "agent": "coding_assistant", 
        "step": 1,
        "description": "First implementation"
    }
})

result = response.json()
print(f"Checkpoint created: {result['tag']}")
```

## 📋 Checkpoint Format

VCMCP uses a structured naming convention:

```
vcmcp/<agent>/<step>@<timestamp>
```

Example: `vcmcp/coder/step3@20240522T0942`

Each checkpoint includes:
- Git commit with structured message
- Metadata file with checkpoint details
- Links to parent checkpoints

## 🔍 File Structure

```
project/
├── .git/
├── .agent-meta/          # VCMCP metadata
│   └── vcmcp-*.json      # Checkpoint metadata
└── your code...
```

## ⚡ Key Features

- **Git-based**: Leverages Git for reliable version control
- **MCP Compatible**: Standard interface for AI systems
- **Multi-agent**: Supports multiple agents working together
- **Metadata Tracking**: Rich metadata for each checkpoint
- **HTTP API**: RESTful interface for integration
- **CLI + Python**: Multiple usage interfaces

## 🏗 Architecture

VCMCP consists of:
- **Core Library**: Version control operations
- **CLI Tool**: Command-line interface
- **HTTP Server**: MCP-compatible REST API
- **Tool Schema**: MCP tool definition

## 🔄 Workflow Example

```python
# AI agent workflow with VCMCP
from vcmcp import save, restore

def implement_feature():
    # Save initial state
    save("agent", 1, "Starting implementation")
    
    try:
        # Make changes...
        implement_code()
        
        # Save progress
        save("agent", 2, "Feature completed")
        
    except Exception as e:
        # Something went wrong, roll back
        restore("vcmcp/agent/step1@timestamp")
        raise e
```

## 📊 Benefits

- **Safety**: Easy rollback from failures
- **Transparency**: Full history of changes
- **Collaboration**: Agents can coordinate via checkpoints
- **Debugging**: Compare working vs broken states
- **Documentation**: Checkpoint descriptions provide context

## 🛡 Requirements

- Python 3.8+
- Git installed and available in PATH
- Network access (for MCP server mode)

## 📦 Package Contents

- `vcmcp.core`: Core version control functionality
- `vcmcp.cli`: Command-line interface
- `vcmcp.server`: HTTP/mcp server
- `vcmcp.tool`: MCP tool schema and handlers

VCMCP provides the essential version control infrastructure that AI agents need for safe, iterative development and collaboration.
