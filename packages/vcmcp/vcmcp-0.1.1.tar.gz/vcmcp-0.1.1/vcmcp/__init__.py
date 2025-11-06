"""
VCMCP - Version Control Model Protocol

A lightweight, Git-compatible version control protocol for AI agents
to save, restore, and diff checkpoints during code transformations.
"""

from vcmcp.core import save, restore, diff, list_checkpoints
from vcmcp.tool import format_tool_schema, handle_tool_call, process_tool_request
from vcmcp.server import run_server

__version__ = "0.1.0"
__all__ = [
    "save", "restore", "diff", "list_checkpoints",
    "format_tool_schema", "handle_tool_call", "process_tool_request",
    "run_server"
] 