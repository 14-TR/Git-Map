"""Merge route handlers."""
from flask import Blueprint, jsonify, request

from ..config import merge_state
from ..utils import get_repo

bp = Blueprint('merge', __name__, url_prefix='/api')


@bp.route('/merge/preview', methods=['POST'])
def api_merge_preview():
    """Preview a merge and detect conflicts."""
    from ..config import merge_state as config_merge_state
    import gitmap_gui.config as config_module
    
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    data = request.get_json()
    source_branch = data.get('branch') if data else None

    if not source_branch:
        return jsonify({'success': False, 'error': 'Source branch required'}), 400

    try:
        from gitmap_core.merge import merge_maps

        current_branch = r.get_current_branch()
        if not current_branch:
            return jsonify({'success': False, 'error': 'Cannot merge in detached HEAD state'}), 400

        if source_branch == current_branch:
            return jsonify({'success': False, 'error': 'Cannot merge branch into itself'}), 400

        # Get map data from both branches
        current_commit_id = r.get_head_commit()
        source_commit_id = r.get_branch_commit(source_branch)

        if not source_commit_id:
            return jsonify({'success': False, 'error': f'Branch {source_branch} not found'}), 400

        current_commit = r.get_commit(current_commit_id) if current_commit_id else None
        source_commit = r.get_commit(source_commit_id)

        ours = current_commit.map_data if current_commit else {}
        theirs = source_commit.map_data if source_commit else {}

        # Perform merge preview
        result = merge_maps(ours, theirs)

        # Store merge state for later execution
        config_module.merge_state = {
            'source_branch': source_branch,
            'target_branch': current_branch,
            'result': result,
            'ours': ours,
            'theirs': theirs,
        }

        # Format conflicts for frontend
        conflicts = []
        if hasattr(result, 'conflicts') and result.conflicts:
            for c in result.conflicts:
                conflicts.append({
                    'layer_id': c.layer_id,
                    'layer_title': c.layer_title,
                    'type': 'layer',
                })

        return jsonify({
            'success': True,
            'has_conflicts': result.has_conflicts if hasattr(result, 'has_conflicts') else len(conflicts) > 0,
            'conflicts': conflicts,
            'summary': {
                'added_layers': len(result.added_layers) if hasattr(result, 'added_layers') else 0,
                'removed_layers': len(result.removed_layers) if hasattr(result, 'removed_layers') else 0,
                'modified_layers': len(result.modified_layers) if hasattr(result, 'modified_layers') else 0,
            },
            'source_branch': source_branch,
            'target_branch': current_branch,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/merge/execute', methods=['POST'])
def api_merge_execute():
    """Execute merge with conflict resolutions."""
    from ..config import merge_state as config_merge_state
    import gitmap_gui.config as config_module
    
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    if not config_module.merge_state:
        return jsonify({'success': False, 'error': 'No merge in progress. Call /api/merge/preview first'}), 400

    data = request.get_json() or {}
    resolutions = data.get('resolutions', {})
    auto_commit = data.get('auto_commit', True)

    try:
        from gitmap_core.merge import resolve_conflict, apply_resolution

        result = config_module.merge_state['result']

        # Apply conflict resolutions
        if hasattr(result, 'conflicts') and result.conflicts:
            for conflict in result.conflicts:
                resolution = resolutions.get(conflict.layer_id, 'ours')
                resolved_layer = resolve_conflict(conflict, resolution)
                result = apply_resolution(result, conflict.layer_id, resolved_layer)

        # Update index with merged data
        r.update_index(result.merged_data)

        commit_id = None
        if auto_commit:
            source_branch = config_module.merge_state['source_branch']
            commit = r.create_commit(
                message=f"Merge branch '{source_branch}' into {config_module.merge_state['target_branch']}"
            )
            commit_id = commit.id

        # Clear merge state
        config_module.merge_state = None

        return jsonify({
            'success': True,
            'commit_id': commit_id,
            'message': 'Merge completed successfully',
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/merge/abort', methods=['POST'])
def api_merge_abort():
    """Abort the current merge."""
    import gitmap_gui.config as config_module
    config_module.merge_state = None
    return jsonify({'success': True, 'message': 'Merge aborted'})
