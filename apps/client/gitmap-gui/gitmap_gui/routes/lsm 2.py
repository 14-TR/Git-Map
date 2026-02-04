"""Layer Settings Merge (LSM) route handlers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

from ..utils import get_repo, scan_repositories
import gitmap_gui.config as config_module

bp = Blueprint('lsm', __name__, url_prefix='/api')


def _get_repo_by_path(repo_path: str):
    """Get a Repository instance for a given path."""
    from gitmap_core.repository import Repository
    try:
        repo = Repository(Path(repo_path))
        if repo.exists() and repo.is_valid():
            return repo
    except Exception:
        pass
    return None


@bp.route('/lsm/health')
def api_lsm_health():
    """Health check for LSM blueprint - verifies blueprint is loaded."""
    return jsonify({'status': 'ok', 'blueprint': 'lsm', 'routes': ['/api/lsm/health', '/api/lsm/sources', '/api/lsm/preview', '/api/lsm/execute']})


def _find_layer_by_name(
        layers: list[dict[str, Any]],
        layer_name: str,
) -> dict[str, Any] | None:
    """Find layer in list by exact name match."""
    for layer in layers:
        if layer.get("title") == layer_name or layer.get("id") == layer_name:
            return layer
    return None


def _transfer_layer_settings(
        source_layer: dict[str, Any],
        target_layer: dict[str, Any],
) -> dict[str, Any]:
    """Transfer popup and form settings from source to target layer."""
    updated_layer = target_layer.copy()

    # Transfer popupInfo if present in source
    if "popupInfo" in source_layer:
        updated_layer["popupInfo"] = json.loads(
            json.dumps(source_layer["popupInfo"]),
        )

    # Transfer formInfo if present in source
    if "formInfo" in source_layer:
        updated_layer["formInfo"] = json.loads(
            json.dumps(source_layer["formInfo"]),
        )

    # Handle nested layers (for GroupLayers)
    if "layers" in source_layer and "layers" in target_layer:
        source_nested = source_layer["layers"]
        target_nested = target_layer["layers"]
        updated_nested = []

        for target_nest_layer in target_nested:
            target_nest_name = target_nest_layer.get("title") or target_nest_layer.get("id", "Unknown")
            source_nest_layer = _find_layer_by_name(source_nested, target_nest_name)

            if source_nest_layer:
                updated_nest_layer = _transfer_layer_settings(source_nest_layer, target_nest_layer)
                updated_nested.append(updated_nest_layer)
            else:
                updated_nested.append(target_nest_layer)

        updated_layer["layers"] = updated_nested

    return updated_layer


def _transfer_settings_between_maps(
        source_map: dict[str, Any],
        target_map: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Transfer popup and form settings between maps."""
    source_layers = source_map.get("operationalLayers", [])
    source_tables = source_map.get("tables", [])

    target_layers = json.loads(json.dumps(target_map.get("operationalLayers", [])))
    target_tables = json.loads(json.dumps(target_map.get("tables", [])))

    transferred_layers: list[str] = []
    skipped_layers: list[str] = []

    for source_layer in source_layers:
        layer_name = source_layer.get("title") or source_layer.get("id", "Unknown")
        target_layer = _find_layer_by_name(target_layers, layer_name)

        if not target_layer:
            skipped_layers.append(layer_name)
            continue

        updated_layer = _transfer_layer_settings(source_layer, target_layer)
        for i, layer in enumerate(target_layers):
            if layer.get("title") == layer_name or layer.get("id") == layer_name:
                target_layers[i] = updated_layer
                break

        transferred_layers.append(layer_name)

    transferred_tables: list[str] = []
    skipped_tables: list[str] = []

    for source_table in source_tables:
        table_name = source_table.get("title") or source_table.get("id", "Unknown")
        target_table = _find_layer_by_name(target_tables, table_name)

        if not target_table:
            skipped_tables.append(table_name)
            continue

        updated_table = _transfer_layer_settings(source_table, target_table)
        for i, table in enumerate(target_tables):
            if table.get("title") == table_name or table.get("id") == table_name:
                target_tables[i] = updated_table
                break

        transferred_tables.append(table_name)

    updated_map = target_map.copy()
    updated_map["operationalLayers"] = target_layers
    updated_map["tables"] = target_tables

    summary = {
        "transferred_layers": transferred_layers,
        "skipped_layers": skipped_layers,
        "transferred_tables": transferred_tables,
        "skipped_tables": skipped_tables,
    }

    return updated_map, summary


@bp.route('/lsm/repositories')
def api_lsm_repositories():
    """Get all repositories with their branches for LSM selection."""
    if not config_module.repositories_dir:
        return jsonify({'success': False, 'error': 'Repositories directory not configured'}), 400

    try:
        repos_data = []
        repos = scan_repositories(config_module.repositories_dir)

        for repo_info in repos:
            repo = _get_repo_by_path(repo_info['path'])
            if not repo:
                continue

            branches = []
            for branch in repo.list_branches():
                commit_id = repo.get_branch_commit(branch)
                if commit_id:
                    commit = repo.get_commit(commit_id)
                    if commit:
                        branches.append({
                            'name': branch,
                            'commit_id': commit_id,
                            'message': commit.message,
                            'timestamp': commit.timestamp.isoformat() if hasattr(commit.timestamp, 'isoformat') else commit.timestamp,
                        })

            repos_data.append({
                'path': repo_info['path'],
                'name': repo_info['name'],
                'project_name': repo_info.get('project_name', repo_info['name']),
                'current_branch': repo_info.get('current_branch', 'main'),
                'branches': branches,
            })

        # Get current repo info
        current_repo = get_repo()
        current_repo_path = str(current_repo.root) if current_repo else None

        return jsonify({
            'success': True,
            'repositories': repos_data,
            'current_repo_path': current_repo_path,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/lsm/sources')
def api_lsm_sources():
    """Get available LSM sources (branches and commits)."""
    repo = get_repo()
    if not repo:
        return jsonify({'success': False, 'error': 'No repository loaded'}), 400

    try:
        sources = []

        # Add branches as sources
        branches = repo.list_branches()
        for branch in branches:
            commit_id = repo.get_branch_commit(branch)
            if commit_id:
                commit = repo.get_commit(commit_id)
                if commit:
                    sources.append({
                        'type': 'branch',
                        'name': branch,
                        'commit_id': commit_id,
                        'message': commit.message,
                        'timestamp': commit.timestamp.isoformat() if hasattr(commit.timestamp, 'isoformat') else commit.timestamp,
                    })

        return jsonify({
            'success': True,
            'sources': sources,
            'current_branch': repo.get_current_branch(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/lsm/preview', methods=['POST'])
def api_lsm_preview():
    """Preview layer settings merge without applying."""
    try:
        data = request.get_json() or {}

        # Support both old (single repo) and new (cross-repo) API
        source_repo_path = data.get('source_repo_path')
        source_branch = data.get('source_branch')
        target_repo_path = data.get('target_repo_path')
        target_branch = data.get('target_branch')

        if not source_branch:
            return jsonify({'success': False, 'error': 'Source branch is required'}), 400

        # Get source repository
        if source_repo_path:
            source_repo = _get_repo_by_path(source_repo_path)
            if not source_repo:
                return jsonify({'success': False, 'error': f"Source repository not found: {source_repo_path}"}), 400
        else:
            source_repo = get_repo()
            if not source_repo:
                return jsonify({'success': False, 'error': 'No repository loaded'}), 400

        # Get target repository
        if target_repo_path:
            target_repo = _get_repo_by_path(target_repo_path)
            if not target_repo:
                return jsonify({'success': False, 'error': f"Target repository not found: {target_repo_path}"}), 400
        else:
            target_repo = get_repo()
            if not target_repo:
                return jsonify({'success': False, 'error': 'No repository loaded'}), 400

        # Get source map from branch
        source_commit_id = source_repo.get_branch_commit(source_branch)
        if not source_commit_id:
            return jsonify({'success': False, 'error': f"Branch '{source_branch}' has no commits"}), 400

        source_commit = source_repo.get_commit(source_commit_id)
        if not source_commit:
            return jsonify({'success': False, 'error': f"Commit '{source_commit_id}' not found"}), 400

        source_map = source_commit.map_data

        # Get target map - either from specified branch or current index
        if target_branch:
            target_commit_id = target_repo.get_branch_commit(target_branch)
            if not target_commit_id:
                return jsonify({'success': False, 'error': f"Target branch '{target_branch}' has no commits"}), 400
            target_commit = target_repo.get_commit(target_commit_id)
            if not target_commit:
                return jsonify({'success': False, 'error': f"Target commit '{target_commit_id}' not found"}), 400
            target_map = target_commit.map_data
        else:
            target_map = target_repo.get_index()
            if not target_map:
                return jsonify({'success': False, 'error': 'No map data in target index'}), 400

        # Preview transfer
        _, summary = _transfer_settings_between_maps(source_map, target_map)

        return jsonify({
            'success': True,
            'summary': {
                'transferred_layers': summary['transferred_layers'],
                'skipped_layers': summary['skipped_layers'],
                'transferred_tables': summary['transferred_tables'],
                'skipped_tables': summary['skipped_tables'],
                'total_transferred': len(summary['transferred_layers']) + len(summary['transferred_tables']),
                'total_skipped': len(summary['skipped_layers']) + len(summary['skipped_tables']),
            },
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/lsm/execute', methods=['POST'])
def api_lsm_execute():
    """Execute layer settings merge."""
    try:
        data = request.get_json() or {}

        # Support both old (single repo) and new (cross-repo) API
        source_repo_path = data.get('source_repo_path')
        source_branch = data.get('source_branch')
        target_repo_path = data.get('target_repo_path')
        target_branch = data.get('target_branch')

        if not source_branch:
            return jsonify({'success': False, 'error': 'Source branch is required'}), 400

        # Get source repository
        if source_repo_path:
            source_repo = _get_repo_by_path(source_repo_path)
            if not source_repo:
                return jsonify({'success': False, 'error': f"Source repository not found: {source_repo_path}"}), 400
        else:
            source_repo = get_repo()
            if not source_repo:
                return jsonify({'success': False, 'error': 'No repository loaded'}), 400

        # Get target repository
        if target_repo_path:
            target_repo = _get_repo_by_path(target_repo_path)
            if not target_repo:
                return jsonify({'success': False, 'error': f"Target repository not found: {target_repo_path}"}), 400
        else:
            target_repo = get_repo()
            if not target_repo:
                return jsonify({'success': False, 'error': 'No repository loaded'}), 400

        # Get source map from branch
        source_commit_id = source_repo.get_branch_commit(source_branch)
        if not source_commit_id:
            return jsonify({'success': False, 'error': f"Branch '{source_branch}' has no commits"}), 400

        source_commit = source_repo.get_commit(source_commit_id)
        if not source_commit:
            return jsonify({'success': False, 'error': f"Commit '{source_commit_id}' not found"}), 400

        source_map = source_commit.map_data

        # Get target map - either from specified branch or current index
        if target_branch:
            target_commit_id = target_repo.get_branch_commit(target_branch)
            if not target_commit_id:
                return jsonify({'success': False, 'error': f"Target branch '{target_branch}' has no commits"}), 400
            target_commit = target_repo.get_commit(target_commit_id)
            if not target_commit:
                return jsonify({'success': False, 'error': f"Target commit '{target_commit_id}' not found"}), 400
            target_map = target_commit.map_data
        else:
            target_map = target_repo.get_index()
            if not target_map:
                return jsonify({'success': False, 'error': 'No map data in target index'}), 400

        # Execute transfer
        updated_map, summary = _transfer_settings_between_maps(source_map, target_map)

        # Update target repository's index with transferred settings
        target_repo.update_index(updated_map)

        return jsonify({
            'success': True,
            'summary': {
                'transferred_layers': summary['transferred_layers'],
                'skipped_layers': summary['skipped_layers'],
                'transferred_tables': summary['transferred_tables'],
                'skipped_tables': summary['skipped_tables'],
                'total_transferred': len(summary['transferred_layers']) + len(summary['transferred_tables']),
                'total_skipped': len(summary['skipped_layers']) + len(summary['skipped_tables']),
            },
            'message': 'Settings transferred to target index. Use commit to save changes.',
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
