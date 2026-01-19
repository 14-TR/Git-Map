"""GitMap GUI - Web-based graphical interface.

A beautiful web GUI for GitMap version control operations.

This Flask application provides a web-based interface for GitMap operations including:
- Repository management and browsing
- Branch and commit operations
- Merge operations with conflict resolution
- Portal integration (clone, pull, push)
- Real-time diff viewing

The application uses a modular architecture:
- Routes organized into blueprints by feature (repository, branch, commit, etc.)
- Static files (CSS/JS) separated from templates
- Global state management in config.py
- Utility functions in utils.py

Run with: gitmap-gui [--repo PATH] [--port PORT] [--repositories-dir DIR]

Examples:
    gitmap-gui                                    # Scan /app/repositories
    gitmap-gui --repo /path/to/repo               # Use specific repository
    gitmap-gui --port 8080                        # Run on port 8080
    gitmap-gui --repositories-dir /path/to/repos  # Scan custom directory
"""
from __future__ import annotations

import argparse
from pathlib import Path

from flask import Flask

from . import config
from .routes import register_blueprints
from .utils import scan_repositories

# Templates and static files are now in separate files:
# - templates/base.html (HTML structure)
# - static/css/style.css (CSS styles)
# - static/js/app.js (JavaScript)
# HTML Template (DEPRECATED - using templates/base.html instead)
HTML_TEMPLATE = '''
<!-- DEPRECATED: This template string is no longer used. -->
<!-- See templates/base.html instead. -->
'''

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Register all route blueprints
register_blueprints(app)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='GitMap GUI - Web-based interface')
    parser.add_argument('--repo', '-r', type=str, help='Path to GitMap repository')
    parser.add_argument('--repositories-dir', type=str, help='Directory containing GitMap repositories (default: /app/repositories)')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port to run on (default: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    # Set repositories directory (default to /app/repositories)
    if args.repositories_dir:
        config.repositories_dir = Path(args.repositories_dir).resolve()
    else:
        # Default to /app/repositories if it exists, otherwise current directory's repositories subdir
        default_repos_dir = Path('/app/repositories')
        if default_repos_dir.exists():
            config.repositories_dir = default_repos_dir
        else:
            config.repositories_dir = Path.cwd() / 'repositories'
    
    # Try to load repo
    try:
        from gitmap_core.repository import Repository, find_repository
        if args.repo:
            config.repo_path = Path(args.repo).resolve()
            config.repo = Repository(config.repo_path)
        else:
            # Default: look for repositories in repositories_dir and use the first one found
            if config.repositories_dir and config.repositories_dir.exists():
                repos_found = scan_repositories(config.repositories_dir)
                if repos_found:
                    # Use the first repository found as default
                    first_repo_path = Path(repos_found[0]['path'])
                    config.repo = Repository(first_repo_path)
                    config.repo_path = first_repo_path
                    print(f"Defaulting to first repository found: {repos_found[0]['name']}")
                else:
                    # No repositories found in repositories_dir
                    config.repo_path = None
                    config.repo = None
                    print(f"Note: No GitMap repositories found in {config.repositories_dir}.")
                    print("      You can initialize a repository with 'gitmap init' or clone one with 'gitmap clone'.")
            else:
                # Fallback: try to find repository in current directory or parents
                repo = find_repository()
                if repo:
                    config.repo_path = repo.root
                    config.repo = repo
                else:
                    config.repo_path = None
                    config.repo = None
                    print("Note: No GitMap repository found.")
    except Exception as e:
        print(f"Note: Could not load repository: {e}")
        print("GUI will start but some features may be limited.")
        config.repo_path = None
        config.repo = None
    
    print(f"\n🗺️  GitMap GUI")
    print(f"   Repository: {config.repo_path}")
    print(f"   Repositories Directory: {config.repositories_dir}")
    print(f"   URL: http://localhost:{args.port}")
    print(f"\n   Press Ctrl+C to stop\n")
    
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
