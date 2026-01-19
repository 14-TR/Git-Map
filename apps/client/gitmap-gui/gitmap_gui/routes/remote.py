"""Remote operations route handlers (clone, pull, push)."""
from pathlib import Path

from flask import Blueprint, jsonify, request

from ..config import portal_connection, portal_gis, repositories_dir
from ..utils import get_repo

bp = Blueprint('remote', __name__, url_prefix='/api')


@bp.route('/clone', methods=['POST'])
def api_clone():
    """Clone a webmap from Portal."""
    from ..config import portal_gis, portal_connection, repositories_dir as config_repos_dir
    import gitmap_gui.config as config_module
    
    if not portal_gis:
        return jsonify({'success': False, 'error': 'Not connected to Portal. Connect first.'}), 400

    data = request.get_json() or {}
    item_id = data.get('item_id')
    directory = data.get('directory')

    if not item_id:
        return jsonify({'success': False, 'error': 'Item ID required'}), 400

    try:
        from gitmap_core.repository import Repository
        from gitmap_core.maps import get_webmap_by_id
        from gitmap_core.models import Remote

        # Fetch webmap from Portal
        item, map_data = get_webmap_by_id(portal_gis, item_id)

        # Determine target directory
        if not directory:
            # Sanitize title for directory name
            directory = item.title.replace(' ', '_').replace('/', '_')

        target_path = Path(config_repos_dir) / directory if config_repos_dir else Path(directory)

        if target_path.exists():
            return jsonify({'success': False, 'error': f'Directory already exists: {target_path}'}), 400

        # Create and initialize repository
        target_path.mkdir(parents=True, exist_ok=True)
        new_repo = Repository(target_path)
        new_repo.init(project_name=item.title, user_name=portal_gis.users.me.username if portal_gis.users.me else '')

        # Configure remote
        config = new_repo.get_config()
        config.remote = Remote(
            name='origin',
            url=config_module.portal_connection.url if config_module.portal_connection else 'https://www.arcgis.com',
            item_id=item_id,
        )
        new_repo.update_config(config)

        # Stage map data and create initial commit
        new_repo.update_index(map_data)
        commit = new_repo.create_commit(message=f"Clone from Portal: {item.title}")

        # Switch to new repository
        config_module.repo = new_repo
        config_module.repo_path = target_path

        # Count layers
        layers = map_data.get('operationalLayers', [])

        return jsonify({
            'success': True,
            'path': str(target_path),
            'title': item.title,
            'layers': len(layers),
            'commit_id': commit.id,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/pull', methods=['POST'])
def api_pull():
    """Pull changes from Portal."""
    from ..config import portal_gis, portal_connection as config_portal_connection
    
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    if not portal_gis:
        return jsonify({'success': False, 'error': 'Not connected to Portal'}), 400

    data = request.get_json() or {}
    branch = data.get('branch')

    try:
        from gitmap_core.remote import RemoteOperations

        remote_ops = RemoteOperations(r, config_portal_connection)
        map_data = remote_ops.pull(branch)

        # Update index with pulled data
        r.update_index(map_data)

        layers = map_data.get('operationalLayers', [])

        return jsonify({
            'success': True,
            'layers': len(layers),
            'has_changes': r.has_uncommitted_changes(),
            'message': 'Changes pulled. Review with diff and commit when ready.',
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/push', methods=['POST'])
def api_push():
    """Push changes to Portal."""
    from ..config import portal_gis, portal_connection as config_portal_connection
    
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    if not portal_gis:
        return jsonify({'success': False, 'error': 'Not connected to Portal'}), 400

    data = request.get_json() or {}
    branch = data.get('branch')
    skip_notifications = data.get('skip_notifications', False)

    try:
        from gitmap_core.remote import RemoteOperations

        remote_ops = RemoteOperations(r, config_portal_connection)
        item, notification_status = remote_ops.push(branch, skip_notifications=skip_notifications)

        return jsonify({
            'success': True,
            'item_id': item.id,
            'title': item.title,
            'url': item.homepage,
            'notifications': notification_status,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400
