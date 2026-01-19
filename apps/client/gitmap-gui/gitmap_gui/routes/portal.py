"""Portal route handlers."""
import os

from flask import Blueprint, jsonify, request

from ..config import portal_connection, portal_gis

bp = Blueprint('portal', __name__, url_prefix='/api')


@bp.route('/portal/connect', methods=['POST'])
def api_portal_connect():
    """Connect to ArcGIS Portal."""
    import gitmap_gui.config as config_module
    
    data = request.get_json() or {}
    url = data.get('url') or os.environ.get('PORTAL_URL', 'https://www.arcgis.com')
    username = data.get('username') or os.environ.get('PORTAL_USER') or os.environ.get('ARCGIS_USERNAME')
    password = data.get('password') or os.environ.get('PORTAL_PASSWORD') or os.environ.get('ARCGIS_PASSWORD')

    try:
        from gitmap_core.connection import get_connection

        config_module.portal_connection = get_connection(url, username, password)
        config_module.portal_gis = config_module.portal_connection.connect(password)

        return jsonify({
            'success': True,
            'url': url,
            'username': config_module.portal_gis.users.me.username if config_module.portal_gis.users.me else username,
        })
    except Exception as e:
        config_module.portal_connection = None
        config_module.portal_gis = None
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/portal/status')
def api_portal_status():
    """Get portal connection status."""
    from ..config import portal_connection, portal_gis
    
    if portal_gis:
        try:
            user = portal_gis.users.me
            return jsonify({
                'connected': True,
                'url': portal_connection.url if portal_connection else None,
                'username': user.username if user else None,
            })
        except Exception:
            pass

    return jsonify({
        'connected': False,
        'url': None,
        'username': None,
    })


@bp.route('/portal/webmaps')
def api_portal_webmaps():
    """List available webmaps from Portal."""
    from ..config import portal_gis
    
    if not portal_gis:
        return jsonify({'success': False, 'error': 'Not connected to Portal'}), 400

    try:
        from gitmap_core.maps import list_webmaps

        query = request.args.get('query', '')
        owner = request.args.get('owner', '')

        webmaps = list_webmaps(portal_gis, query=query, owner=owner)
        return jsonify({
            'success': True,
            'webmaps': webmaps,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
