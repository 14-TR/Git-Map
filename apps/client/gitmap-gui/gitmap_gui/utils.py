"""Utility functions for GitMap GUI."""
from pathlib import Path
from typing import Optional

import gitmap_gui.config as config


def get_repo():
    """Get or initialize the repository."""
    if config.repo is None and config.repo_path:
        try:
            from gitmap_core.repository import Repository
            config.repo = Repository(Path(config.repo_path))
        except Exception:
            pass
    return config.repo


def scan_repositories(directory: Path) -> list[dict]:
    """Scan directory for GitMap repositories.
    
    Args:
        directory: Directory to scan (typically /app/repositories).
    
    Returns:
        List of repository info dictionaries.
    """
    repos = []
    if not directory.exists():
        print(f"scan_repositories: Directory does not exist: {directory}")
        return repos
    
    try:
        from gitmap_core.repository import Repository
        
        count = 0
        for item in directory.iterdir():
            if item.is_dir():
                count += 1
                try:
                    r = Repository(item)
                    if r.exists() and r.is_valid():
                        config = r.get_config()
                        current_branch = r.get_current_branch()
                        head_commit = r.get_head_commit()
                        
                        # Handle remote serialization (Remote might not have model_dump)
                        remote_dict = None
                        if config and config.remote:
                            remote = config.remote
                            if hasattr(remote, 'model_dump'):
                                remote_dict = remote.model_dump()
                            elif hasattr(remote, 'dict'):
                                remote_dict = remote.dict()
                            else:
                                # Fallback: convert to dict manually
                                remote_dict = {
                                    'name': getattr(remote, 'name', None),
                                    'url': getattr(remote, 'url', None),
                                    'item_id': getattr(remote, 'item_id', None),
                                    'folder_id': getattr(remote, 'folder_id', None),
                                }
                        
                        repos.append({
                            'path': str(item),
                            'name': item.name,
                            'project_name': config.project_name if config else item.name,
                            'current_branch': current_branch or 'main',
                            'head_commit': head_commit,
                            'remote': remote_dict,
                        })
                except Exception as e:
                    # Not a valid GitMap repository, skip
                    # Print only if it's not the expected "not a repo" error
                    if 'not a GitMap repository' not in str(e).lower():
                        print(f"scan_repositories: Error checking {item.name}: {e}")
                    continue
        
        print(f"scan_repositories: Scanned {count} directories, found {len(repos)} valid repositories")
    except Exception as e:
        import traceback
        print(f"Error scanning repositories: {e}")
        traceback.print_exc()
    
    return repos
