"""Services route handlers for browsing Portal services."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp = Blueprint('services', __name__, url_prefix='/api')


@bp.route('/portal/services')
def api_portal_services():
    """List available services from Portal.

    Query Parameters:
        query: Optional search query string.
        owner: Optional owner username filter.
        service_type: Optional service type filter (default: Feature Service).

    Returns:
        JSON response with list of services or error.
    """
    from ..config import portal_gis

    if not portal_gis:
        return jsonify({'success': False, 'error': 'Not connected to Portal'}), 400

    try:
        from gitmap_core.maps import list_services

        query = request.args.get('query', '')
        owner = request.args.get('owner', '')
        service_type = request.args.get('service_type', '')

        services = list_services(
            portal_gis,
            query=query,
            owner=owner,
            service_type=service_type,
        )
        return jsonify({
            'success': True,
            'services': services,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
