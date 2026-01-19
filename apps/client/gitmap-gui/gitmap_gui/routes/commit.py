"""Commit route handlers."""
from flask import Blueprint, jsonify, request

from ..utils import get_repo

bp = Blueprint('commit', __name__, url_prefix='/api')


@bp.route('/commits')
def api_commits():
    """Get commit history - uses same method as CLI."""
    r = get_repo()
    from ..config import repo_path
    
    if not r:
        return jsonify({'commits': [], 'error': f'No repository loaded. repo_path={repo_path}'})
    
    try:
        # Debug: Check repository state first
        current_branch = r.get_current_branch()
        head_commit = r.get_head_commit()
        all_branches = r.list_branches()
        
        print(f"DEBUG api_commits: repo_path={repo_path}, repo.root={r.root}")
        print(f"DEBUG api_commits: current_branch={current_branch}, head_commit={head_commit}")
        print(f"DEBUG api_commits: all_branches={all_branches}")
        
        # Use EXACT same method as CLI: get_commit_history()
        # This starts from HEAD (current branch) and walks back through parent commits
        commits = r.get_commit_history(limit=50)
        
        print(f"DEBUG api_commits: get_commit_history returned {len(commits)} commits")
        
        # Build commit list exactly like CLI would display
        commit_list = []
        for c in commits:
            commit_list.append({
                'id': c.id,
                'message': c.message,
                'author': c.author,
                'timestamp': c.timestamp,
                'branches': [current_branch] if current_branch else [],  # Current branch
            })
        
        # Also collect from all branches for completeness
        all_branches = r.list_branches()
        commit_to_branches = {c.id: [current_branch] if current_branch else [] for c in commits}
        
        # Add commits from other branches
        for branch_name in all_branches:
            if branch_name == current_branch:
                continue  # Already have commits from current branch
            
            commit_id = r.get_branch_commit(branch_name)
            if not commit_id:
                continue
            
            # Traverse this branch's commits
            visited = set()
            current_commit_id = commit_id
            depth = 0
            
            while current_commit_id and depth < 50:
                if current_commit_id in visited:
                    break
                visited.add(current_commit_id)
                
                commit = r.get_commit(current_commit_id)
                if not commit:
                    break
                
                # Add to our list if not already there
                if commit.id not in [c['id'] for c in commit_list]:
                    commit_list.append({
                        'id': commit.id,
                        'message': commit.message,
                        'author': commit.author,
                        'timestamp': commit.timestamp,
                        'branches': [branch_name],
                    })
                    commit_to_branches[commit.id] = [branch_name]
                elif commit.id in commit_to_branches:
                    # Update branches list
                    if branch_name not in commit_to_branches[commit.id]:
                        commit_to_branches[commit.id].append(branch_name)
                        # Update in commit_list
                        for c in commit_list:
                            if c['id'] == commit.id:
                                c['branches'] = commit_to_branches[commit.id]
                                break
                
                current_commit_id = commit.parent
                depth += 1
        
        # Sort by timestamp (newest first)
        commit_list.sort(key=lambda c: c['timestamp'], reverse=True)
        
        return jsonify({
            'commits': commit_list[:50],
            'debug': {
                'current_branch': current_branch,
                'head_commit': head_commit,
                'total_commits': len(commits),
                'all_commits_count': len(commit_list),
                'repo_path': str(r.root),
            }
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in api_commits: {e}")
        print(error_trace)
        return jsonify({
            'commits': [], 
            'error': str(e),
            'debug': {
                'repo_path': str(r.root) if r else None,
                'repo_exists': r.exists() if r else False,
                'repo_valid': r.is_valid() if r else False,
            }
        })


@bp.route('/commit', methods=['POST'])
def api_commit():
    """Create a new commit."""
    r = get_repo()
    if not r:
        return jsonify({'success': False, 'error': 'No repository'})
    
    data = request.get_json()
    message = data.get('message') if data else None
    author = data.get('author') if data else None
    
    if not message:
        return jsonify({'success': False, 'error': 'Commit message is required'})
    
    try:
        commit = r.create_commit(message, author=author)
        return jsonify({
            'success': True,
            'commit': {
                'id': commit.id,
                'message': commit.message,
                'author': commit.author,
                'timestamp': commit.timestamp.isoformat() if hasattr(commit.timestamp, 'isoformat') else str(commit.timestamp),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
