"""GitMap MCP Server.

MCP server that exposes GitMap functionality as tools for Cursor agents.

Execution Context:
    MCP server - run via `python main.py` or `python -m gitmap_mcp.main`

Dependencies:
    - mcp: Model Context Protocol SDK
    - gitmap_core: Core GitMap functionality

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Load .env file from workspace root at startup
try:
    from dotenv import load_dotenv
    
    # Find workspace root by looking for .env file
    # Start from current file location and search up
    current = Path(__file__).resolve().parent
    workspace_root = None
    
    # Search up to 5 levels to find workspace root with .env
    for _ in range(5):
        env_file = current / ".env"
        if env_file.exists():
            workspace_root = current
            load_dotenv(env_file, override=True)
            break
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
    
    # If not found, try loading from common workspace locations
    if workspace_root is None:
        # Try common workspace root locations
        possible_roots = [
            Path.cwd(),
            Path.cwd().parent,
            Path(__file__).resolve().parent.parent.parent.parent,  # /app from apps/mcp/gitmap-mcp/main.py
        ]
        for root in possible_roots:
            env_file = root / ".env"
            if env_file.exists():
                load_dotenv(env_file, override=True)
                break
except ImportError:
    # dotenv not available, will rely on system environment variables
    pass

# Import tools - try package import first, then fall back to direct import
try:
    from gitmap_mcp.scripts.tools.branch_tools import gitmap_branch_create
    from gitmap_mcp.scripts.tools.branch_tools import gitmap_branch_delete
    from gitmap_mcp.scripts.tools.branch_tools import gitmap_branch_list
    from gitmap_mcp.scripts.tools.branch_tools import gitmap_checkout
    from gitmap_mcp.scripts.tools.commit_tools import gitmap_commit
    from gitmap_mcp.scripts.tools.commit_tools import gitmap_diff
    from gitmap_mcp.scripts.tools.commit_tools import gitmap_log
    from gitmap_mcp.scripts.tools.commit_tools import gitmap_merge
    from gitmap_mcp.scripts.tools.context_tools import context_explain_changes
    from gitmap_mcp.scripts.tools.context_tools import context_get_timeline
    from gitmap_mcp.scripts.tools.context_tools import context_record_lesson
    from gitmap_mcp.scripts.tools.context_tools import context_search_history
    from gitmap_mcp.scripts.tools.layer_tools import gitmap_layer_settings_merge
    from gitmap_mcp.scripts.tools.portal_tools import gitmap_list_groups
    from gitmap_mcp.scripts.tools.portal_tools import gitmap_list_maps
    from gitmap_mcp.scripts.tools.portal_tools import gitmap_notify
    from gitmap_mcp.scripts.tools.remote_tools import gitmap_pull
    from gitmap_mcp.scripts.tools.remote_tools import gitmap_push
    from gitmap_mcp.scripts.tools.repository_tools import gitmap_clone
    from gitmap_mcp.scripts.tools.repository_tools import gitmap_init
    from gitmap_mcp.scripts.tools.repository_tools import gitmap_status
    from gitmap_mcp.scripts.tools.stash_tools import gitmap_stash_drop
    from gitmap_mcp.scripts.tools.stash_tools import gitmap_stash_list
    from gitmap_mcp.scripts.tools.stash_tools import gitmap_stash_pop
    from gitmap_mcp.scripts.tools.stash_tools import gitmap_stash_push
except ImportError:
    # Fall back to direct import when running as script
    _scripts_dir = Path(__file__).parent / "scripts"
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))

    from tools.branch_tools import gitmap_branch_create
    from tools.branch_tools import gitmap_branch_delete
    from tools.branch_tools import gitmap_branch_list
    from tools.branch_tools import gitmap_checkout
    from tools.commit_tools import gitmap_commit
    from tools.commit_tools import gitmap_diff
    from tools.commit_tools import gitmap_log
    from tools.commit_tools import gitmap_merge
    from tools.context_tools import context_explain_changes
    from tools.context_tools import context_get_timeline
    from tools.context_tools import context_record_lesson
    from tools.context_tools import context_search_history
    from tools.layer_tools import gitmap_layer_settings_merge
    from tools.portal_tools import gitmap_list_groups
    from tools.portal_tools import gitmap_list_maps
    from tools.portal_tools import gitmap_notify
    from tools.remote_tools import gitmap_pull
    from tools.remote_tools import gitmap_push
    from tools.repository_tools import gitmap_clone
    from tools.repository_tools import gitmap_init
    from tools.repository_tools import gitmap_status
    from tools.stash_tools import gitmap_stash_drop
    from tools.stash_tools import gitmap_stash_list
    from tools.stash_tools import gitmap_stash_pop
    from tools.stash_tools import gitmap_stash_push

# Create MCP server
mcp = FastMCP("GitMap MCP Server", json_response=True)

# Register repository tools
mcp.tool()(gitmap_init)
mcp.tool()(gitmap_clone)
mcp.tool()(gitmap_status)

# Register branch tools
mcp.tool()(gitmap_branch_list)
mcp.tool()(gitmap_branch_create)
mcp.tool()(gitmap_branch_delete)
mcp.tool()(gitmap_checkout)

# Register commit tools
mcp.tool()(gitmap_commit)
mcp.tool()(gitmap_log)
mcp.tool()(gitmap_diff)
mcp.tool()(gitmap_merge)

# Register remote tools
mcp.tool()(gitmap_push)
mcp.tool()(gitmap_pull)

# Register layer tools
mcp.tool()(gitmap_layer_settings_merge)

# Register portal tools
mcp.tool()(gitmap_notify)
mcp.tool()(gitmap_list_maps)
mcp.tool()(gitmap_list_groups)

# Register stash tools
mcp.tool()(gitmap_stash_push)
mcp.tool()(gitmap_stash_pop)
mcp.tool()(gitmap_stash_list)
mcp.tool()(gitmap_stash_drop)

# Register context tools
mcp.tool()(context_search_history)
mcp.tool()(context_get_timeline)
mcp.tool()(context_explain_changes)
mcp.tool()(context_record_lesson)


def main() -> int:
    """Main entry point for GitMap MCP server.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Run MCP server with stdio transport (standard for MCP)
        mcp.run(transport="stdio")
        return 0
    except Exception as server_error:
        print(f"Error: {server_error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
