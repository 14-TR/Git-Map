#!/usr/bin/env python3
"""
GitMap Skill Server

Exposes GitMap CLI commands as HTTP tool endpoints for OpenClaw.
Run with: python3 server.py
Access at: http://localhost:7400

Endpoints:
    GET  /health              — Health check
    GET  /tools               — List available tools
    POST /tools/{tool_name}   — Call a tool with JSON body
"""

from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Add skill dir to path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

import tools as gitmap_tools

PORT = 7400

# ---- Tool registry -------------------------------------------------------------------

TOOL_REGISTRY = {
    "gitmap_list": {
        "fn": gitmap_tools.gitmap_list,
        "description": "List available web maps from Portal or ArcGIS Online",
        "params": {
            "query": "Search query (e.g., 'title:MyMap')",
            "owner": "Filter by owner username",
            "tag": "Filter by tag",
            "max_results": "Max results (default 50)",
            "portal_url": "Portal URL",
            "username": "Portal username",
            "password": "Portal password",
            "cwd": "Working directory (optional)",
        },
    },
    "gitmap_status": {
        "fn": gitmap_tools.gitmap_status,
        "description": "Show working tree status for a GitMap repo",
        "params": {
            "cwd": "Path to GitMap repository (required)",
        },
    },
    "gitmap_commit": {
        "fn": gitmap_tools.gitmap_commit,
        "description": "Commit current map state",
        "params": {
            "message": "Commit message (required)",
            "cwd": "Path to GitMap repository (required)",
            "author": "Override commit author (optional)",
        },
    },
    "gitmap_branch": {
        "fn": gitmap_tools.gitmap_branch,
        "description": "List or create branches in a repo",
        "params": {
            "cwd": "Path to GitMap repository (required)",
            "name": "Branch name to create (omit to list)",
            "delete": "If true, delete the named branch",
        },
    },
    "gitmap_diff": {
        "fn": gitmap_tools.gitmap_diff,
        "description": "Show changes between working tree and a branch or commit",
        "params": {
            "cwd": "Path to GitMap repository (required)",
            "branch": "Compare with this branch",
            "commit": "Compare with this commit hash",
        },
    },
    "gitmap_push": {
        "fn": gitmap_tools.gitmap_push,
        "description": "Push committed changes to ArcGIS Portal",
        "params": {
            "cwd": "Path to GitMap repository (required)",
            "branch": "Branch to push (default: current)",
            "portal_url": "Portal URL override",
            "username": "Portal username override",
            "password": "Portal password override",
        },
    },
    "gitmap_pull": {
        "fn": gitmap_tools.gitmap_pull,
        "description": "Pull latest map from ArcGIS Portal",
        "params": {
            "cwd": "Path to GitMap repository (required)",
            "branch": "Branch to pull (default: current)",
            "portal_url": "Portal URL override",
            "username": "Portal username override",
            "password": "Portal password override",
        },
    },
    "gitmap_log": {
        "fn": gitmap_tools.gitmap_log,
        "description": "View commit history for a repo",
        "params": {
            "cwd": "Path to GitMap repository (required)",
            "branch": "Branch to show log for",
            "limit": "Max commits to show",
        },
    },
}


# ---- HTTP Handler --------------------------------------------------------------------

class GitMapHandler(BaseHTTPRequestHandler):
    """Handle tool call requests."""

    def send_json(self, data: dict, status: int = 200) -> None:
        """Send a JSON response."""
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        """Read and parse the JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length:
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode())
            except json.JSONDecodeError:
                return {}
        return {}

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests."""
        path = urllib.parse.urlparse(self.path).path.rstrip("/")

        if path == "/health":
            self.send_json({"ok": True, "service": "gitmap-skill", "port": PORT})

        elif path == "/tools":
            tool_list = [
                {
                    "name": name,
                    "description": info["description"],
                    "params": info["params"],
                }
                for name, info in TOOL_REGISTRY.items()
            ]
            self.send_json({"tools": tool_list, "count": len(tool_list)})

        else:
            self.send_json({"error": f"Not found: {path}"}, 404)

    def do_POST(self) -> None:
        """Handle POST tool calls: POST /tools/{tool_name}"""
        path = urllib.parse.urlparse(self.path).path.rstrip("/")

        if not path.startswith("/tools/"):
            self.send_json({"error": "Not found"}, 404)
            return

        tool_name = path[len("/tools/"):]

        if tool_name not in TOOL_REGISTRY:
            self.send_json(
                {
                    "error": f"Unknown tool: {tool_name}",
                    "available": list(TOOL_REGISTRY.keys()),
                },
                404,
            )
            return

        params = self.read_body()
        tool_fn = TOOL_REGISTRY[tool_name]["fn"]

        try:
            result = tool_fn(**params)
            self.send_json(result)
        except TypeError as type_error:
            self.send_json(
                {
                    "ok": False,
                    "error": f"Invalid parameters: {type_error}",
                    "params": TOOL_REGISTRY[tool_name]["params"],
                },
                400,
            )
        except Exception as general_error:
            self.send_json(
                {
                    "ok": False,
                    "error": f"Tool error: {general_error}",
                },
                500,
            )

    def log_message(self, fmt: str, *args) -> None:  # noqa: D102
        """Custom log prefix."""
        print(f"[GitMap] {args[0]}")


# ---- Entry Point ---------------------------------------------------------------------

def run_server() -> None:
    """Start the GitMap skill HTTP server."""
    server = HTTPServer(("localhost", PORT), GitMapHandler)
    print(f"🗺️  GitMap skill server running at http://localhost:{PORT}")
    print()
    print(f"   Health:  http://localhost:{PORT}/health")
    print(f"   Tools:   http://localhost:{PORT}/tools")
    print(f"   Call:    POST http://localhost:{PORT}/tools/gitmap_status")
    print()
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
