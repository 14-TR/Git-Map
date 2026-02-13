"""Tests for gitmap_core.merge module.

Tests the layer-level merge logic for GitMap including:
- Basic merging without conflicts
- Three-way merge with conflict detection
- Conflict resolution
- Table merging
- Summary formatting
"""
from __future__ import annotations

import pytest

from gitmap_core.merge import (
    apply_resolution,
    format_merge_summary,
    merge_maps,
    MergeConflict,
    MergeResult,
    resolve_conflict,
)


# ---- Fixtures -----------------------------------------------------------------------------------------------


@pytest.fixture
def base_map() -> dict:
    """Base map state for three-way merges."""
    return {
        "operationalLayers": [
            {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
            {"id": "layer2", "title": "Layer Two", "url": "http://example.com/2"},
        ],
        "tables": [
            {"id": "table1", "title": "Table One", "url": "http://example.com/t1"},
        ],
    }


@pytest.fixture
def our_map() -> dict:
    """Our modified map state."""
    return {
        "operationalLayers": [
            {"id": "layer1", "title": "Layer One Modified", "url": "http://example.com/1"},
            {"id": "layer2", "title": "Layer Two", "url": "http://example.com/2"},
            {"id": "layer3", "title": "Layer Three (New)", "url": "http://example.com/3"},
        ],
        "tables": [
            {"id": "table1", "title": "Table One", "url": "http://example.com/t1"},
        ],
    }


@pytest.fixture
def their_map() -> dict:
    """Their modified map state."""
    return {
        "operationalLayers": [
            {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
            {"id": "layer2", "title": "Layer Two Updated", "url": "http://example.com/2-new"},
            {"id": "layer4", "title": "Layer Four (New)", "url": "http://example.com/4"},
        ],
        "tables": [
            {"id": "table1", "title": "Table One Updated", "url": "http://example.com/t1-new"},
        ],
    }


# ---- MergeConflict Tests ------------------------------------------------------------------------------------


class TestMergeConflict:
    """Tests for MergeConflict dataclass."""

    def test_create_conflict(self):
        """Test basic conflict creation."""
        conflict = MergeConflict(
            layer_id="layer1",
            layer_title="Test Layer",
            ours={"id": "layer1", "title": "Ours"},
            theirs={"id": "layer1", "title": "Theirs"},
        )
        assert conflict.layer_id == "layer1"
        assert conflict.layer_title == "Test Layer"
        assert conflict.ours == {"id": "layer1", "title": "Ours"}
        assert conflict.theirs == {"id": "layer1", "title": "Theirs"}
        assert conflict.base is None

    def test_conflict_with_base(self):
        """Test conflict with base version."""
        conflict = MergeConflict(
            layer_id="layer1",
            layer_title="Test Layer",
            ours={"id": "layer1", "title": "Ours"},
            theirs={"id": "layer1", "title": "Theirs"},
            base={"id": "layer1", "title": "Base"},
        )
        assert conflict.base == {"id": "layer1", "title": "Base"}


# ---- MergeResult Tests --------------------------------------------------------------------------------------


class TestMergeResult:
    """Tests for MergeResult dataclass."""

    def test_default_result(self):
        """Test default merge result values."""
        result = MergeResult()
        assert result.success is True
        assert result.merged_data == {}
        assert result.conflicts == []
        assert result.added_layers == []
        assert result.removed_layers == []
        assert result.modified_layers == []

    def test_has_conflicts_false(self):
        """Test has_conflicts property when no conflicts."""
        result = MergeResult()
        assert result.has_conflicts is False

    def test_has_conflicts_true(self):
        """Test has_conflicts property when conflicts exist."""
        result = MergeResult()
        result.conflicts.append(MergeConflict(
            layer_id="layer1",
            layer_title="Test",
            ours={},
            theirs={},
        ))
        assert result.has_conflicts is True


# ---- merge_maps Tests ---------------------------------------------------------------------------------------


class TestMergeMaps:
    """Tests for merge_maps function."""

    def test_merge_identical_maps(self):
        """Test merging identical maps produces no conflicts."""
        map_data = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One"},
            ],
            "tables": [],
        }
        result = merge_maps(map_data, map_data)
        assert result.success is True
        assert result.has_conflicts is False
        assert len(result.merged_data["operationalLayers"]) == 1

    def test_merge_empty_maps(self):
        """Test merging empty maps."""
        result = merge_maps({}, {})
        assert result.success is True
        assert result.merged_data.get("operationalLayers", []) == []
        assert result.merged_data.get("tables", []) == []

    def test_merge_adds_their_new_layer(self):
        """Test merging adds layers only in theirs."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One"},
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One"},
                {"id": "layer2", "title": "Layer Two"},
            ],
        }
        result = merge_maps(ours, theirs)
        assert result.success is True
        assert len(result.merged_data["operationalLayers"]) == 2
        assert "layer2" in result.added_layers

    def test_merge_keeps_our_new_layer(self):
        """Test merging keeps layers only in ours."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One"},
                {"id": "layer2", "title": "Layer Two"},
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One"},
            ],
        }
        result = merge_maps(ours, theirs)
        assert result.success is True
        assert len(result.merged_data["operationalLayers"]) == 2

    def test_three_way_merge_theirs_modified(self, base_map, our_map, their_map):
        """Test three-way merge when they modified a layer we didn't."""
        # Revert our modification to layer1 to test "theirs wins"
        our_map["operationalLayers"][0]["title"] = "Layer One"  # Same as base

        result = merge_maps(our_map, their_map, base_map)

        # Layer2 should use their version since we didn't change it
        layer2 = next(
            (l for l in result.merged_data["operationalLayers"] if l["id"] == "layer2"),
            None
        )
        assert layer2 is not None
        assert layer2["title"] == "Layer Two Updated"
        assert "layer2" in result.modified_layers

    def test_three_way_merge_ours_modified(self, base_map):
        """Test three-way merge when we modified a layer they didn't."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One Modified", "url": "http://example.com/1"},
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
            ],
        }
        base = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
            ],
        }

        result = merge_maps(ours, theirs, base)

        # Our modification should be kept
        layer1 = result.merged_data["operationalLayers"][0]
        assert layer1["title"] == "Layer One Modified"
        assert result.success is True

    def test_three_way_merge_both_modified_conflict(self, base_map):
        """Test three-way merge creates conflict when both modify same layer."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One - Ours", "url": "http://example.com/1"},
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One - Theirs", "url": "http://example.com/1"},
            ],
        }
        base = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
            ],
        }

        result = merge_maps(ours, theirs, base)

        assert result.success is False
        assert result.has_conflicts is True
        assert len(result.conflicts) == 1
        assert result.conflicts[0].layer_id == "layer1"

    def test_merge_conflict_without_base(self):
        """Test conflict when same layer differs without base."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One - Ours"},
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One - Theirs"},
            ],
        }

        result = merge_maps(ours, theirs)

        assert result.success is False
        assert len(result.conflicts) == 1

    def test_merge_they_deleted_we_kept(self, base_map):
        """Test merging when they deleted a layer we kept."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
                {"id": "layer2", "title": "Layer Two", "url": "http://example.com/2"},
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
                # layer2 deleted
            ],
        }

        result = merge_maps(ours, theirs, base_map)

        # We kept layer2, it should be in merged result
        layer_ids = [l["id"] for l in result.merged_data["operationalLayers"]]
        assert "layer2" in layer_ids

    def test_merge_we_deleted_they_modified_conflict(self, base_map):
        """Test conflict when we deleted and they modified."""
        ours = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
                # layer2 deleted
            ],
        }
        theirs = {
            "operationalLayers": [
                {"id": "layer1", "title": "Layer One", "url": "http://example.com/1"},
                {"id": "layer2", "title": "Layer Two Modified", "url": "http://example.com/2-new"},
            ],
        }

        result = merge_maps(ours, theirs, base_map)

        # Conflict: we deleted, they modified
        assert result.has_conflicts is True
        conflict = result.conflicts[0]
        assert conflict.layer_id == "layer2"
        assert conflict.ours == {}  # We deleted

    def test_merge_tables_conflict(self, base_map):
        """Test table merge creates conflicts correctly."""
        ours = {
            "operationalLayers": [],
            "tables": [
                {"id": "table1", "title": "Table One - Ours", "url": "http://example.com/t1"},
            ],
        }
        theirs = {
            "operationalLayers": [],
            "tables": [
                {"id": "table1", "title": "Table One - Theirs", "url": "http://example.com/t1"},
            ],
        }

        result = merge_maps(ours, theirs, base_map)

        assert result.has_conflicts is True
        conflict = result.conflicts[0]
        assert conflict.layer_id == "table1"

    def test_merge_adds_their_new_table(self):
        """Test merging adds tables only in theirs."""
        ours = {
            "operationalLayers": [],
            "tables": [],
        }
        theirs = {
            "operationalLayers": [],
            "tables": [
                {"id": "table1", "title": "New Table"},
            ],
        }

        result = merge_maps(ours, theirs)

        assert len(result.merged_data["tables"]) == 1
        assert "table1" in result.added_layers

    def test_merge_tables_conflict_two_way(self):
        """Test two-way table merge (no base) creates conflict when both differ."""
        ours = {
            "operationalLayers": [],
            "tables": [
                {"id": "table1", "title": "Table One - Ours", "url": "http://example.com/t1-ours"},
            ],
        }
        theirs = {
            "operationalLayers": [],
            "tables": [
                {"id": "table1", "title": "Table One - Theirs", "url": "http://example.com/t1-theirs"},
            ],
        }

        # Two-way merge: no base argument
        result = merge_maps(ours, theirs)

        assert result.has_conflicts is True
        assert len(result.conflicts) == 1
        conflict = result.conflicts[0]
        assert conflict.layer_id == "table1"
        assert conflict.layer_title == "Table One - Ours"
        assert conflict.ours == ours["tables"][0]
        assert conflict.theirs == theirs["tables"][0]
        assert conflict.base is None  # No base in two-way merge

    def test_merge_they_modified_table_we_deleted(self, base_map):
        """Test conflict when they modify a table we deleted."""
        # We deleted table1 (not in our map)
        ours = {
            "operationalLayers": base_map["operationalLayers"],
            "tables": [],  # We deleted table1
        }
        # They modified table1
        theirs = {
            "operationalLayers": base_map["operationalLayers"],
            "tables": [
                {"id": "table1", "title": "Table One Modified By Them", "url": "http://example.com/t1-modified"},
            ],
        }

        result = merge_maps(ours, theirs, base_map)

        # Should create a conflict: they modified, we deleted
        assert result.has_conflicts is True
        conflict = next((c for c in result.conflicts if c.layer_id == "table1"), None)
        assert conflict is not None
        assert conflict.ours == {}  # We deleted it
        assert conflict.theirs["title"] == "Table One Modified By Them"
        assert conflict.base == base_map["tables"][0]

    def test_merge_they_kept_table_we_deleted_unchanged(self, base_map):
        """Test that when they don't change a table we deleted, we respect our deletion."""
        # We deleted table1
        ours = {
            "operationalLayers": base_map["operationalLayers"],
            "tables": [],
        }
        # They didn't modify table1 (same as base)
        theirs = {
            "operationalLayers": base_map["operationalLayers"],
            "tables": base_map["tables"].copy(),  # Same as base
        }

        result = merge_maps(ours, theirs, base_map)

        # No conflict - we deleted, they didn't change, so deletion is respected
        table_conflicts = [c for c in result.conflicts if c.layer_id == "table1"]
        assert len(table_conflicts) == 0
        # Table should not be in merged result
        merged_table_ids = [t["id"] for t in result.merged_data.get("tables", [])]
        assert "table1" not in merged_table_ids

    def test_merge_preserves_non_layer_properties(self):
        """Test that merge preserves map properties outside layers."""
        ours = {
            "mapTitle": "My Map",
            "basemap": "topo",
            "operationalLayers": [],
        }
        theirs = {
            "mapTitle": "Their Map",
            "basemap": "satellite",
            "operationalLayers": [],
        }

        result = merge_maps(ours, theirs)

        # Should keep ours since we start with our map
        assert result.merged_data["mapTitle"] == "My Map"
        assert result.merged_data["basemap"] == "topo"


# ---- resolve_conflict Tests ---------------------------------------------------------------------------------


class TestResolveConflict:
    """Tests for resolve_conflict function."""

    @pytest.fixture
    def conflict(self):
        """Create a test conflict."""
        return MergeConflict(
            layer_id="layer1",
            layer_title="Test Layer",
            ours={"id": "layer1", "title": "Ours"},
            theirs={"id": "layer1", "title": "Theirs"},
            base={"id": "layer1", "title": "Base"},
        )

    def test_resolve_ours(self, conflict):
        """Test resolving conflict with 'ours'."""
        result = resolve_conflict(conflict, "ours")
        assert result == {"id": "layer1", "title": "Ours"}

    def test_resolve_theirs(self, conflict):
        """Test resolving conflict with 'theirs'."""
        result = resolve_conflict(conflict, "theirs")
        assert result == {"id": "layer1", "title": "Theirs"}

    def test_resolve_base(self, conflict):
        """Test resolving conflict with 'base'."""
        result = resolve_conflict(conflict, "base")
        assert result == {"id": "layer1", "title": "Base"}

    def test_resolve_base_not_available(self):
        """Test error when resolving with base but no base exists."""
        conflict = MergeConflict(
            layer_id="layer1",
            layer_title="Test",
            ours={},
            theirs={},
            base=None,
        )
        with pytest.raises(ValueError, match="No base version available"):
            resolve_conflict(conflict, "base")

    def test_resolve_invalid_strategy(self, conflict):
        """Test error with invalid resolution strategy."""
        with pytest.raises(ValueError, match="Invalid resolution strategy"):
            resolve_conflict(conflict, "invalid")


# ---- apply_resolution Tests ---------------------------------------------------------------------------------


class TestApplyResolution:
    """Tests for apply_resolution function."""

    def test_apply_layer_resolution(self):
        """Test applying resolution to a layer conflict."""
        merge_result = MergeResult(
            merged_data={
                "operationalLayers": [
                    {"id": "layer1", "title": "Old"},
                ],
                "tables": [],
            },
            conflicts=[
                MergeConflict(
                    layer_id="layer1",
                    layer_title="Test",
                    ours={"id": "layer1", "title": "Old"},
                    theirs={"id": "layer1", "title": "New"},
                ),
            ],
        )

        result = apply_resolution(
            merge_result,
            "layer1",
            {"id": "layer1", "title": "Resolved"},
        )

        assert len(result.conflicts) == 0
        assert result.success is True
        assert result.merged_data["operationalLayers"][0]["title"] == "Resolved"

    def test_apply_table_resolution(self):
        """Test applying resolution to a table conflict."""
        merge_result = MergeResult(
            merged_data={
                "operationalLayers": [],
                "tables": [
                    {"id": "table1", "title": "Old"},
                ],
            },
            conflicts=[
                MergeConflict(
                    layer_id="table1",
                    layer_title="Test",
                    ours={},
                    theirs={},
                ),
            ],
        )

        result = apply_resolution(
            merge_result,
            "table1",
            {"id": "table1", "title": "Resolved"},
        )

        assert len(result.conflicts) == 0
        assert result.merged_data["tables"][0]["title"] == "Resolved"

    def test_apply_resolution_deletes_layer(self):
        """Test that empty resolution deletes the layer."""
        merge_result = MergeResult(
            merged_data={
                "operationalLayers": [
                    {"id": "layer1", "title": "To Delete"},
                ],
                "tables": [],
            },
            conflicts=[
                MergeConflict(
                    layer_id="layer1",
                    layer_title="Test",
                    ours={},
                    theirs={},
                ),
            ],
        )

        result = apply_resolution(merge_result, "layer1", {})

        assert len(result.merged_data["operationalLayers"]) == 0

    def test_apply_resolution_adds_missing_layer(self):
        """Test adding a layer that wasn't in merged data."""
        merge_result = MergeResult(
            merged_data={
                "operationalLayers": [],
                "tables": [],
            },
            conflicts=[
                MergeConflict(
                    layer_id="layer1",
                    layer_title="Test",
                    ours={},
                    theirs={"id": "layer1", "title": "New"},
                ),
            ],
        )

        result = apply_resolution(
            merge_result,
            "layer1",
            {"id": "layer1", "title": "New"},
        )

        assert len(result.merged_data["operationalLayers"]) == 1
        assert result.merged_data["operationalLayers"][0]["title"] == "New"


# ---- format_merge_summary Tests -----------------------------------------------------------------------------


class TestFormatMergeSummary:
    """Tests for format_merge_summary function."""

    def test_format_successful_merge(self):
        """Test formatting a successful merge."""
        result = MergeResult(success=True)
        summary = format_merge_summary(result)
        assert "Merge completed successfully" in summary

    def test_format_merge_with_conflicts(self):
        """Test formatting a merge with conflicts."""
        result = MergeResult(
            success=False,
            conflicts=[
                MergeConflict(
                    layer_id="layer1",
                    layer_title="Problem Layer",
                    ours={},
                    theirs={},
                ),
            ],
        )
        summary = format_merge_summary(result)
        assert "1 conflict" in summary
        assert "Problem Layer" in summary
        assert "layer1" in summary

    def test_format_with_added_layers(self):
        """Test formatting shows added layers."""
        result = MergeResult(
            success=True,
            added_layers=["layer1", "layer2"],
        )
        summary = format_merge_summary(result)
        assert "Added layers: 2" in summary
        assert "+ layer1" in summary
        assert "+ layer2" in summary

    def test_format_with_removed_layers(self):
        """Test formatting shows removed layers."""
        result = MergeResult(
            success=True,
            removed_layers=["layer1"],
        )
        summary = format_merge_summary(result)
        assert "Removed layers: 1" in summary
        assert "- layer1" in summary

    def test_format_with_modified_layers(self):
        """Test formatting shows modified layers."""
        result = MergeResult(
            success=True,
            modified_layers=["layer1"],
        )
        summary = format_merge_summary(result)
        assert "Modified layers: 1" in summary
        assert "~ layer1" in summary

    def test_format_with_tables(self):
        """Test formatting shows merged tables count."""
        result = MergeResult(
            success=True,
            merged_data={
                "tables": [
                    {"id": "table1"},
                    {"id": "table2"},
                ],
            },
        )
        summary = format_merge_summary(result)
        assert "Merged tables: 2" in summary
