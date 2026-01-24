"""Configuration route handlers."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..utils import get_repo

bp = Blueprint('config', __name__, url_prefix='/api')


@bp.route('/config')
def api_get_config():
    """Get repository configuration."""
    repo = get_repo()
    if not repo:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    try:
        config = repo.get_config()
        return jsonify({
            'success': True,
            'config': {
                'project_name': config.get('project_name', ''),
                'user_name': config.get('user_name', ''),
                'user_email': config.get('user_email', ''),
                'production_branch': config.get('production_branch', ''),
                'auto_visualize': config.get('auto_visualize', False),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/config', methods=['POST'])
def api_update_config():
    """Update repository configuration."""
    repo = get_repo()
    if not repo:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    try:
        data = request.get_json() or {}

        # Get current config and update
        config = repo.get_config()

        # Update only provided fields
        if 'project_name' in data:
            config['project_name'] = data['project_name']
        if 'user_name' in data:
            config['user_name'] = data['user_name']
        if 'user_email' in data:
            config['user_email'] = data['user_email']
        if 'production_branch' in data:
            config['production_branch'] = data['production_branch']
        if 'auto_visualize' in data:
            config['auto_visualize'] = data['auto_visualize']

        # Save config
        repo.save_config(config)

        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
