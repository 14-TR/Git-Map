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

function showCommitDetail(commitId) {
    const { commits } = repoData;
    const commit = (commits?.commits || []).find(c => c.id === commitId);

    if (!commit) {
        showToast('Commit not found', 'error');
        return;
    }

    const modalBody = document.getElementById('commit-detail-body');

    modalBody.innerHTML = `
        <div class="commit-detail">
            <div class="commit-detail-header">
                <div class="commit-detail-hash">${escapeHtml(commit.id || '')}</div>
                ${commit.branches && commit.branches.length > 0 ?
                    `<div class="commit-detail-branches">
                        ${commit.branches.map(b => `<span class="branch-badge">${escapeHtml(b)}</span>`).join(' ')}
                    </div>` : ''
                }
            </div>

            <div class="commit-detail-message">${escapeHtml(commit.message || 'No message')}</div>

            <div class="commit-detail-meta">
                <div class="meta-row">
                    <span class="meta-label">Author</span>
                    <span class="meta-value">${escapeHtml(commit.author || 'Unknown')}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Date</span>
                    <span class="meta-value">${formatDate(commit.timestamp)}</span>
                </div>
                ${commit.parent ? `
                    <div class="meta-row">
                        <span class="meta-label">Parent</span>
                        <span class="meta-value commit-hash clickable" onclick="showCommitDetail('${escapeHtml(commit.parent)}')">${commit.parent.substring(0, 8)}</span>
                    </div>
                ` : ''}
            </div>

            ${commit.changes ? `
                <div class="commit-detail-changes">
                    <h4>Changes</h4>
                    <div class="changes-summary">
                        <span class="change-stat added">+${commit.changes.added || 0} added</span>
                        <span class="change-stat modified">~${commit.changes.modified || 0} modified</span>
                        <span class="change-stat removed">-${commit.changes.removed || 0} removed</span>
                    </div>
                </div>
            ` : ''}
        </div>
    `;

    openModal('commit-detail-modal');
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

    // Pages that don't require a repository
    const noRepoPages = ['portal', 'repositories'];

    if (!noRepoPages.includes(currentPage) && (!repoData || repoData.status?.error)) {
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
        case 'portal':
            renderPortalBrowser();
            break;
        case 'context':
            renderContextTimeline();
            break;
        case 'settings':
            renderSettings();
            break;
        case 'lsm':
            renderLayerSettingsMerge();
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

let commitSearchQuery = '';
let commitAuthorFilter = '';

function renderCommits() {
    const { commits, status } = repoData;
    const content = document.getElementById('main-content');

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
            </div>
        `;
        return;
    }

    let commitList = commits?.commits || [];

    // Apply filters
    if (commitSearchQuery) {
        const query = commitSearchQuery.toLowerCase();
        commitList = commitList.filter(c =>
            (c.message || '').toLowerCase().includes(query) ||
            (c.id || '').toLowerCase().includes(query)
        );
    }
    if (commitAuthorFilter) {
        const author = commitAuthorFilter.toLowerCase();
        commitList = commitList.filter(c =>
            (c.author || '').toLowerCase().includes(author)
        );
    }

    // Get unique authors for filter dropdown
    const authors = [...new Set((commits?.commits || []).map(c => c.author).filter(Boolean))];

    content.innerHTML = `
        <h1 class="page-title">Commit History</h1>
        <p class="page-subtitle">${commits?.commits?.length || 0} commits in repository</p>

        <div class="card">
            <div class="filter-bar">
                <input type="text" class="form-input" id="commit-search"
                       placeholder="Search commits by message or hash..."
                       value="${escapeHtml(commitSearchQuery)}"
                       oninput="filterCommits()">
                <select class="form-input" id="commit-author-filter" onchange="filterCommits()">
                    <option value="">All Authors</option>
                    ${authors.map(a => `<option value="${escapeHtml(a)}" ${commitAuthorFilter === a ? 'selected' : ''}>${escapeHtml(a)}</option>`).join('')}
                </select>
                ${(commitSearchQuery || commitAuthorFilter) ? `
                    <button class="btn btn-secondary" onclick="clearCommitFilters()">Clear Filters</button>
                ` : ''}
            </div>
        </div>

        <div class="card">
            ${commitList.length > 0 ? `
                <div class="card-header">
                    <span style="color: var(--text-muted);">Showing ${commitList.length} of ${commits?.commits?.length || 0} commits</span>
                </div>
                <div class="commit-list">
                    ${commitList.map((commit, i) => `
                        <div class="commit-item" onclick="showCommitDetail('${escapeHtml(commit.id || '')}')">
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
                    <div class="empty-icon">${commitSearchQuery || commitAuthorFilter ? '🔍' : '📝'}</div>
                    <div class="empty-title">${commitSearchQuery || commitAuthorFilter ? 'No matching commits' : 'No commits yet'}</div>
                    <p>${commitSearchQuery || commitAuthorFilter ?
                        'Try adjusting your search criteria.' :
                        'Create your first commit with <code>gitmap commit -m "message"</code>'
                    }</p>
                </div>
            `}
        </div>
    `;
}

function filterCommits() {
    commitSearchQuery = document.getElementById('commit-search').value;
    commitAuthorFilter = document.getElementById('commit-author-filter').value;
    renderCommits();
}

function clearCommitFilters() {
    commitSearchQuery = '';
    commitAuthorFilter = '';
    renderCommits();
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

// ============================================================================
// Portal Browser Page
// ============================================================================

let portalWebmaps = [];
let portalSearchQuery = '';
let portalSearchOwner = '';

async function renderPortalBrowser() {
    const content = document.getElementById('main-content');

    // Check portal status first
    await checkPortalStatus();

    if (!portalStatus.connected) {
        content.innerHTML = `
            <h1 class="page-title">Portal Browser</h1>
            <p class="page-subtitle">Browse and clone web maps from ArcGIS Portal</p>

            <div class="card">
                <div class="empty-state">
                    <div class="empty-icon">🔌</div>
                    <div class="empty-title">Not Connected</div>
                    <p>Connect to ArcGIS Portal to browse available web maps.</p>
                    <button class="btn btn-primary" style="margin-top: 1rem;" onclick="openPortalModal()">
                        Connect to Portal
                    </button>
                </div>
            </div>
        `;
        return;
    }

    content.innerHTML = `
        <h1 class="page-title">Portal Browser</h1>
        <p class="page-subtitle">Connected to ${escapeHtml(portalStatus.url || 'Portal')} as ${escapeHtml(portalStatus.username || 'user')}</p>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Search Web Maps</h3>
            </div>
            <div class="search-filters">
                <div class="form-group" style="flex: 1;">
                    <label class="form-label">Search Query</label>
                    <input type="text" class="form-input" id="portal-search-query"
                           placeholder="Search by title, tags, or description..."
                           value="${escapeHtml(portalSearchQuery)}"
                           onkeypress="if(event.key==='Enter') searchPortalMaps()">
                </div>
                <div class="form-group" style="width: 200px;">
                    <label class="form-label">Owner</label>
                    <input type="text" class="form-input" id="portal-search-owner"
                           placeholder="Username"
                           value="${escapeHtml(portalSearchOwner)}"
                           onkeypress="if(event.key==='Enter') searchPortalMaps()">
                </div>
                <div class="form-group" style="align-self: flex-end;">
                    <button class="btn btn-primary" onclick="searchPortalMaps()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                        Search
                    </button>
                </div>
            </div>
        </div>

        <div class="card" id="webmaps-results">
            <div class="empty-state">
                <div class="empty-icon">🗺️</div>
                <div class="empty-title">Search for Web Maps</div>
                <p>Enter a search query or owner to find web maps, or click Search to list all available maps.</p>
            </div>
        </div>
    `;
}

async function searchPortalMaps() {
    const query = document.getElementById('portal-search-query').value.trim();
    const owner = document.getElementById('portal-search-owner').value.trim();

    portalSearchQuery = query;
    portalSearchOwner = owner;

    const resultsContainer = document.getElementById('webmaps-results');
    resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const params = new URLSearchParams();
        if (query) params.append('query', query);
        if (owner) params.append('owner', owner);

        const response = await fetch(`/api/portal/webmaps?${params.toString()}`);
        const data = await response.json();

        if (!data.success) {
            resultsContainer.innerHTML = `<div class="error-state">${escapeHtml(data.error)}</div>`;
            return;
        }

        portalWebmaps = data.webmaps || [];

        if (portalWebmaps.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <div class="empty-title">No Web Maps Found</div>
                    <p>Try adjusting your search criteria.</p>
                </div>
            `;
            return;
        }

        resultsContainer.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">${portalWebmaps.length} Web Maps Found</h3>
            </div>
            <div class="webmap-grid">
                ${portalWebmaps.map(map => `
                    <div class="webmap-card" onclick="selectWebmapForClone('${escapeHtml(map.id)}', '${escapeHtml(map.title || 'Untitled')}')">
                        <div class="webmap-thumbnail">
                            ${map.thumbnail ?
                                `<img src="${escapeHtml(map.thumbnail)}" alt="${escapeHtml(map.title)}" onerror="this.style.display='none'">` :
                                '<div class="webmap-thumbnail-placeholder">🗺️</div>'
                            }
                        </div>
                        <div class="webmap-info">
                            <div class="webmap-title">${escapeHtml(map.title || 'Untitled')}</div>
                            <div class="webmap-meta">
                                <span>Owner: ${escapeHtml(map.owner || 'Unknown')}</span>
                                ${map.numLayers !== undefined ? `<span>${map.numLayers} layers</span>` : ''}
                            </div>
                            <div class="webmap-id">${escapeHtml(map.id)}</div>
                        </div>
                        <button class="btn btn-primary btn-small webmap-clone-btn" onclick="event.stopPropagation(); cloneWebmap('${escapeHtml(map.id)}')">
                            Clone
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        resultsContainer.innerHTML = `<div class="error-state">Error: ${escapeHtml(error.message)}</div>`;
    }
}

function selectWebmapForClone(itemId, title) {
    document.getElementById('clone-item-id').value = itemId;
    document.getElementById('clone-directory').value = '';
    openModal('clone-modal');
}

async function cloneWebmap(itemId) {
    showToast('Cloning map...', 'info');
    const result = await postAPI('/clone', { item_id: itemId });

    if (result.success) {
        showToast(`Cloned '${result.title}' (${result.layers} layers)`, 'success');
        await loadRepoData();
        showPage('overview');
    } else {
        showToast(result.error || 'Clone failed', 'error');
    }
}

// ============================================================================
// Context Timeline Page
// ============================================================================

async function renderContextTimeline() {
    const content = document.getElementById('main-content');
    const { status } = repoData;

    content.innerHTML = `
        <h1 class="page-title">Context Timeline</h1>
        <p class="page-subtitle">Event history and relationships</p>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                    Activity Timeline
                </h3>
                <div style="display: flex; gap: 0.5rem;">
                    <select class="form-input" id="context-filter" style="width: auto;" onchange="filterContextEvents()">
                        <option value="all">All Events</option>
                        <option value="commit">Commits</option>
                        <option value="push">Pushes</option>
                        <option value="pull">Pulls</option>
                        <option value="merge">Merges</option>
                        <option value="branch">Branches</option>
                    </select>
                </div>
            </div>
            <div id="context-timeline-content">
                ${renderContextEvents()}
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Export Context</h3>
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Export the context graph for documentation or visualization.
            </p>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button class="btn btn-secondary" onclick="exportContext('mermaid')">Export Mermaid</button>
                <button class="btn btn-secondary" onclick="exportContext('ascii')">Export ASCII</button>
                <button class="btn btn-secondary" onclick="exportContext('html')">Export HTML</button>
            </div>
        </div>
    `;
}

function renderContextEvents() {
    const { commits } = repoData;
    const commitList = commits?.commits || [];

    if (commitList.length === 0) {
        return `
            <div class="empty-state" style="padding: 2rem;">
                <div class="empty-icon">📊</div>
                <div class="empty-title">No Events Yet</div>
                <p>Activity will appear here as you make commits, push, pull, and merge.</p>
            </div>
        `;
    }

    // Build timeline from commits (we can expand this to include other events)
    return `
        <div class="timeline">
            ${commitList.slice(0, 20).map((commit, i) => `
                <div class="timeline-item" data-type="commit">
                    <div class="timeline-marker commit"></div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="timeline-type">Commit</span>
                            <span class="timeline-hash">${(commit.id || '').substring(0, 8)}</span>
                        </div>
                        <div class="timeline-message">${escapeHtml(commit.message || 'No message')}</div>
                        <div class="timeline-meta">
                            <span>${escapeHtml(commit.author || 'Unknown')}</span>
                            <span>${formatDate(commit.timestamp)}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function filterContextEvents() {
    const filter = document.getElementById('context-filter').value;
    const items = document.querySelectorAll('.timeline-item');

    items.forEach(item => {
        if (filter === 'all' || item.dataset.type === filter) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

async function exportContext(format) {
    showToast(`Exporting context as ${format}...`, 'info');
    // This would call a backend API to generate the export
    // For now, show a placeholder message
    showToast(`Export to ${format} - Coming soon!`, 'warning');
}

// ============================================================================
// Settings Page
// ============================================================================

async function renderSettings() {
    const content = document.getElementById('main-content');
    const { status } = repoData || {};

    // Fetch current config
    let config = {};
    try {
        const configData = await fetchAPI('/config');
        config = configData.config || {};
    } catch (e) {
        // Config endpoint may not exist yet
    }

    content.innerHTML = `
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">Repository and application configuration</p>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
                    </svg>
                    Repository Configuration
                </h3>
            </div>
            <div class="settings-form">
                <div class="form-group">
                    <label class="form-label">Project Name</label>
                    <input type="text" class="form-input" id="setting-project-name"
                           value="${escapeHtml(config.project_name || status?.project_name || '')}"
                           placeholder="My Web Map Project">
                </div>
                <div class="form-group">
                    <label class="form-label">User Name</label>
                    <input type="text" class="form-input" id="setting-user-name"
                           value="${escapeHtml(config.user_name || '')}"
                           placeholder="Your Name">
                </div>
                <div class="form-group">
                    <label class="form-label">User Email</label>
                    <input type="text" class="form-input" id="setting-user-email"
                           value="${escapeHtml(config.user_email || '')}"
                           placeholder="your@email.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Production Branch</label>
                    <input type="text" class="form-input" id="setting-production-branch"
                           value="${escapeHtml(config.production_branch || '')}"
                           placeholder="main (triggers notifications on push)">
                    <small style="color: var(--text-muted);">Branch that triggers notifications when pushed to Portal</small>
                </div>
                <div class="form-group">
                    <label class="form-label" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                        <input type="checkbox" id="setting-auto-visualize" ${config.auto_visualize ? 'checked' : ''}>
                        Auto-visualize context after events
                    </label>
                </div>
                <button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <line x1="3" y1="9" x2="21" y2="9"/>
                        <line x1="9" y1="21" x2="9" y2="9"/>
                    </svg>
                    Theme
                </h3>
            </div>
            <div style="display: flex; gap: 1rem;">
                <button class="btn btn-secondary theme-btn ${!document.body.classList.contains('light-theme') ? 'active' : ''}" onclick="setTheme('dark')">
                    🌙 Dark
                </button>
                <button class="btn btn-secondary theme-btn ${document.body.classList.contains('light-theme') ? 'active' : ''}" onclick="setTheme('light')">
                    ☀️ Light
                </button>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                        <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
                    </svg>
                    Keyboard Shortcuts
                </h3>
            </div>
            <div class="shortcuts-grid">
                <div class="shortcut-item"><kbd>R</kbd> Refresh data</div>
                <div class="shortcut-item"><kbd>N</kbd> New commit</div>
                <div class="shortcut-item"><kbd>B</kbd> New branch</div>
                <div class="shortcut-item"><kbd>1-6</kbd> Switch pages</div>
                <div class="shortcut-item"><kbd>Esc</kbd> Close modal</div>
                <div class="shortcut-item"><kbd>?</kbd> Show shortcuts</div>
            </div>
        </div>
    `;
}

async function saveSettings() {
    const settings = {
        project_name: document.getElementById('setting-project-name').value.trim(),
        user_name: document.getElementById('setting-user-name').value.trim(),
        user_email: document.getElementById('setting-user-email').value.trim(),
        production_branch: document.getElementById('setting-production-branch').value.trim(),
        auto_visualize: document.getElementById('setting-auto-visualize').checked,
    };

    const result = await postAPI('/config', settings);

    if (result.success) {
        showToast('Settings saved', 'success');
        await loadRepoData();
    } else {
        showToast(result.error || 'Failed to save settings', 'error');
    }
}

function setTheme(theme) {
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        localStorage.setItem('gitmap-theme', 'light');
    } else {
        document.body.classList.remove('light-theme');
        localStorage.setItem('gitmap-theme', 'dark');
    }
    // Update active state
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

// ============================================================================
// Layer Settings Merge (LSM) Page
// ============================================================================

let lsmSources = [];
let selectedLsmSource = null;

async function renderLayerSettingsMerge() {
    const content = document.getElementById('main-content');

    content.innerHTML = `
        <h1 class="page-title">Layer Settings Merge</h1>
        <p class="page-subtitle">Transfer popup and form settings between branches</p>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="2" width="8" height="8" rx="1"/>
                        <rect x="14" y="2" width="8" height="8" rx="1"/>
                    </svg>
                    Select Source Branch
                </h3>
            </div>
            <div id="lsm-sources-container">
                <div class="loading"><div class="spinner"></div></div>
            </div>
        </div>

        <div class="card" id="lsm-preview-card" style="display: none;">
            <div class="card-header">
                <h3 class="card-title">Transfer Preview</h3>
            </div>
            <div id="lsm-preview-content"></div>
        </div>
    `;

    // Load available sources
    await loadLsmSources();
}

async function loadLsmSources() {
    const container = document.getElementById('lsm-sources-container');

    try {
        const data = await fetchAPI('/lsm/sources');

        if (!data.success) {
            container.innerHTML = `<div class="error-state">${escapeHtml(data.error)}</div>`;
            return;
        }

        lsmSources = data.sources || [];
        const currentBranch = data.current_branch;

        if (lsmSources.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 2rem;">
                    <div class="empty-icon">🌿</div>
                    <div class="empty-title">No branches available</div>
                    <p>Create branches and commits to use Layer Settings Merge.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Select a source branch to transfer popup and form settings from.
                Settings will be applied to your current working index.
            </p>
            <div class="lsm-source-list">
                ${lsmSources.map(source => `
                    <div class="lsm-source-item ${source.name === currentBranch ? 'current' : ''}"
                         onclick="selectLsmSource('${escapeHtml(source.name)}')">
                        <div class="lsm-source-info">
                            <div class="lsm-source-name">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="6" y1="3" x2="6" y2="15"/>
                                    <circle cx="18" cy="6" r="3"/>
                                    <circle cx="6" cy="18" r="3"/>
                                    <path d="M18 9a9 9 0 01-9 9"/>
                                </svg>
                                ${escapeHtml(source.name)}
                                ${source.name === currentBranch ? '<span class="branch-badge">Current</span>' : ''}
                            </div>
                            <div class="lsm-source-meta">
                                <span>${escapeHtml(source.message || 'No message')}</span>
                                <span>${source.timestamp ? formatDate(source.timestamp) : ''}</span>
                            </div>
                        </div>
                        <button class="btn btn-primary btn-small" onclick="event.stopPropagation(); previewLsm('${escapeHtml(source.name)}')">
                            Preview
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        container.innerHTML = `<div class="error-state">Error: ${escapeHtml(error.message)}</div>`;
    }
}

function selectLsmSource(sourceName) {
    selectedLsmSource = sourceName;
    document.querySelectorAll('.lsm-source-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
}

async function previewLsm(sourceBranch) {
    selectedLsmSource = sourceBranch;
    const previewCard = document.getElementById('lsm-preview-card');
    const previewContent = document.getElementById('lsm-preview-content');

    previewCard.style.display = 'block';
    previewContent.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const result = await postAPI('/lsm/preview', { source_branch: sourceBranch });

        if (!result.success) {
            previewContent.innerHTML = `<div class="error-state">${escapeHtml(result.error)}</div>`;
            return;
        }

        const summary = result.summary;

        previewContent.innerHTML = `
            <div class="lsm-summary">
                <div class="lsm-summary-header">
                    <span>Transferring from <strong>${escapeHtml(sourceBranch)}</strong> to <strong>current index</strong></span>
                </div>

                <div class="lsm-stats">
                    <div class="lsm-stat success">
                        <span class="lsm-stat-value">${summary.total_transferred}</span>
                        <span class="lsm-stat-label">Will Transfer</span>
                    </div>
                    <div class="lsm-stat warning">
                        <span class="lsm-stat-value">${summary.total_skipped}</span>
                        <span class="lsm-stat-label">Will Skip</span>
                    </div>
                </div>

                ${summary.transferred_layers.length > 0 ? `
                    <div class="lsm-section">
                        <h4>Layers to Transfer</h4>
                        <ul class="lsm-list success">
                            ${summary.transferred_layers.map(l => `<li>${escapeHtml(l)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${summary.transferred_tables.length > 0 ? `
                    <div class="lsm-section">
                        <h4>Tables to Transfer</h4>
                        <ul class="lsm-list success">
                            ${summary.transferred_tables.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${summary.skipped_layers.length > 0 ? `
                    <div class="lsm-section">
                        <h4>Layers to Skip (not in target)</h4>
                        <ul class="lsm-list warning">
                            ${summary.skipped_layers.map(l => `<li>${escapeHtml(l)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${summary.skipped_tables.length > 0 ? `
                    <div class="lsm-section">
                        <h4>Tables to Skip (not in target)</h4>
                        <ul class="lsm-list warning">
                            ${summary.skipped_tables.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                <div style="margin-top: 1.5rem;">
                    <button class="btn btn-primary" onclick="executeLsm('${escapeHtml(sourceBranch)}')"
                            ${summary.total_transferred === 0 ? 'disabled style="opacity: 0.5;"' : ''}>
                        Apply Settings to Index
                    </button>
                </div>
            </div>
        `;
    } catch (error) {
        previewContent.innerHTML = `<div class="error-state">Error: ${escapeHtml(error.message)}</div>`;
    }
}

async function executeLsm(sourceBranch) {
    const result = await postAPI('/lsm/execute', { source_branch: sourceBranch });

    if (result.success) {
        showToast(`Transferred ${result.summary.total_transferred} layer settings to index`, 'success');
        await loadRepoData();
        showPage('changes');
    } else {
        showToast(result.error || 'Layer settings merge failed', 'error');
    }
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Don't trigger shortcuts when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    // Check for modal open
    const modalOpen = document.querySelector('.modal-overlay.active');

    if (modalOpen) {
        if (e.key === 'Escape') {
            modalOpen.classList.remove('active');
        }
        return;
    }

    switch (e.key.toLowerCase()) {
        case 'r':
            refreshData();
            break;
        case 'n':
            openCommitModal();
            break;
        case 'b':
            openModal('create-branch-modal');
            break;
        case '1':
            showPage('overview');
            break;
        case '2':
            showPage('commits');
            break;
        case '3':
            showPage('branches');
            break;
        case '4':
            showPage('changes');
            break;
        case '5':
            showPage('portal');
            break;
        case '6':
            showPage('remote');
            break;
        case '?':
            showPage('settings');
            break;
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load saved theme
    const savedTheme = localStorage.getItem('gitmap-theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }

    await loadRepoData();
    await checkPortalStatus();
    renderPage();
});
