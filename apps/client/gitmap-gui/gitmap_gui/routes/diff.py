"""Diff route handlers."""
from flask import Blueprint, jsonify

from ..utils import get_repo

bp = Blueprint('diff', __name__, url_prefix='/api')


@bp.route('/diff')
def api_diff():
    """Get current diff."""
    r = get_repo()
    if not r:
        return jsonify({'diff': None, 'error': 'No repository'})
    
    try:
        from gitmap_core.diff import diff_maps
        index_data = r.get_index()
        head_commit = r.get_head_commit()
        
        if head_commit:
            # Compare index with HEAD
            head_data = r.get_commit(head_commit).map_data
            if head_data and index_data and head_data != index_data:
                diff_result = diff_maps(head_data, index_data)
                # Serialize MapDiff dataclass to dict
                diff_dict = {
                    'layer_changes': [
                        {
                            'layer_id': c.layer_id,
                            'layer_title': getattr(c, 'layer_title', None) or c.layer_id,
                            'change_type': c.change_type,
                            'details': c.details if hasattr(c, 'details') else {}
                        }
                        for c in (diff_result.layer_changes or [])
                    ],
                    'table_changes': [
                        {
                            'layer_id': c.layer_id,
                            'layer_title': getattr(c, 'layer_title', None) or c.layer_id,
                            'change_type': c.change_type,
                            'details': c.details if hasattr(c, 'details') else {}
                        }
                        for c in (diff_result.table_changes or [])
                    ],
                    'property_changes': diff_result.property_changes or {},
                    'has_changes': diff_result.has_changes
                }
                return jsonify({'diff': diff_dict, 'has_changes': True})
        else:
            # No HEAD commit - if index has data, there are changes
            if index_data and len(index_data.get('operationalLayers', [])) > 0:
                # Create a diff showing all layers as added (since there's no previous state)
                # For now, just indicate there are changes
                return jsonify({
                    'diff': {
                        'layer_changes': [
                            {
                                'layer_id': 'new_map',
                                'layer_title': 'New map',
                                'change_type': 'added'
                            }
                        ]
                    },
                    'has_changes': True
                })
        
        return jsonify({'diff': None, 'has_changes': False})
    except Exception as e:
        return jsonify({'diff': None, 'error': str(e)})
