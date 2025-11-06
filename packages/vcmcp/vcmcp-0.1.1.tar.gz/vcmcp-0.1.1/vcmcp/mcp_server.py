#!/usr/bin/env python3
"""
VCMCP MCP Server

Model Context Protocol server for VCMCP (Version Control Model Protocol).
This server provides MCP tools for AI agents to use VCMCP functionality.
"""

import asyncio
import json
import sys
from typing import List, Dict, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions

# Import VCMCP functions
from vcmcp.core import save, restore, diff, list_checkpoints

# Initialize the server
server = Server("vcmcp")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available VCMCP tools."""
    return [
        Tool(
            name="vcmcp_save",
            description="Save a checkpoint using VCMCP (Version Control Model Protocol)",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description": "Name of the agent creating the checkpoint"
                    },
                    "step": {
                        "type": "integer",
                        "description": "Step number in the agent's workflow"
                    },
                    "description": {
                        "type": "string",
                        "description": "A short description of the changes"
                    },
                    "tools_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tools used by the agent"
                    }
                },
                "required": ["agent", "step"]
            }
        ),
        Tool(
            name="vcmcp_list",
            description="List all VCMCP checkpoints, optionally filtered by agent and step",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description": "Filter by agent name (optional)"
                    },
                    "step": {
                        "type": "integer",
                        "description": "Filter by step number (optional)"
                    }
                }
            }
        ),
        Tool(
            name="vcmcp_restore",
            description="Restore to a specific checkpoint using VCMCP",
            inputSchema={
                "type": "object",
                "properties": {
                    "checkpoint": {
                        "type": "string",
                        "description": "Checkpoint tag to restore to (e.g., vcmcp/agent/step@timestamp)"
                    }
                },
                "required": ["checkpoint"]
            }
        ),
        Tool(
            name="vcmcp_diff",
            description="Show diff between two checkpoints using VCMCP",
            inputSchema={
                "type": "object",
                "properties": {
                    "checkpoint1": {
                        "type": "string",
                        "description": "First checkpoint for comparison"
                    },
                    "checkpoint2": {
                        "type": "string",
                        "description": "Second checkpoint for comparison"
                    }
                },
                "required": ["checkpoint1", "checkpoint2"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle VCMCP tool calls."""
    try:
        if name == "vcmcp_save":
            agent = arguments.get("agent", "unknown")
            step = arguments.get("step", 1)
            description = arguments.get("description", f"Step {step}")
            tools_used = arguments.get("tools_used", [])
            
            # Save checkpoint
            tag = save(
                agent=agent,
                step=step,
                description=description,
                tools_used=tools_used
            )
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "checkpoint_tag": tag,
                        "agent": agent,
                        "step": step,
                        "description": description,
                        "tools_used": tools_used,
                        "message": f"Checkpoint saved successfully as {tag}"
                    }, indent=2)
                )
            ]
            
        elif name == "vcmcp_list":
            agent = arguments.get("agent")
            step = arguments.get("step")
            
            # List checkpoints
            checkpoints = list_checkpoints(agent=agent, step=step)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "checkpoints": checkpoints,
                        "filter": {"agent": agent, "step": step},
                        "total": len(checkpoints)
                    }, indent=2)
                )
            ]
            
        elif name == "vcmcp_restore":
            checkpoint = arguments.get("checkpoint")
            
            if not checkpoint:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": "checkpoint parameter is required"
                        }, indent=2)
                    )
                ]
            
            # Restore checkpoint
            restore(checkpoint)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "checkpoint": checkpoint,
                        "message": f"Successfully restored to checkpoint {checkpoint}"
                    }, indent=2)
                )
            ]
            
        elif name == "vcmcp_diff":
            checkpoint1 = arguments.get("checkpoint1")
            checkpoint2 = arguments.get("checkpoint2")
            
            if not checkpoint1 or not checkpoint2:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": "Both checkpoint1 and checkpoint2 parameters are required"
                        }, indent=2)
                    )
                ]
            
            # Get diff
            diff_output = diff(checkpoint1, checkpoint2)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "checkpoint1": checkpoint1,
                        "checkpoint2": checkpoint2,
                        "diff": diff_output
                    }, indent=2)
                )
            ]
            
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Unknown tool: {name}"
                    }, indent=2)
                )
            ]
            
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "tool": name
                }, indent=2)
            )
        ]


async def main():
    """Main entry point for the VCMCP MCP server."""
    print("VCMCP MCP Server starting...", file=sys.stderr)
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="vcmcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={},
                    ),
                ),
            )
    except KeyboardInterrupt:
        print("\nVCMCP MCP server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"VCMCP MCP server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
