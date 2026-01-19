"""Branch route handlers."""
from flask import Blueprint, jsonify, request

from ..utils import get_repo

bp = Blueprint('branch', __name__, url_prefix='/api')


@bp.route('/branches')
def api_branches():
    """Get branch list."""
    r = get_repo()
    if not r:
        return jsonify({'branches': [], 'error': 'No repository'})
    
    try:
        branches = r.list_branches()
        branch_list = [{'name': b} for b in branches]
        return jsonify({'branches': branch_list})
    except Exception as e:
        return jsonify({'branches': [], 'error': str(e)})


@bp.route('/branch/create', methods=['POST'])
def api_branch_create():
    """Create a new branch."""
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository'})
    
    data = request.get_json()
    name = data.get('name') if data else None
    
    if not name:
        return jsonify({'success': False, 'error': 'Branch name is required'})
    
    try:
        r.create_branch(name)
        return jsonify({'success': True, 'branch': name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/branch/checkout', methods=['POST'])
def api_branch_checkout():
    """Checkout a branch."""
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository'})
    
    data = request.get_json()
    name = data.get('name') if data else None
    
    if not name:
        return jsonify({'success': False, 'error': 'Branch name is required'})
    
    try:
        r.checkout_branch(name)
        return jsonify({'success': True, 'branch': name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/branch/<name>', methods=['DELETE'])
def api_branch_delete(name):
    """Delete a branch."""
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository'})
    
    try:
        r.delete_branch(name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
