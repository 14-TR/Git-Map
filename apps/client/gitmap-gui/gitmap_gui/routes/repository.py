"""Repository route handlers."""
from flask import Blueprint, jsonify, request

from ..config import repo_path
from ..utils import get_repo, scan_repositories

bp = Blueprint('repository', __name__, url_prefix='/api')


@bp.route('/status')
def api_status():
    """Get repository status."""
    r = get_repo()
    if not r:
        return jsonify({'error': 'No repository loaded', 'path': str(repo_path) if repo_path else None})
    
    try:
        current_branch = r.get_current_branch()
        head_commit = r.get_head_commit()
        config = r.get_config()
        
        # Check for changes by comparing index with head
        has_changes = False
        try:
            index_data = r.get_index()
            # If there's a HEAD commit, compare index with it
            if head_commit:
                head_data = r.get_commit(head_commit).map_data
                has_changes = index_data != head_data
            else:
                # No HEAD commit - check if index has any data (uncommitted initial state)
                # If index exists and has data, there are changes
                has_changes = bool(index_data) and len(index_data.get('operationalLayers', [])) > 0
        except Exception as e:
            # If we can't get index, assume no changes
            print(f"Error checking for changes: {e}")
            pass
        
        return jsonify({
            'path': str(r.root),
            'current_branch': current_branch or 'main',
            'head': head_commit,
            'has_changes': has_changes,
            'remote': {
                'name': config.remote.name,
                'url': config.remote.url,
                'item_id': getattr(config.remote, 'item_id', None),
                'folder_id': getattr(config.remote, 'folder_id', None),
            } if config and config.remote else None,
        })
    except Exception as e:
        return jsonify({'error': str(e), 'path': str(r.root) if r else None})


@bp.route('/repositories')
def api_repositories():
    """List all repositories in the repositories directory."""
    import gitmap_gui.config as config_module
    
    if not config_module.repositories_dir:
        return jsonify({
            'repositories': [],
            'directory': None,
            'error': 'Repositories directory not configured'
        })
    
    try:
        repos = scan_repositories(config_module.repositories_dir)
        return jsonify({
            'repositories': repos,
            'directory': str(config_module.repositories_dir)
        })
    except Exception as e:
        return jsonify({
            'repositories': [],
            'directory': str(config_module.repositories_dir) if config_module.repositories_dir else None,
            'error': str(e)
        })


@bp.route('/repo/switch', methods=['POST'])
def api_switch_repo():
    """Switch to a different repository."""
    from pathlib import Path
    import gitmap_gui.config as config_module
    
    data = request.get_json()
    path = data.get('path') if data else None
    
    if not path:
        return jsonify({'success': False, 'error': 'Path is required'})
    
    try:
        from gitmap_core.repository import Repository
        
        new_repo = Repository(Path(path))
        if not new_repo.exists() or not new_repo.is_valid():
            return jsonify({'success': False, 'error': 'Invalid GitMap repository'})
        
        config_module.repo = new_repo
        config_module.repo_path = Path(path)
        
        return jsonify({
            'success': True,
            'path': str(new_repo.root),
            'current_branch': new_repo.get_current_branch() or 'main'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/repo/reload', methods=['POST'])
def api_reload_repo():
    """Reload repository from disk (to pick up external changes)."""
    from pathlib import Path
    import gitmap_gui.config as config_module
    
    try:
        from gitmap_core.repository import Repository
        
        if not config_module.repo_path:
            return jsonify({'success': False, 'error': 'No repository loaded'})
        
        # Force reload by creating new Repository instance
        config_module.repo = Repository(Path(config_module.repo_path))
        
        return jsonify({
            'success': True,
            'path': str(config_module.repo.root),
            'current_branch': config_module.repo.get_current_branch() or 'main'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
