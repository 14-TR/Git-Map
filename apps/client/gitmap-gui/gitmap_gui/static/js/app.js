let repoData = null;
let currentPage = 'overview';
let portalStatus = { connected: false };
let mergeConflicts = [];
let mergeResolutions = {};

// ============================================================================
// Toast Notifications
// ============================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="status-dot"></span>
        <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// ============================================================================
// Modal Functions
// ============================================================================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ============================================================================
// API Helper for POST requests
// ============================================================================

async function postAPI(endpoint, data = {}) {
    try {
        const response = await fetch(`/api${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

async function deleteAPI(endpoint) {
    try {
        const response = await fetch(`/api${endpoint}`, { method: 'DELETE' });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// ============================================================================
// Branch Operations
// ============================================================================

async function createBranch() {
    const name = document.getElementById('new-branch-name').value.trim();
    if (!name) {
        showToast('Branch name is required', 'error');
        return;
    }

    const result = await postAPI('/branch/create', { name });
    if (result.success) {
        showToast(`Branch '${name}' created`, 'success');
        closeModal('create-branch-modal');
        document.getElementById('new-branch-name').value = '';
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Failed to create branch', 'error');
    }
}

async function checkoutBranch(name) {
    const result = await postAPI('/branch/checkout', { name });
    if (result.success) {
        showToast(`Switched to branch '${name}'`, 'success');
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Failed to switch branch', 'error');
    }
}

async function deleteBranch(name) {
    if (!confirm(`Delete branch '${name}'?`)) return;

    const result = await deleteAPI(`/branch/${encodeURIComponent(name)}`);
    if (result.success) {
        showToast(`Branch '${name}' deleted`, 'success');
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Failed to delete branch', 'error');
    }
}

// ============================================================================
// Commit Operations
// ============================================================================

function openCommitModal() {
    openModal('commit-modal');
}

async function createCommit() {
    const message = document.getElementById('commit-message').value.trim();
    const author = document.getElementById('commit-author').value.trim();

    if (!message) {
        showToast('Commit message is required', 'error');
        return;
    }

    const result = await postAPI('/commit', { message, author: author || undefined });
    if (result.success) {
        showToast(`Commit ${result.commit.id.substring(0, 8)} created`, 'success');
        closeModal('commit-modal');
        document.getElementById('commit-message').value = '';
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Failed to create commit', 'error');
    }
}

// ============================================================================
// Merge Operations
// ============================================================================

async function openMergeModal(branchName) {
    mergeConflicts = [];
    mergeResolutions = {};

    const modalBody = document.getElementById('merge-modal-body');
    modalBody.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    openModal('merge-modal');

    const result = await postAPI('/merge/preview', { branch: branchName });

    if (!result.success) {
        modalBody.innerHTML = `<div class="error-state">${escapeHtml(result.error)}</div>`;
        return;
    }

    if (result.has_conflicts && result.conflicts.length > 0) {
        mergeConflicts = result.conflicts;
        // Initialize resolutions to 'ours' by default
        result.conflicts.forEach(c => {
            mergeResolutions[c.layer_id] = 'ours';
        });

        modalBody.innerHTML = `
            <p style="margin-bottom: 1rem; color: var(--warning);">
                Conflicts detected. Choose how to resolve each conflict:
            </p>
            ${result.conflicts.map(c => `
                <div class="conflict-item">
                    <div class="conflict-header">
                        <span class="conflict-title">${escapeHtml(c.layer_title || c.layer_id)}</span>
                    </div>
                    <div class="conflict-choices">
                        <label class="conflict-choice selected" data-layer="${c.layer_id}" data-choice="ours" onclick="selectResolution('${c.layer_id}', 'ours', this)">
                            <input type="radio" name="conflict-${c.layer_id}" checked>
                            Keep Ours
                        </label>
                        <label class="conflict-choice" data-layer="${c.layer_id}" data-choice="theirs" onclick="selectResolution('${c.layer_id}', 'theirs', this)">
                            <input type="radio" name="conflict-${c.layer_id}">
                            Use Theirs
                        </label>
                    </div>
                </div>
            `).join('')}
        `;
    } else {
        modalBody.innerHTML = `
            <p>Merge <strong>${escapeHtml(result.source_branch)}</strong> into <strong>${escapeHtml(result.target_branch)}</strong></p>
            <div style="margin-top: 1rem; padding: 1rem; background: var(--bg-panel); border-radius: 8px;">
                <div style="color: var(--success);">+ ${result.summary.added_layers} layers added</div>
                <div style="color: var(--error);">- ${result.summary.removed_layers} layers removed</div>
                <div style="color: var(--warning);">~ ${result.summary.modified_layers} layers modified</div>
            </div>
            <p style="margin-top: 1rem; color: var(--success);">No conflicts detected. Ready to merge.</p>
        `;
    }
}

function selectResolution(layerId, choice, element) {
    mergeResolutions[layerId] = choice;
    // Update UI
    const parent = element.parentElement;
    parent.querySelectorAll('.conflict-choice').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
}

async function executeMerge() {
    const result = await postAPI('/merge/execute', {
        resolutions: mergeResolutions,
        auto_commit: true
    });

    if (result.success) {
        showToast('Merge completed successfully', 'success');
        closeModal('merge-modal');
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Merge failed', 'error');
    }
}

// ============================================================================
// Portal Operations
// ============================================================================

async function checkPortalStatus() {
    portalStatus = await fetchAPI('/portal/status');
    return portalStatus;
}

function openPortalModal() {
    openModal('portal-modal');
}

async function connectPortal() {
    const url = document.getElementById('portal-url').value.trim();
    const username = document.getElementById('portal-username').value.trim();
    const password = document.getElementById('portal-password').value;

    const result = await postAPI('/portal/connect', { url, username, password });
    if (result.success) {
        showToast(`Connected as ${result.username}`, 'success');
        closeModal('portal-modal');
        portalStatus = { connected: true, url: result.url, username: result.username };
        renderPage();
    } else {
        showToast(result.error || 'Connection failed', 'error');
    }
}

// ============================================================================
// Clone Operations
// ============================================================================

function openCloneModal() {
    if (!portalStatus.connected) {
        showToast('Connect to Portal first', 'warning');
        openPortalModal();
        return;
    }
    openModal('clone-modal');
}

async function cloneMap() {
    const itemId = document.getElementById('clone-item-id').value.trim();
    const directory = document.getElementById('clone-directory').value.trim();

    if (!itemId) {
        showToast('Item ID is required', 'error');
        return;
    }

    showToast('Cloning map...', 'info');
    const result = await postAPI('/clone', { item_id: itemId, directory: directory || undefined });

    if (result.success) {
        showToast(`Cloned '${result.title}' (${result.layers} layers)`, 'success');
        closeModal('clone-modal');
        document.getElementById('clone-item-id').value = '';
        document.getElementById('clone-directory').value = '';
        await loadRepoData();
        showPage('overview');
    } else {
        showToast(result.error || 'Clone failed', 'error');
    }
}

// ============================================================================
// Pull/Push Operations
// ============================================================================

async function pullFromPortal() {
    if (!portalStatus.connected) {
        showToast('Connect to Portal first', 'warning');
        openPortalModal();
        return;
    }

    showToast('Pulling from Portal...', 'info');
    const result = await postAPI('/pull', {});

    if (result.success) {
        showToast(`Pulled ${result.layers} layers. ${result.has_changes ? 'Review changes and commit.' : 'No changes.'}`, 'success');
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Pull failed', 'error');
    }
}

async function pushToPortal() {
    if (!portalStatus.connected) {
        showToast('Connect to Portal first', 'warning');
        openPortalModal();
        return;
    }

    showToast('Pushing to Portal...', 'info');
    const result = await postAPI('/push', {});

    if (result.success) {
        showToast(`Pushed to Portal: ${result.title}`, 'success');
    } else {
        showToast(result.error || 'Push failed', 'error');
    }
}

// ============================================================================
// Original API Helper
// ============================================================================

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`/api${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: error.message };
    }
}

async function loadRepoData() {
    const [status, commits, branches] = await Promise.all([
        fetchAPI('/status'),
        fetchAPI('/commits'),
        fetchAPI('/branches')
    ]);
    
    repoData = { status, commits, branches };
    
    // Update repo path in header
    document.getElementById('repo-path').textContent = 
        status.path || 'No repository';
    
    return repoData;
}

function showPage(page) {
    currentPage = page;
    
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });
    
    renderPage();
}

function renderPage() {
    const content = document.getElementById('main-content');
    
    if (!repoData || repoData.status?.error) {
        content.innerHTML = `
            <div class="error-state">
                <h3>No Repository Found</h3>
                <p>${repoData?.status?.error || 'Unable to load repository data'}</p>
                <p style="margin-top: 1rem; color: var(--text-muted);">
                    Run <code>gitmap init</code> in a directory first, then start the GUI with <code>--repo /path/to/repo</code>
                </p>
            </div>
        `;
        return;
    }

    switch (currentPage) {
        case 'overview':
            renderOverview();
            break;
        case 'commits':
            renderCommits();
            break;
        case 'branches':
            renderBranches();
            break;
        case 'changes':
            renderChanges();
            break;
        case 'remote':
            renderRemote();
            break;
        case 'repositories':
            renderRepositories();
            break;
    }
}

function renderOverview() {
    const { status, commits, branches } = repoData;
    const content = document.getElementById('main-content');
    
    const recentCommits = (commits.commits || []).slice(0, 5);
    
    content.innerHTML = `
        <h1 class="page-title">Repository Overview</h1>
        <p class="page-subtitle">Version control for ArcGIS web maps</p>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="status-label">Current Branch</div>
                <div class="status-value branch">${status.current_branch || 'main'}</div>
            </div>
            <div class="status-card">
                <div class="status-label">Total Commits</div>
                <div class="status-value">${commits.commits?.length || 0}</div>
            </div>
            <div class="status-card">
                <div class="status-label">Branches</div>
                <div class="status-value">${branches.branches?.length || 0}</div>
            </div>
            <div class="status-card">
                <div class="status-label">Pending Changes</div>
                <div class="status-value">${status.has_changes ? 'Yes' : 'No'}</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="4"/>
                        <line x1="1.05" y1="12" x2="7" y2="12"/>
                        <line x1="17.01" y1="12" x2="22.96" y2="12"/>
                    </svg>
                    Recent Commits
                </h3>
                <button class="btn btn-secondary" onclick="showPage('commits')">View All</button>
            </div>
            ${recentCommits.length > 0 ? `
                <div class="commit-list">
                    ${recentCommits.map(commit => `
                        <div class="commit-item">
                            <div class="commit-graph">
                                <div class="commit-dot"></div>
                            </div>
                            <div class="commit-info">
                                <div class="commit-message">${escapeHtml(commit.message || 'No message')}</div>
                                <div class="commit-meta">
                                    <span>${commit.author || 'Unknown'}</span>
                                    <span>${formatDate(commit.timestamp)}</span>
                                </div>
                            </div>
                            <div class="commit-hash">${(commit.id || '').substring(0, 8)}</div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <div class="empty-title">No commits yet</div>
                    <p>Create your first commit with <code>gitmap commit -m "message"</code></p>
                </div>
            `}
        </div>

        ${status.remote ? `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="2" y1="12" x2="22" y2="12"/>
                            <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
                        </svg>
                        Remote
                    </h3>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; color: var(--text-secondary);">
                    <div style="margin-bottom: 0.5rem;"><strong>URL:</strong> ${status.remote.url || 'Not set'}</div>
                    <div><strong>Item ID:</strong> ${status.remote.item_id || 'Not set'}</div>
                </div>
            </div>
        ` : ''}
    `;
}

function renderCommits() {
    const { commits, status } = repoData;
    const content = document.getElementById('main-content');
    
    // Debug: Log what we received
    console.log('Commits data:', commits);
    console.log('Commits commits:', commits?.commits);
    console.log('Commits debug:', commits?.debug);
    console.log('Status:', status);
    
    // Check for errors
    if (commits?.error) {
        content.innerHTML = `
            <div class="error-state">
                <h3>Error Loading Commits</h3>
                <p>${commits.error}</p>
                <p style="margin-top: 1rem; color: var(--text-muted);">
                    Repository path: ${status?.path || 'Not set'}<br>
                    Try refreshing the page or switching to a different repository.
                </p>
                ${commits.debug ? `<pre style="background: var(--bg-card); padding: 1rem; margin-top: 1rem; border-radius: 8px; overflow: auto;">${JSON.stringify(commits.debug, null, 2)}</pre>` : ''}
            </div>
        `;
        return;
    }
    
    const commitList = commits?.commits || [];
    const debugInfo = commits?.debug || {};
    
    content.innerHTML = `
        <h1 class="page-title">Commit History</h1>
        <p class="page-subtitle">
            ${commitList.length} commits in repository
            ${status?.path ? `<br><span style="font-size: 0.8em; color: var(--text-muted);">Repository: ${status.path}</span>` : ''}
            ${debugInfo.current_branch ? `<br><span style="font-size: 0.8em; color: var(--text-muted);">Branch: ${debugInfo.current_branch}, HEAD: ${debugInfo.head_commit ? debugInfo.head_commit.substring(0, 8) : 'none'}</span>` : ''}
            ${debugInfo.total_commits !== undefined ? `<br><span style="font-size: 0.8em; color: var(--accent-primary);">Debug: total_commits=${debugInfo.total_commits}, all_commits=${debugInfo.all_commits_count || 0}</span>` : ''}
        </p>
        
        <div class="card">
            ${commitList.length > 0 ? `
                <div class="commit-list">
                    ${commitList.map((commit, i) => `
                        <div class="commit-item">
                            <div class="commit-graph">
                                <div class="commit-dot"></div>
                            </div>
                            <div class="commit-info">
                                <div class="commit-message">${escapeHtml(commit.message || 'No message')}</div>
                                <div class="commit-meta">
                                    <span>${commit.author || 'Unknown'}</span>
                                    <span>${formatDate(commit.timestamp)}</span>
                                    ${commit.branches && commit.branches.length > 0 ? 
                                        `<span style="color: var(--accent-primary);">Branches: ${commit.branches.join(', ')}</span>` 
                                        : ''}
                                </div>
                            </div>
                            <div class="commit-hash">${(commit.id || '').substring(0, 8)}</div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <div class="empty-title">No commits yet</div>
                    <p>Create your first commit with <code>gitmap commit -m "message"</code></p>
                    ${status?.path ? `<p style="margin-top: 0.5rem; color: var(--text-muted);">Repository: ${status.path}</p>` : ''}
                </div>
            `}
        </div>
    `;
}

function renderBranches() {
    const { branches, status } = repoData;
    const content = document.getElementById('main-content');
    const branchList = branches.branches || [];
    const currentBranch = status.current_branch || 'main';

    content.innerHTML = `
        <h1 class="page-title">Branches</h1>
        <p class="page-subtitle">${branchList.length} branches in repository</p>

        <div style="margin-bottom: 1.5rem;">
            <button class="btn btn-primary" onclick="openModal('create-branch-modal')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Create Branch
            </button>
        </div>

        <div class="card">
            ${branchList.length > 0 ? `
                <div class="branch-list">
                    ${branchList.map(branch => `
                        <div class="branch-item ${branch.name === currentBranch ? 'current' : ''}">
                            <div class="branch-name">
                                <svg class="branch-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="6" y1="3" x2="6" y2="15"/>
                                    <circle cx="18" cy="6" r="3"/>
                                    <circle cx="6" cy="18" r="3"/>
                                    <path d="M18 9a9 9 0 01-9 9"/>
                                </svg>
                                ${escapeHtml(branch.name)}
                            </div>
                            <div class="item-actions">
                                ${branch.name === currentBranch ?
                                    '<span class="branch-badge">Current</span>' :
                                    `<button class="btn btn-secondary btn-small" onclick="checkoutBranch('${escapeHtml(branch.name)}')">Checkout</button>
                                     <button class="btn btn-secondary btn-small" onclick="openMergeModal('${escapeHtml(branch.name)}')">Merge</button>
                                     <button class="btn btn-danger btn-small" onclick="deleteBranch('${escapeHtml(branch.name)}')">Delete</button>`
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="empty-state">
                    <div class="empty-icon">🌿</div>
                    <div class="empty-title">No branches</div>
                    <p>Click "Create Branch" to get started</p>
                </div>
            `}
        </div>
    `;
}

async function renderChanges() {
    const { status } = repoData;
    const content = document.getElementById('main-content');

    // Show loading state
    content.innerHTML = `
        <h1 class="page-title">Working Changes</h1>
        <p class="page-subtitle">Pending modifications to the map</p>
        <div class="card">
            <div class="loading"><div class="spinner"></div></div>
        </div>
    `;

    // Fetch diff to see actual changes
    const diffData = await fetchAPI('/diff');
    
    const hasChanges = status.has_changes || (diffData && diffData.has_changes);
    const diff = diffData?.diff;

    // Build changes list from diff
    let changesHtml = '';
    if (hasChanges && diff) {
        const changes = [];
        
        // Add layer changes
        if (diff.layer_changes && diff.layer_changes.length > 0) {
            diff.layer_changes.forEach(change => {
                const type = change.change_type || 'modified';
                const layerId = change.layer_id || 'Unknown';
                const layerTitle = change.layer_title || change.details?.title || layerId;
                changes.push({
                    type: type,
                    name: layerTitle,
                    id: layerId
                });
            });
        }

        // Add table changes
        if (diff.table_changes && diff.table_changes.length > 0) {
            diff.table_changes.forEach(change => {
                const type = change.change_type || 'modified';
                const tableId = change.layer_id || 'Unknown';
                changes.push({
                    type: type,
                    name: `Table: ${tableId}`,
                    id: tableId
                });
            });
        }

        // Add property changes
        if (diff.property_changes && Object.keys(diff.property_changes).length > 0) {
            changes.push({
                type: 'modified',
                name: 'Map properties',
                id: 'properties'
            });
        }

        if (changes.length > 0) {
            changesHtml = `
                <div class="changes-list">
                    ${changes.map(change => `
                        <div class="change-item">
                            <span class="change-type ${change.type}">${change.type.charAt(0).toUpperCase() + change.type.slice(1)}</span>
                            <span>${escapeHtml(change.name)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            // Fallback: show generic message if diff doesn't have detailed changes
            changesHtml = `
                <div class="changes-list">
                    <div class="change-item">
                        <span class="change-type modified">Modified</span>
                        <span>map.json (web map data)</span>
                    </div>
                </div>
            `;
        }
    } else if (hasChanges) {
        // Has changes but no diff details available
        changesHtml = `
            <div class="changes-list">
                <div class="change-item">
                    <span class="change-type modified">Modified</span>
                    <span>map.json (web map data)</span>
                </div>
            </div>
        `;
    }

    content.innerHTML = `
        <h1 class="page-title">Working Changes</h1>
        <p class="page-subtitle">Pending modifications to the map</p>

        <div class="card">
            ${hasChanges ? `
                ${changesHtml}
                <div style="margin-top: 1.5rem; display: flex; gap: 1rem;">
                    <button class="btn btn-primary" onclick="openCommitModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Commit Changes
                    </button>
                </div>
            ` : `
                <div class="empty-state">
                    <div class="empty-icon">✨</div>
                    <div class="empty-title">No pending changes</div>
                    <p>Working directory is clean. Pull from Portal or make changes to see them here.</p>
                </div>
            `}
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Quick Commit</h3>
            </div>
            <div class="form-group">
                <label class="form-label">Commit Message</label>
                <input type="text" class="form-input" id="quick-commit-message" placeholder="Describe your changes..." ${!hasChanges ? 'disabled' : ''}>
            </div>
            <button class="btn btn-primary" onclick="quickCommit()" ${!hasChanges ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                Create Commit
            </button>
        </div>
    `;
}

async function quickCommit() {
    const message = document.getElementById('quick-commit-message').value.trim();
    if (!message) {
        showToast('Commit message is required', 'error');
        return;
    }

    const result = await postAPI('/commit', { message });
    if (result.success) {
        showToast(`Commit ${result.commit.id.substring(0, 8)} created`, 'success');
        document.getElementById('quick-commit-message').value = '';
        await loadRepoData();
        renderPage();
    } else {
        showToast(result.error || 'Failed to create commit', 'error');
    }
}

async function renderRemote() {
    const content = document.getElementById('main-content');
    const { status } = repoData;

    // Check portal status
    await checkPortalStatus();

    content.innerHTML = `
        <h1 class="page-title">Remote Operations</h1>
        <p class="page-subtitle">Sync with ArcGIS Portal</p>

        <!-- Connection Status -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Portal Connection</h3>
                <div class="connection-status ${portalStatus.connected ? 'connected' : 'disconnected'}">
                    <span class="status-dot"></span>
                    ${portalStatus.connected ? `Connected as ${escapeHtml(portalStatus.username || 'user')}` : 'Disconnected'}
                </div>
            </div>
            ${portalStatus.connected ? `
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                    Connected to <code>${escapeHtml(portalStatus.url || 'Portal')}</code>
                </p>
            ` : `
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                    Connect to ArcGIS Portal to clone, pull, and push web maps.
                </p>
            `}
            <button class="btn ${portalStatus.connected ? 'btn-secondary' : 'btn-primary'}" onclick="openPortalModal()">
                ${portalStatus.connected ? 'Reconnect' : 'Connect to Portal'}
            </button>
        </div>

        <!-- Clone Section -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Clone Web Map</h3>
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Clone a web map from Portal to create a new local repository.
            </p>
            <button class="btn btn-primary" onclick="openCloneModal()" ${!portalStatus.connected ? 'disabled style="opacity: 0.5;"' : ''}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                </svg>
                Clone from Portal
            </button>
        </div>

        <!-- Pull/Push Section -->
        ${status.remote ? `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Sync Repository</h3>
                </div>
                <div style="margin-bottom: 1rem; padding: 1rem; background: var(--bg-panel); border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                    <div style="color: var(--text-secondary);">Remote: <span style="color: var(--text-primary);">${escapeHtml(status.remote.url || 'origin')}</span></div>
                    <div style="color: var(--text-secondary);">Item ID: <span style="color: var(--accent-secondary);">${escapeHtml(status.remote.item_id || 'Not set')}</span></div>
                </div>
                <div style="display: flex; gap: 1rem;">
                    <button class="btn btn-secondary" onclick="pullFromPortal()" ${!portalStatus.connected ? 'disabled style="opacity: 0.5;"' : ''}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="8 17 12 21 16 17"/>
                            <line x1="12" y1="12" x2="12" y2="21"/>
                            <path d="M20.88 18.09A5 5 0 0018 9h-1.26A8 8 0 103 16.29"/>
                        </svg>
                        Pull from Portal
                    </button>
                    <button class="btn btn-primary" onclick="pushToPortal()" ${!portalStatus.connected ? 'disabled style="opacity: 0.5;"' : ''}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="16 16 12 12 8 16"/>
                            <line x1="12" y1="12" x2="12" y2="21"/>
                            <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/>
                        </svg>
                        Push to Portal
                    </button>
                </div>
            </div>
        ` : `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Sync Repository</h3>
                </div>
                <div class="empty-state" style="padding: 2rem;">
                    <div class="empty-icon">🔗</div>
                    <div class="empty-title">No remote configured</div>
                    <p>Clone a web map from Portal to set up remote sync, or configure a remote manually.</p>
                </div>
            </div>
        `}
    `;
}

async function renderRepositories() {
    const content = document.getElementById('main-content');
    
    // Show loading state
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    const reposData = await fetchAPI('/repositories');
    
    if (reposData.error) {
        content.innerHTML = `
            <h1 class="page-title">Repositories</h1>
            <p class="page-subtitle">Browse all GitMap repositories</p>
            
            <div class="card">
                <div class="error-state">
                    <h3>Error loading repositories</h3>
                    <p>${reposData.error}</p>
                </div>
            </div>
        `;
        return;
    }
    
    const repos = reposData.repositories || [];
    const currentPath = repoData?.status?.path || '';
    
    content.innerHTML = `
        <h1 class="page-title">Repositories</h1>
        <p class="page-subtitle">${repos.length} repositories found in ${reposData.directory || '/app/repositories'}</p>
        
        <div class="card">
            ${repos.length > 0 ? `
                <div class="branch-list">
                    ${repos.map(repo => `
                        <div class="branch-item ${repo.path === currentPath ? 'current' : ''}" 
                             onclick="switchRepository('${repo.path}')" 
                             style="cursor: pointer;">
                            <div class="branch-name">
                                <svg class="branch-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
                                </svg>
                                ${escapeHtml(repo.project_name || repo.name)}
                            </div>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                ${repo.path === currentPath ? '<span class="branch-badge">Active</span>' : ''}
                                <span style="font-size: 0.75rem; color: var(--text-muted);">${repo.current_branch}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="empty-state">
                    <div class="empty-icon">📁</div>
                    <div class="empty-title">No repositories found</div>
                    <p>No GitMap repositories found in the repositories directory.</p>
                    <p style="margin-top: 1rem; color: var(--text-muted);">
                        Clone a map with <code>gitmap clone &lt;item_id&gt;</code> or initialize one with <code>gitmap init</code>
                    </p>
                </div>
            `}
        </div>
    `;
}

async function switchRepository(path) {
    try {
        const response = await fetch('/api/repo/switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path }),
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Reload all data with new repository
            await loadRepoData();
            // Go back to overview
            showPage('overview');
        } else {
            alert(`Error switching repository: ${result.error}`);
        }
    } catch (error) {
        alert(`Error switching repository: ${error.message}`);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(timestamp) {
    if (!timestamp) return 'Unknown date';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

async function refreshData() {
    const content = document.getElementById('main-content');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    // Force reload repo from disk to pick up external changes
    await postAPI('/repo/reload', {});
    await loadRepoData();
    await checkPortalStatus();
    renderPage();
    showToast('Data refreshed', 'success');
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadRepoData();
    await checkPortalStatus();
    renderPage();
});
