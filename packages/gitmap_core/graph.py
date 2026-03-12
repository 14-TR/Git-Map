"""GitMap commit graph builder.

Builds and renders an ASCII commit graph from repository history,
inspired by `git log --graph`. Supports linear histories, diverging
branches, and merge commits (two-parent).

Execution Context:
    Library module - used by CLI log command

Dependencies:
    - gitmap_core.repository: Repository, Commit

Metadata:
    Version: 1.0.0
    Author: GitMap Team
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gitmap_core.models import Commit
    from gitmap_core.repository import Repository


# ---- Data Classes -------------------------------------------------------------------------------------------


@dataclass
class GraphNode:
    """A commit node in the graph, with rendering metadata.

    Attributes:
        commit: The underlying Commit object.
        lane: Column index this commit occupies.
        labels: Branch / ref labels pointing at this commit.
        prefix_line: The ``* | | `` prefix for the commit line.
        connector_lines: Lines drawn between this node and the next.
    """

    commit: "Commit"
    lane: int
    labels: list[str] = field(default_factory=list)
    prefix_line: str = ""
    connector_lines: list[str] = field(default_factory=list)


# ---- Graph Builder ------------------------------------------------------------------------------------------


def _collect_commits(
        repo: "Repository",
        limit: int,
) -> tuple[dict[str, "Commit"], dict[str, list[str]]]:
    """Walk all branches and collect reachable commits.

    Args:
        repo: Repository to walk.
        limit: Maximum commits to collect per branch (soft cap).

    Returns:
        Tuple of (all_commits, labels) where all_commits maps commit_id
        to Commit and labels maps commit_id to list of ref label strings.
    """
    branches = repo.list_branches()
    current_branch = repo.get_current_branch()
    head_commit_id = repo.get_head_commit()

    labels: dict[str, list[str]] = {}
    all_commits: dict[str, "Commit"] = {}

    for branch in branches:
        tip = repo.get_branch_commit(branch)
        if not tip:
            continue

        # Build the ref label
        is_current = (branch == current_branch)
        if is_current and tip == head_commit_id:
            label = f"HEAD -> {branch}"
        else:
            label = branch
        labels.setdefault(tip, []).append(label)

        # Walk the chain
        cid = tip
        walked = 0
        while cid and walked < limit * 4:
            if cid in all_commits:
                break
            commit = repo.get_commit(cid)
            if not commit:
                break
            all_commits[cid] = commit
            # Walk both parents for merge commits
            if commit.parent2 and commit.parent2 not in all_commits:
                sub_cid = commit.parent2
                sub_walked = 0
                while sub_cid and sub_walked < limit * 2:
                    if sub_cid in all_commits:
                        break
                    sub_commit = repo.get_commit(sub_cid)
                    if not sub_commit:
                        break
                    all_commits[sub_cid] = sub_commit
                    sub_cid = sub_commit.parent
                    sub_walked += 1
            cid = commit.parent
            walked += 1

    return all_commits, labels


def _topological_sort(
        all_commits: dict[str, "Commit"],
) -> list["Commit"]:
    """Sort commits in reverse chronological topological order.

    Commits are sorted newest-first (children before parents) so the
    lane-drawing algorithm can assign columns correctly.  Uses a
    modified Kahn's algorithm that starts from branch tips (commits
    that have no children in the visible set).

    Args:
        all_commits: Dict mapping commit_id to Commit.

    Returns:
        Ordered list of Commits (newest-first, children before parents).
    """
    # Build commit -> children map (reverse of parent pointers)
    children_of: dict[str, list[str]] = {}
    for cid, commit in all_commits.items():
        if commit.parent and commit.parent in all_commits:
            children_of.setdefault(commit.parent, []).append(cid)
        if commit.parent2 and commit.parent2 in all_commits:
            children_of.setdefault(commit.parent2, []).append(cid)

    # in_degree = number of children not yet emitted
    # Tips (branch heads) have in_degree == 0 → start there
    in_degree = {cid: len(children_of.get(cid, [])) for cid in all_commits}

    # Seed the queue with tips, sorted newest first to break ties
    queue = sorted(
        [cid for cid, deg in in_degree.items() if deg == 0],
        key=lambda cid: all_commits[cid].timestamp,
        reverse=True,
    )

    result: list["Commit"] = []
    while queue:
        cid = queue.pop(0)
        result.append(all_commits[cid])
        commit = all_commits[cid]
        # Release parent(s): when all their children are emitted, they
        # become eligible.
        for parent_id in (commit.parent, commit.parent2):
            if parent_id and parent_id in all_commits:
                in_degree[parent_id] -= 1
                if in_degree[parent_id] == 0:
                    # Insert in timestamp-sorted order (newest first)
                    ts = all_commits[parent_id].timestamp
                    inserted = False
                    for i, qcid in enumerate(queue):
                        if all_commits[qcid].timestamp < ts:
                            queue.insert(i, parent_id)
                            inserted = True
                            break
                    if not inserted:
                        queue.append(parent_id)

    # Append any unreachable commits (shouldn't happen in a valid repo)
    seen = {c.id for c in result}
    for cid, commit in all_commits.items():
        if cid not in seen:
            result.append(commit)

    return result


def _build_lane_prefix(lanes: list[str | None], active_lane: int) -> str:
    """Build the ``* | |`` prefix string for a commit row.

    Args:
        lanes: Current lane state (commit_id each lane is waiting for).
        active_lane: The lane index where ``*`` is placed.

    Returns:
        String like ``* | |`` or ``| * |``.
    """
    parts = []
    for i, lane_cid in enumerate(lanes):
        if i == active_lane:
            parts.append("*")
        elif lane_cid is not None:
            parts.append("|")
        else:
            parts.append(" ")
    return " ".join(parts).rstrip()


def _build_connector(
        lanes_before: list[str | None],
        lanes_after: list[str | None],
        active_lane: int,
        merge_lane: int | None,
) -> list[str]:
    """Build connector lines between two commit rows.

    Args:
        lanes_before: Lane state immediately after placing the commit ``*``.
        lanes_after: Lane state for the next commit row.
        active_lane: Lane of the current commit.
        merge_lane: Lane of the second parent (merge), or None.

    Returns:
        List of connector line strings (may be empty for simple cases).
    """
    # If no lane count change and no merge, just return empty (straight lines
    # are implied by the next commit's ``|``).
    if merge_lane is None:
        return []

    # For a merge commit: draw the ``|\`` connector once.
    parts = []
    for i in range(max(len(lanes_before), merge_lane + 1)):
        if i == active_lane:
            parts.append("|")
        elif i == merge_lane:
            parts.append("\\")
        elif i < len(lanes_before) and lanes_before[i] is not None:
            parts.append("|")
        else:
            parts.append(" ")
    return [" ".join(parts).rstrip()]


# ---- Public API ---------------------------------------------------------------------------------------------


def build_graph(
        repo: "Repository",
        limit: int = 20,
) -> list[GraphNode]:
    """Build a list of GraphNodes representing the commit graph.

    Args:
        repo: Repository to build from.
        limit: Maximum number of nodes to include.

    Returns:
        Ordered list of GraphNodes (newest commit first) ready for
        rendering.
    """
    all_commits, labels = _collect_commits(repo, limit)
    if not all_commits:
        return []

    sorted_commits = _topological_sort(all_commits)
    if len(sorted_commits) > limit:
        sorted_commits = sorted_commits[:limit]

    # Lane state: each slot holds the commit_id we're waiting for, or None.
    lanes: list[str | None] = []
    nodes: list[GraphNode] = []

    for commit in sorted_commits:
        cid = commit.id

        # --- Find this commit's lane ---
        my_lane: int | None = None
        for i, lane_cid in enumerate(lanes):
            if lane_cid == cid:
                my_lane = i
                break

        if my_lane is None:
            # Assign a free lane, or extend
            try:
                my_lane = lanes.index(None)
                lanes[my_lane] = cid
            except ValueError:
                my_lane = len(lanes)
                lanes.append(cid)

        # --- Emit the commit line prefix ---
        prefix = _build_lane_prefix(lanes, my_lane)

        # --- Update lanes for this commit's parents ---
        lanes_copy = list(lanes)

        merge_lane: int | None = None

        # Primary parent takes over our lane
        if commit.parent and commit.parent in all_commits:
            lanes[my_lane] = commit.parent
        else:
            lanes[my_lane] = None

        # Second parent (merge commit): add to a lane
        if commit.parent2 and commit.parent2 in all_commits:
            # Check if already tracked
            already = None
            for i, lc in enumerate(lanes):
                if lc == commit.parent2:
                    already = i
                    break
            if already is not None:
                merge_lane = already
            else:
                try:
                    merge_lane = lanes.index(None)
                    lanes[merge_lane] = commit.parent2
                except ValueError:
                    merge_lane = len(lanes)
                    lanes.append(commit.parent2)

        # Trim trailing None lanes to keep rendering compact
        while lanes and lanes[-1] is None:
            lanes.pop()

        # --- Build connector lines ---
        connector_lines = _build_connector(
            lanes_copy,
            lanes,
            my_lane,
            merge_lane,
        )

        node = GraphNode(
            commit=commit,
            lane=my_lane,
            labels=labels.get(cid, []),
            prefix_line=prefix,
            connector_lines=connector_lines,
        )
        nodes.append(node)

    return nodes
