# -*- coding: utf-8 -*-
"""GitMap.pyt — ArcGIS Pro Python Toolbox

Wraps the gitmap_core library into native ArcGIS Pro tools so GIS
professionals can version-control their web maps directly from the
ArcGIS Pro ribbon or Catalog pane.

Installation:
    1. Ensure gitmap_core is installed:  pip install gitmap-core
    2. In ArcGIS Pro: Catalog > Toolboxes > Add Toolbox > select this .pyt file
    3. The "GitMap" toolbox appears in the Catalog pane

Requirements:
    - ArcGIS Pro 3.0+
    - gitmap_core >= 0.6.0
    - arcpy (included with ArcGIS Pro)

Metadata:
    Version: 0.1.0
    Author: GitMap Team
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Toolbox definition
# ---------------------------------------------------------------------------

class Toolbox:
    """ArcGIS Pro toolbox definition.

    Attributes:
        label: Friendly name shown in ArcGIS Pro.
        alias: Short alias (no spaces) used in Python.
        tools: List of tool classes exposed by this toolbox.
    """

    def __init__(self) -> None:
        self.label = "GitMap"
        self.alias = "gitmap"
        self.tools = [
            InitRepo,
            CommitMap,
            CheckoutBranch,
            CreateBranch,
            LogHistory,
            DiffMaps,
            StatusCheck,
            PushRemote,
            PullRemote,
        ]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get_repo(workspace: str) -> object:
    """Return a Repository instance for the given workspace path.

    Args:
        workspace: Filesystem path to the repository root.

    Returns:
        Initialised gitmap_core Repository object.

    Raises:
        ImportError: If gitmap_core is not installed.
        ValueError: If the path is not a valid GitMap repository.
    """
    try:
        from gitmap_core.repository import Repository
    except ImportError as exc:
        raise ImportError(
            "gitmap_core is not installed. Run: pip install gitmap-core"
        ) from exc
    return Repository(Path(workspace))


def _add_workspace_param(tool) -> object:
    """Return a standard workspace Parameter for use across tools.

    Args:
        tool: The ArcGIS tool instance (unused, kept for signature parity).

    Returns:
        arcpy.Parameter configured for a folder (repository root).
    """
    try:
        import arcpy
        param = arcpy.Parameter(
            displayName="Repository Workspace",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )
        param.value = os.getcwd()
        return param
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Tool: InitRepo
# ---------------------------------------------------------------------------

class InitRepo:
    """Initialise a new GitMap repository in a folder.

    Creates the hidden .gitmap directory structure with an initial
    commit on the 'main' branch.
    """

    def __init__(self) -> None:
        self.label = "Init Repository"
        self.description = (
            "Initialise a new GitMap repository in the selected folder. "
            "Creates .gitmap directory structure and an initial commit."
        )
        self.canRunInBackground = False
        self.category = "Repository"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        description = arcpy.Parameter(
            displayName="Project Description",
            name="description",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        description.value = "GitMap repository for ArcGIS web maps"

        return [workspace, description]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        import arcpy
        from gitmap_core.repository import Repository

        workspace = parameters[0].valueAsText
        description = parameters[1].valueAsText or ""

        path = Path(workspace)
        repo = Repository(path)

        if repo.exists():
            messages.addWarningMessage(
                f"Repository already exists at {workspace}"
            )
            return

        repo.init()
        messages.addMessage(f"✓ Initialised GitMap repository at {workspace}")
        messages.addMessage("  Branch: main")
        messages.addMessage("  Run 'Commit Map' to save your first snapshot.")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: CommitMap
# ---------------------------------------------------------------------------

class CommitMap:
    """Save a snapshot of a web map JSON file as a commit.

    Reads the map JSON, computes a content hash, stores the snapshot
    in the object store, and advances HEAD on the current branch.
    """

    def __init__(self) -> None:
        self.label = "Commit Map"
        self.description = (
            "Save a snapshot of a web map JSON file as a versioned commit."
        )
        self.canRunInBackground = False
        self.category = "Repository"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        map_file = arcpy.Parameter(
            displayName="Web Map JSON File",
            name="map_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )
        map_file.filter.list = ["json"]

        message = arcpy.Parameter(
            displayName="Commit Message",
            name="message",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        author = arcpy.Parameter(
            displayName="Author",
            name="author",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        author.value = os.environ.get("USERNAME", "arcgis-user")

        return [workspace, map_file, message, author]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        if parameters[1].altered and parameters[1].valueAsText:
            path = Path(parameters[1].valueAsText)
            if path.exists() and path.suffix.lower() != ".json":
                parameters[1].setErrorMessage("File must be a .json web map export.")

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository

        workspace = parameters[0].valueAsText
        map_file = parameters[1].valueAsText
        message = parameters[2].valueAsText
        author = parameters[3].valueAsText or "arcgis-user"

        with open(map_file, "r", encoding="utf-8") as fh:
            map_data = json.load(fh)

        repo = Repository(Path(workspace))
        commit = repo.create_commit(message=message, author=author, map_data=map_data)

        messages.addMessage(f"✓ Committed: {commit.id[:8]}  {message}")
        messages.addMessage(f"  Branch: {repo.get_current_branch()}")
        messages.addMessage(f"  Author: {author}")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: CheckoutBranch
# ---------------------------------------------------------------------------

class CheckoutBranch:
    """Switch to an existing branch and restore its HEAD map state."""

    def __init__(self) -> None:
        self.label = "Checkout Branch"
        self.description = (
            "Switch to an existing branch. Optionally export the restored "
            "map snapshot to a JSON file."
        )
        self.canRunInBackground = False
        self.category = "Branches"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        branch = arcpy.Parameter(
            displayName="Branch Name",
            name="branch",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        export_file = arcpy.Parameter(
            displayName="Export Map JSON (optional)",
            name="export_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output",
        )

        return [workspace, branch, export_file]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository

        workspace = parameters[0].valueAsText
        branch_name = parameters[1].valueAsText
        export_file = parameters[2].valueAsText if parameters[2].altered else None

        repo = Repository(Path(workspace))
        repo.checkout_branch(branch_name)

        messages.addMessage(f"✓ Switched to branch: {branch_name}")

        if export_file:
            commit = repo.get_head_commit()
            if commit and commit.map_data:
                with open(export_file, "w", encoding="utf-8") as fh:
                    json.dump(commit.map_data, fh, indent=2)
                messages.addMessage(f"  Map exported to: {export_file}")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: CreateBranch
# ---------------------------------------------------------------------------

class CreateBranch:
    """Create a new branch from the current HEAD."""

    def __init__(self) -> None:
        self.label = "Create Branch"
        self.description = "Create a new branch from the current HEAD commit."
        self.canRunInBackground = False
        self.category = "Branches"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        branch = arcpy.Parameter(
            displayName="New Branch Name",
            name="branch",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        checkout = arcpy.Parameter(
            displayName="Switch to New Branch",
            name="checkout",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        checkout.value = True

        return [workspace, branch, checkout]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository

        workspace = parameters[0].valueAsText
        branch_name = parameters[1].valueAsText
        do_checkout = parameters[2].value

        repo = Repository(Path(workspace))
        repo.create_branch(branch_name)
        messages.addMessage(f"✓ Created branch: {branch_name}")

        if do_checkout:
            repo.checkout_branch(branch_name)
            messages.addMessage(f"  Switched to: {branch_name}")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: LogHistory
# ---------------------------------------------------------------------------

class LogHistory:
    """Display the commit history for the current branch."""

    def __init__(self) -> None:
        self.label = "Log History"
        self.description = (
            "Display the commit history for the current or specified branch."
        )
        self.canRunInBackground = False
        self.category = "History"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        branch = arcpy.Parameter(
            displayName="Branch (leave blank for current)",
            name="branch",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )

        limit = arcpy.Parameter(
            displayName="Max Commits to Show",
            name="limit",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
        )
        limit.value = 20

        return [workspace, branch, limit]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository

        workspace = parameters[0].valueAsText
        branch_name = parameters[1].valueAsText or None
        limit = int(parameters[2].value or 20)

        repo = Repository(Path(workspace))
        current = repo.get_current_branch()
        target = branch_name or current

        messages.addMessage(f"Branch: {target}")
        messages.addMessage("-" * 60)

        commits = repo.get_commit_history(branch=target, limit=limit)
        for commit in commits:
            short_id = commit.id[:8]
            ts = commit.timestamp[:19].replace("T", " ")
            messages.addMessage(
                f"  {short_id}  {ts}  {commit.author:<16}  {commit.message}"
            )

        if not commits:
            messages.addMessage("  (no commits yet)")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: DiffMaps
# ---------------------------------------------------------------------------

class DiffMaps:
    """Show differences between two commits or branches."""

    def __init__(self) -> None:
        self.label = "Diff Maps"
        self.description = (
            "Compare two commits or branches and display what changed "
            "in the web map (layers added/removed, properties changed)."
        )
        self.canRunInBackground = False
        self.category = "History"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        ref_a = arcpy.Parameter(
            displayName="From (branch or commit hash)",
            name="ref_a",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        ref_b = arcpy.Parameter(
            displayName="To (branch or commit hash)",
            name="ref_b",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        return [workspace, ref_a, ref_b]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository
        from gitmap_core.diff import diff_maps

        workspace = parameters[0].valueAsText
        ref_a = parameters[1].valueAsText
        ref_b = parameters[2].valueAsText

        repo = Repository(Path(workspace))

        commit_a = repo.get_branch_commit(ref_a) if len(ref_a) < 20 else repo.get_commit(ref_a)
        commit_b = repo.get_branch_commit(ref_b) if len(ref_b) < 20 else repo.get_commit(ref_b)

        if not commit_a:
            messages.addErrorMessage(f"Cannot resolve ref: {ref_a}")
            return
        if not commit_b:
            messages.addErrorMessage(f"Cannot resolve ref: {ref_b}")
            return

        diff_result = diff_maps(commit_a.map_data, commit_b.map_data)

        messages.addMessage(f"Diff: {ref_a} → {ref_b}")
        messages.addMessage("-" * 60)

        if not diff_result.has_changes:
            messages.addMessage("  No differences found.")
            return

        for change in diff_result.layer_changes:
            symbol = {"added": "+", "removed": "-", "modified": "~"}.get(change.change_type, "?")
            messages.addMessage(f"  {symbol} [layer] {change.layer_title}")

        for prop, val in diff_result.property_changes.items():
            messages.addMessage(f"  ~ [property] {prop}: {val}")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: StatusCheck
# ---------------------------------------------------------------------------

class StatusCheck:
    """Show current branch, HEAD commit, and repository health."""

    def __init__(self) -> None:
        self.label = "Status"
        self.description = "Show current branch, HEAD commit, and repository info."
        self.canRunInBackground = False
        self.category = "Repository"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        return [workspace]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository

        workspace = parameters[0].valueAsText
        repo = Repository(Path(workspace))

        if not repo.exists():
            messages.addErrorMessage(
                f"No GitMap repository found at {workspace}. "
                "Run 'Init Repository' first."
            )
            return

        current = repo.get_current_branch()
        head = repo.get_head_commit()
        branches = repo.list_branches()

        messages.addMessage(f"Repository: {workspace}")
        messages.addMessage(f"  Current branch : {current}")

        if head:
            messages.addMessage(f"  HEAD commit    : {head.id[:8]}  {head.message}")
            messages.addMessage(f"  Last author    : {head.author}")
            messages.addMessage(f"  Timestamp      : {head.timestamp[:19].replace('T', ' ')}")
        else:
            messages.addMessage("  HEAD commit    : (none — no commits yet)")

        messages.addMessage(f"  Branches ({len(branches)})    : {', '.join(b.name for b in branches)}")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: PushRemote
# ---------------------------------------------------------------------------

class PushRemote:
    """Push the current branch to a configured remote."""

    def __init__(self) -> None:
        self.label = "Push to Remote"
        self.description = (
            "Push the current branch to a GitMap remote server. "
            "Requires a remote to be configured (e.g. via gitmap remote add)."
        )
        self.canRunInBackground = False
        self.category = "Remote"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        remote = arcpy.Parameter(
            displayName="Remote Name",
            name="remote",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        remote.value = "origin"

        return [workspace, remote]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository
        from gitmap_core.remote import RemoteOperations

        workspace = parameters[0].valueAsText
        remote_name = parameters[1].valueAsText or "origin"

        repo = Repository(Path(workspace))
        rm = RemoteOperations(repo)

        branch = repo.get_current_branch()
        messages.addMessage(f"Pushing {branch} → {remote_name}...")

        result = rm.push(remote=remote_name, branch=branch)
        messages.addMessage(f"✓ Push complete: {result}")

    def postExecute(self, parameters):  # noqa: N802
        return


# ---------------------------------------------------------------------------
# Tool: PullRemote
# ---------------------------------------------------------------------------

class PullRemote:
    """Pull updates from a remote into the current branch."""

    def __init__(self) -> None:
        self.label = "Pull from Remote"
        self.description = (
            "Pull updates from a GitMap remote server into the current branch."
        )
        self.canRunInBackground = False
        self.category = "Remote"

    def getParameterInfo(self):  # noqa: N802
        import arcpy

        workspace = arcpy.Parameter(
            displayName="Repository Folder",
            name="workspace",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        remote = arcpy.Parameter(
            displayName="Remote Name",
            name="remote",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        remote.value = "origin"

        return [workspace, remote]

    def isLicensed(self):  # noqa: N802
        return True

    def updateParameters(self, parameters):  # noqa: N802
        return

    def updateMessages(self, parameters):  # noqa: N802
        return

    def execute(self, parameters, messages):  # noqa: N802
        from gitmap_core.repository import Repository
        from gitmap_core.remote import RemoteOperations

        workspace = parameters[0].valueAsText
        remote_name = parameters[1].valueAsText or "origin"

        repo = Repository(Path(workspace))
        rm = RemoteOperations(repo)

        branch = repo.get_current_branch()
        messages.addMessage(f"Pulling {remote_name}/{branch}...")

        result = rm.pull(remote=remote_name, branch=branch)
        messages.addMessage(f"✓ Pull complete: {result}")

    def postExecute(self, parameters):  # noqa: N802
        return
