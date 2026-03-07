"""Tests for GitMap.pyt ArcGIS Pro toolbox.

arcpy is not available outside ArcGIS Pro, so we mock it at the module
level and test the pure-Python logic inside each tool's execute() method.
"""
from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock arcpy so the .pyt can be imported without ArcGIS Pro
# ---------------------------------------------------------------------------

def _make_arcpy_mock():
    """Return a minimal arcpy stub sufficient for toolbox import."""
    arcpy = types.ModuleType("arcpy")

    class Parameter:
        def __init__(self, displayName="", name="", datatype="", parameterType="", direction=""):
            self.displayName = displayName
            self.name = name
            self.datatype = datatype
            self.parameterType = parameterType
            self.direction = direction
            self.value = None
            self.valueAsText = None
            self.altered = False
            self.filter = MagicMock()

        def setErrorMessage(self, msg):
            pass

        def setWarningMessage(self, msg):
            pass

    arcpy.Parameter = Parameter
    return arcpy


arcpy_mock = _make_arcpy_mock()
sys.modules["arcpy"] = arcpy_mock


# ---------------------------------------------------------------------------
# Import the toolbox module
# ---------------------------------------------------------------------------

TOOLBOX_PATH = Path(__file__).parent / "GitMap.pyt"

import importlib.machinery
loader = importlib.machinery.SourceFileLoader("GitMap", str(TOOLBOX_PATH))
spec = importlib.util.spec_from_loader("GitMap", loader)
toolbox_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toolbox_mod)

Toolbox = toolbox_mod.Toolbox
InitRepo = toolbox_mod.InitRepo
CommitMap = toolbox_mod.CommitMap
CheckoutBranch = toolbox_mod.CheckoutBranch
CreateBranch = toolbox_mod.CreateBranch
LogHistory = toolbox_mod.LogHistory
DiffMaps = toolbox_mod.DiffMaps
StatusCheck = toolbox_mod.StatusCheck
PushRemote = toolbox_mod.PushRemote
PullRemote = toolbox_mod.PullRemote


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo_dir(tmp_path):
    """Return a fresh temp directory for repository tests."""
    return tmp_path


@pytest.fixture()
def messages():
    """Return a mock messages object."""
    m = MagicMock()
    return m


def _param(value):
    """Helper: return a minimal Parameter-like stub with a given value."""
    p = MagicMock()
    p.value = value
    p.valueAsText = str(value) if value is not None else None
    p.altered = value is not None
    return p


# ---------------------------------------------------------------------------
# Toolbox metadata tests
# ---------------------------------------------------------------------------

class TestToolboxMeta:
    def test_label(self):
        tb = Toolbox()
        assert tb.label == "GitMap"

    def test_alias(self):
        tb = Toolbox()
        assert tb.alias == "gitmap"

    def test_all_tools_present(self):
        tb = Toolbox()
        tool_classes = {t.__name__ for t in tb.tools}
        expected = {
            "InitRepo", "CommitMap", "CheckoutBranch", "CreateBranch",
            "LogHistory", "DiffMaps", "StatusCheck", "PushRemote", "PullRemote",
        }
        assert expected == tool_classes

    def test_tools_have_labels(self):
        for Tool in Toolbox().tools:
            t = Tool()
            assert t.label, f"{Tool.__name__} missing label"

    def test_tools_have_categories(self):
        for Tool in Toolbox().tools:
            t = Tool()
            assert t.category, f"{Tool.__name__} missing category"


# ---------------------------------------------------------------------------
# InitRepo tests
# ---------------------------------------------------------------------------

class TestInitRepo:
    def test_label(self):
        assert InitRepo().label == "Init Repository"

    def test_execute_inits_repo(self, repo_dir, messages):
        tool = InitRepo()
        mock_repo = MagicMock()
        mock_repo.exists.return_value = False

        params = [_param(str(repo_dir)), _param("A test repo")]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        mock_repo.init.assert_called_once()
        messages.addMessage.assert_called()

    def test_execute_warns_if_already_init(self, repo_dir, messages):
        tool = InitRepo()
        mock_repo = MagicMock()
        mock_repo.exists.return_value = True

        params = [_param(str(repo_dir)), _param("")]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        mock_repo.init.assert_not_called()
        messages.addWarningMessage.assert_called()


# ---------------------------------------------------------------------------
# CommitMap tests
# ---------------------------------------------------------------------------

class TestCommitMap:
    def test_label(self):
        assert CommitMap().label == "Commit Map"

    def test_execute_commits(self, repo_dir, messages):
        map_data = {"operationalLayers": [], "version": "2.0"}
        map_file = repo_dir / "webmap.json"
        map_file.write_text(json.dumps(map_data))

        tool = CommitMap()
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.id = "abc12345def"
        mock_repo.create_commit.return_value = mock_commit
        mock_repo.get_current_branch.return_value = "main"

        params = [
            _param(str(repo_dir)),
            _param(str(map_file)),
            _param("initial commit"),
            _param("test-user"),
        ]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        mock_repo.create_commit.assert_called_once_with(
            message="initial commit", author="test-user", map_data=map_data
        )
        messages.addMessage.assert_called()


# ---------------------------------------------------------------------------
# StatusCheck tests
# ---------------------------------------------------------------------------

class TestStatusCheck:
    def test_label(self):
        assert StatusCheck().label == "Status"

    def test_execute_not_initialized(self, repo_dir, messages):
        tool = StatusCheck()
        mock_repo = MagicMock()
        mock_repo.exists.return_value = False

        params = [_param(str(repo_dir))]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        messages.addErrorMessage.assert_called()

    def test_execute_shows_status(self, repo_dir, messages):
        tool = StatusCheck()
        mock_repo = MagicMock()
        mock_repo.exists.return_value = True
        mock_repo.get_current_branch.return_value = "main"
        mock_commit = MagicMock()
        mock_commit.id = "deadbeef1234"
        mock_commit.message = "test commit"
        mock_commit.author = "tr"
        mock_commit.timestamp = "2026-03-07T01:00:00"
        mock_repo.get_head_commit.return_value = mock_commit
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_repo.list_branches.return_value = [mock_branch]

        params = [_param(str(repo_dir))]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        assert messages.addMessage.call_count >= 4


# ---------------------------------------------------------------------------
# CreateBranch tests
# ---------------------------------------------------------------------------

class TestCreateBranch:
    def test_label(self):
        assert CreateBranch().label == "Create Branch"

    def test_execute_creates_and_checks_out(self, repo_dir, messages):
        tool = CreateBranch()
        mock_repo = MagicMock()

        params = [_param(str(repo_dir)), _param("feature/new-layer"), _param(True)]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        mock_repo.create_branch.assert_called_once_with("feature/new-layer")
        mock_repo.checkout_branch.assert_called_once_with("feature/new-layer")

    def test_execute_no_checkout(self, repo_dir, messages):
        tool = CreateBranch()
        mock_repo = MagicMock()

        params = [_param(str(repo_dir)), _param("feature/new-layer"), _param(False)]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        mock_repo.create_branch.assert_called_once()
        mock_repo.checkout_branch.assert_not_called()


# ---------------------------------------------------------------------------
# CheckoutBranch tests
# ---------------------------------------------------------------------------

class TestCheckoutBranch:
    def test_label(self):
        assert CheckoutBranch().label == "Checkout Branch"

    def test_execute_checkout(self, repo_dir, messages):
        tool = CheckoutBranch()
        mock_repo = MagicMock()

        export_param = _param(None)
        export_param.altered = False

        params = [_param(str(repo_dir)), _param("feature/floods"), export_param]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        mock_repo.checkout_branch.assert_called_once_with("feature/floods")

    def test_execute_with_export(self, repo_dir, messages):
        tool = CheckoutBranch()
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.map_data = {"version": "2.0", "operationalLayers": []}
        mock_repo.get_head_commit.return_value = mock_commit

        export_file = repo_dir / "exported.json"
        export_param = _param(str(export_file))
        export_param.altered = True

        params = [_param(str(repo_dir)), _param("main"), export_param]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        assert export_file.exists()
        data = json.loads(export_file.read_text())
        assert data["version"] == "2.0"


# ---------------------------------------------------------------------------
# LogHistory tests
# ---------------------------------------------------------------------------

class TestLogHistory:
    def test_label(self):
        assert LogHistory().label == "Log History"

    def test_execute_no_commits(self, repo_dir, messages):
        tool = LogHistory()
        mock_repo = MagicMock()
        mock_repo.get_current_branch.return_value = "main"
        mock_repo.get_commit_history.return_value = []

        params = [_param(str(repo_dir)), _param(None), _param(10)]
        params[1].valueAsText = None

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        # Should still output something (no commits message)
        messages.addMessage.assert_called()

    def test_execute_with_commits(self, repo_dir, messages):
        tool = LogHistory()
        mock_repo = MagicMock()
        mock_repo.get_current_branch.return_value = "main"

        mock_commit = MagicMock()
        mock_commit.id = "aabbccdd1122"
        mock_commit.timestamp = "2026-03-07T01:00:00"
        mock_commit.author = "tr"
        mock_commit.message = "add flood layer"
        mock_repo.get_commit_history.return_value = [mock_commit]

        params = [_param(str(repo_dir)), _param(None), _param(10)]
        params[1].valueAsText = None

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        call_args = [str(c) for c in messages.addMessage.call_args_list]
        assert any("add flood layer" in a for a in call_args)


# ---------------------------------------------------------------------------
# DiffMaps tests
# ---------------------------------------------------------------------------

class TestDiffMaps:
    def test_label(self):
        assert DiffMaps().label == "Diff Maps"

    def test_execute_no_diff(self, repo_dir, messages):
        tool = DiffMaps()
        mock_repo = MagicMock()
        mock_commit_a = MagicMock()
        mock_commit_a.map_data = {"layers": []}
        mock_commit_b = MagicMock()
        mock_commit_b.map_data = {"layers": []}
        mock_repo.get_branch_commit.side_effect = [mock_commit_a, mock_commit_b]

        mock_diff = MagicMock()
        mock_diff.has_changes = False
        mock_diff.layer_changes = []
        mock_diff.property_changes = {}

        params = [_param(str(repo_dir)), _param("main"), _param("feature/x")]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo), \
             patch("gitmap_core.diff.diff_maps", return_value=mock_diff):
            tool.execute(params, messages)

        call_args = [str(c) for c in messages.addMessage.call_args_list]
        assert any("No differences" in a for a in call_args)

    def test_execute_missing_ref(self, repo_dir, messages):
        tool = DiffMaps()
        mock_repo = MagicMock()
        mock_repo.get_branch_commit.return_value = None

        params = [_param(str(repo_dir)), _param("bad-ref"), _param("main")]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo):
            tool.execute(params, messages)

        messages.addErrorMessage.assert_called()


# ---------------------------------------------------------------------------
# Remote tools (light-touch — just verify they call push/pull)
# ---------------------------------------------------------------------------

class TestPushRemote:
    def test_label(self):
        assert PushRemote().label == "Push to Remote"

    def test_execute_calls_push(self, repo_dir, messages):
        tool = PushRemote()
        mock_repo = MagicMock()
        mock_repo.get_current_branch.return_value = "main"
        mock_rm = MagicMock()
        mock_rm.push.return_value = "ok"

        params = [_param(str(repo_dir)), _param("origin")]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo), \
             patch("gitmap_core.remote.RemoteOperations", return_value=mock_rm):
            tool.execute(params, messages)

        mock_rm.push.assert_called_once_with(remote="origin", branch="main")


class TestPullRemote:
    def test_label(self):
        assert PullRemote().label == "Pull from Remote"

    def test_execute_calls_pull(self, repo_dir, messages):
        tool = PullRemote()
        mock_repo = MagicMock()
        mock_repo.get_current_branch.return_value = "main"
        mock_rm = MagicMock()
        mock_rm.pull.return_value = "ok"

        params = [_param(str(repo_dir)), _param("origin")]

        with patch("gitmap_core.repository.Repository", return_value=mock_repo), \
             patch("gitmap_core.remote.RemoteOperations", return_value=mock_rm):
            tool.execute(params, messages)

        mock_rm.pull.assert_called_once_with(remote="origin", branch="main")
