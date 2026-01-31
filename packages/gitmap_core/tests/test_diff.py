"""Tests for JSON diffing and comparison module.

Tests layer comparison, map diffing, and diff formatting.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - gitmap_core.diff: Module under test
"""
from __future__ import annotations

import pytest

from gitmap_core.diff import (
    LayerChange,
    MapDiff,
    diff_json,
    diff_layers,
    diff_maps,
    format_diff_summary,
)


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def sample_layer_1() -> dict:
    """Create first sample layer."""
    return {
        "id": "layer-001",
        "title": "Roads",
        "url": "https://example.com/roads",
        "opacity": 1.0,
        "visible": True,
    }


@pytest.fixture
def sample_layer_2() -> dict:
    """Create second sample layer."""
    return {
        "id": "layer-002",
        "title": "Buildings",
        "url": "https://example.com/buildings",
        "opacity": 0.8,
        "visible": True,
    }


@pytest.fixture
def sample_layer_3() -> dict:
    """Create third sample layer."""
    return {
        "id": "layer-003",
        "title": "Parks",
        "url": "https://example.com/parks",
        "opacity": 0.9,
        "visible": False,
    }


@pytest.fixture
def sample_map(sample_layer_1: dict, sample_layer_2: dict) -> dict:
    """Create a sample web map."""
    return {
        "operationalLayers": [sample_layer_1, sample_layer_2],
        "tables": [],
        "baseMap": {"title": "Topographic"},
        "version": "2.29",
        "authoringApp": "GitMap",
    }


# ---- LayerChange Tests ---------------------------------------------------------------------------------------


class TestLayerChange:
    """Tests for LayerChange dataclass."""

    def test_create_added_layer(self) -> None:
        """Test creating an added layer change."""
        change = LayerChange(
            layer_id="layer-001",
            layer_title="Test Layer",
            change_type="added",
        )

        assert change.layer_id == "layer-001"
        assert change.layer_title == "Test Layer"
        assert change.change_type == "added"
        assert change.details == {}

    def test_create_modified_layer_with_details(self) -> None:
        """Test creating a modified layer change with details."""
        details = {"values_changed": {"root['opacity']": {"new_value": 0.5, "old_value": 1.0}}}
        change = LayerChange(
            layer_id="layer-002",
            layer_title="Updated Layer",
            change_type="modified",
            details=details,
        )

        assert change.change_type == "modified"
        assert "values_changed" in change.details

    def test_create_removed_layer(self) -> None:
        """Test creating a removed layer change."""
        change = LayerChange(
            layer_id="layer-003",
            layer_title="Deleted Layer",
            change_type="removed",
        )

        assert change.change_type == "removed"


# ---- MapDiff Tests -------------------------------------------------------------------------------------------


class TestMapDiff:
    """Tests for MapDiff dataclass."""

    def test_empty_diff_has_no_changes(self) -> None:
        """Test that empty MapDiff reports no changes."""
        diff = MapDiff()

        assert not diff.has_changes
        assert diff.layer_changes == []
        assert diff.table_changes == []
        assert diff.property_changes == {}

    def test_has_changes_with_layer_changes(self) -> None:
        """Test has_changes with layer changes."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Layer 1", "added"),
            ]
        )

        assert diff.has_changes

    def test_has_changes_with_table_changes(self) -> None:
        """Test has_changes with table changes."""
        diff = MapDiff(
            table_changes=[
                LayerChange("t1", "Table 1", "removed"),
            ]
        )

        assert diff.has_changes

    def test_has_changes_with_property_changes(self) -> None:
        """Test has_changes with property changes."""
        diff = MapDiff(property_changes={"values_changed": {"root['version']": {}}})

        assert diff.has_changes

    def test_added_layers_filter(self) -> None:
        """Test added_layers property filters correctly."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Layer 1", "added"),
                LayerChange("l2", "Layer 2", "removed"),
                LayerChange("l3", "Layer 3", "added"),
            ]
        )

        added = diff.added_layers
        assert len(added) == 2
        assert all(c.change_type == "added" for c in added)

    def test_removed_layers_filter(self) -> None:
        """Test removed_layers property filters correctly."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Layer 1", "added"),
                LayerChange("l2", "Layer 2", "removed"),
                LayerChange("l3", "Layer 3", "removed"),
            ]
        )

        removed = diff.removed_layers
        assert len(removed) == 2
        assert all(c.change_type == "removed" for c in removed)

    def test_modified_layers_filter(self) -> None:
        """Test modified_layers property filters correctly."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Layer 1", "modified"),
                LayerChange("l2", "Layer 2", "added"),
            ]
        )

        modified = diff.modified_layers
        assert len(modified) == 1
        assert modified[0].layer_id == "l1"

    def test_table_change_filters(self) -> None:
        """Test table change filter properties."""
        diff = MapDiff(
            table_changes=[
                LayerChange("t1", "Table 1", "added"),
                LayerChange("t2", "Table 2", "removed"),
                LayerChange("t3", "Table 3", "modified"),
            ]
        )

        assert len(diff.added_tables) == 1
        assert len(diff.removed_tables) == 1
        assert len(diff.modified_tables) == 1


# ---- diff_layers Tests ---------------------------------------------------------------------------------------


class TestDiffLayers:
    """Tests for diff_layers function."""

    def test_empty_layers_no_changes(self) -> None:
        """Test comparing empty layer lists."""
        changes = diff_layers([], [])

        assert changes == []

    def test_identical_layers_no_changes(self, sample_layer_1: dict) -> None:
        """Test comparing identical layers."""
        changes = diff_layers([sample_layer_1], [sample_layer_1.copy()])

        assert changes == []

    def test_detect_added_layer(self, sample_layer_1: dict, sample_layer_2: dict) -> None:
        """Test detecting an added layer."""
        layers1 = [sample_layer_1, sample_layer_2]
        layers2 = [sample_layer_1]

        changes = diff_layers(layers1, layers2)

        added = [c for c in changes if c.change_type == "added"]
        assert len(added) == 1
        assert added[0].layer_id == "layer-002"
        assert added[0].layer_title == "Buildings"

    def test_detect_removed_layer(self, sample_layer_1: dict, sample_layer_2: dict) -> None:
        """Test detecting a removed layer."""
        layers1 = [sample_layer_1]
        layers2 = [sample_layer_1, sample_layer_2]

        changes = diff_layers(layers1, layers2)

        removed = [c for c in changes if c.change_type == "removed"]
        assert len(removed) == 1
        assert removed[0].layer_id == "layer-002"

    def test_detect_modified_layer(self, sample_layer_1: dict) -> None:
        """Test detecting a modified layer."""
        layer1_modified = sample_layer_1.copy()
        layer1_modified["opacity"] = 0.5
        layer1_modified["visible"] = False

        changes = diff_layers([layer1_modified], [sample_layer_1])

        modified = [c for c in changes if c.change_type == "modified"]
        assert len(modified) == 1
        assert modified[0].layer_id == "layer-001"
        assert "values_changed" in modified[0].details

    def test_detect_multiple_changes(
        self, sample_layer_1: dict, sample_layer_2: dict, sample_layer_3: dict
    ) -> None:
        """Test detecting multiple types of changes."""
        # layers1: layer1 (modified), layer3 (added)
        # layers2: layer1 (original), layer2 (will be removed)
        layer1_modified = sample_layer_1.copy()
        layer1_modified["opacity"] = 0.5

        layers1 = [layer1_modified, sample_layer_3]
        layers2 = [sample_layer_1, sample_layer_2]

        changes = diff_layers(layers1, layers2)

        added = [c for c in changes if c.change_type == "added"]
        removed = [c for c in changes if c.change_type == "removed"]
        modified = [c for c in changes if c.change_type == "modified"]

        assert len(added) == 1
        assert len(removed) == 1
        assert len(modified) == 1

    def test_layer_without_id_ignored(self) -> None:
        """Test that layers without IDs are ignored."""
        layer_no_id = {"title": "No ID Layer", "url": "https://example.com"}
        layer_with_id = {"id": "layer-001", "title": "Has ID"}

        changes = diff_layers([layer_no_id, layer_with_id], [layer_with_id])

        # Should only see the layer_with_id, layer_no_id is ignored
        assert len(changes) == 0

    def test_untitled_layer_uses_default(self) -> None:
        """Test that layers without title use 'Untitled'."""
        layer = {"id": "layer-001"}

        changes = diff_layers([layer], [])

        assert changes[0].layer_title == "Untitled"


# ---- diff_maps Tests -----------------------------------------------------------------------------------------


class TestDiffMaps:
    """Tests for diff_maps function."""

    def test_identical_maps_no_changes(self, sample_map: dict) -> None:
        """Test comparing identical maps."""
        import copy
        map2 = copy.deepcopy(sample_map)

        diff = diff_maps(sample_map, map2)

        assert not diff.has_changes

    def test_detect_layer_addition(self, sample_map: dict, sample_layer_3: dict) -> None:
        """Test detecting layer addition in maps."""
        import copy
        map2 = copy.deepcopy(sample_map)
        sample_map["operationalLayers"].append(sample_layer_3)

        diff = diff_maps(sample_map, map2)

        assert len(diff.added_layers) == 1
        assert diff.added_layers[0].layer_id == "layer-003"

    def test_detect_layer_removal(self, sample_map: dict) -> None:
        """Test detecting layer removal in maps."""
        import copy
        map2 = copy.deepcopy(sample_map)
        # Remove first layer from map1
        removed_layer = sample_map["operationalLayers"].pop(0)

        diff = diff_maps(sample_map, map2)

        assert len(diff.removed_layers) == 1
        assert diff.removed_layers[0].layer_id == removed_layer["id"]

    def test_detect_table_changes(self) -> None:
        """Test detecting table changes."""
        map1 = {
            "operationalLayers": [],
            "tables": [{"id": "table-001", "title": "Data Table"}],
        }
        map2 = {
            "operationalLayers": [],
            "tables": [],
        }

        diff = diff_maps(map1, map2)

        assert len(diff.added_tables) == 1
        assert diff.added_tables[0].layer_id == "table-001"

    def test_detect_property_changes(self, sample_map: dict) -> None:
        """Test detecting map property changes."""
        import copy
        map2 = copy.deepcopy(sample_map)
        sample_map["version"] = "2.30"
        sample_map["authoringApp"] = "GitMap Pro"

        diff = diff_maps(sample_map, map2)

        assert diff.property_changes
        assert "values_changed" in diff.property_changes

    def test_ignores_layer_and_table_keys_in_properties(self, sample_map: dict) -> None:
        """Test that operationalLayers and tables are not in property_changes."""
        import copy
        map2 = copy.deepcopy(sample_map)
        # Only change layers, not properties
        sample_map["operationalLayers"].append({"id": "new", "title": "New"})

        diff = diff_maps(sample_map, map2)

        # Should have layer change but no property changes
        assert diff.has_changes
        assert not diff.property_changes
        assert len(diff.added_layers) == 1

    def test_handles_missing_keys(self) -> None:
        """Test handling maps with missing keys."""
        map1 = {"version": "1.0"}
        map2 = {"version": "1.0", "authoringApp": "Test"}

        diff = diff_maps(map1, map2)

        # Should detect the removed key
        assert diff.property_changes


# ---- diff_json Tests -----------------------------------------------------------------------------------------


class TestDiffJson:
    """Tests for diff_json function."""

    def test_identical_objects_no_diff(self) -> None:
        """Test that identical objects have no diff."""
        obj = {"key": "value", "number": 42}

        result = diff_json(obj, obj.copy())

        assert result == {}

    def test_detect_value_change(self) -> None:
        """Test detecting value changes."""
        obj1 = {"key": "new_value"}
        obj2 = {"key": "old_value"}

        result = diff_json(obj1, obj2)

        assert "values_changed" in result

    def test_detect_added_key(self) -> None:
        """Test detecting added keys."""
        obj1 = {"key1": "value1", "key2": "value2"}
        obj2 = {"key1": "value1"}

        result = diff_json(obj1, obj2)

        assert "dictionary_item_added" in result

    def test_detect_removed_key(self) -> None:
        """Test detecting removed keys."""
        obj1 = {"key1": "value1"}
        obj2 = {"key1": "value1", "key2": "value2"}

        result = diff_json(obj1, obj2)

        assert "dictionary_item_removed" in result

    def test_ignore_order_by_default(self) -> None:
        """Test that list order is ignored by default."""
        obj1 = {"items": [1, 2, 3]}
        obj2 = {"items": [3, 2, 1]}

        result = diff_json(obj1, obj2)

        assert result == {}

    def test_respect_order_when_requested(self) -> None:
        """Test that list order can be respected."""
        obj1 = {"items": [1, 2, 3]}
        obj2 = {"items": [3, 2, 1]}

        result = diff_json(obj1, obj2, ignore_order=False)

        assert result != {}


# ---- format_diff_summary Tests -------------------------------------------------------------------------------


class TestFormatDiffSummary:
    """Tests for format_diff_summary function."""

    def test_no_changes_message(self) -> None:
        """Test message for no changes."""
        diff = MapDiff()

        result = format_diff_summary(diff)

        assert result == "No changes detected."

    def test_format_added_layers(self) -> None:
        """Test formatting added layers."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Roads", "added"),
                LayerChange("l2", "Buildings", "added"),
            ]
        )

        result = format_diff_summary(diff)

        assert "Added layers (2):" in result
        assert "+ Roads (l1)" in result
        assert "+ Buildings (l2)" in result

    def test_format_removed_layers(self) -> None:
        """Test formatting removed layers."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Old Layer", "removed"),
            ]
        )

        result = format_diff_summary(diff)

        assert "Removed layers (1):" in result
        assert "- Old Layer (l1)" in result

    def test_format_modified_layers(self) -> None:
        """Test formatting modified layers."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "Updated Layer", "modified"),
            ]
        )

        result = format_diff_summary(diff)

        assert "Modified layers (1):" in result
        assert "~ Updated Layer (l1)" in result

    def test_format_table_changes(self) -> None:
        """Test formatting table changes."""
        diff = MapDiff(
            table_changes=[
                LayerChange("t1", "Data Table", "added"),
                LayerChange("t2", "Old Table", "removed"),
                LayerChange("t3", "Updated Table", "modified"),
            ]
        )

        result = format_diff_summary(diff)

        assert "Added tables (1):" in result
        assert "Removed tables (1):" in result
        assert "Modified tables (1):" in result

    def test_format_property_changes(self) -> None:
        """Test formatting property changes."""
        diff = MapDiff(
            property_changes={
                "values_changed": {"root['version']": {}},
                "dictionary_item_added": {"root['newKey']": {}},
            }
        )

        result = format_diff_summary(diff)

        assert "Map properties changed:" in result
        assert "* values_changed" in result
        assert "* dictionary_item_added" in result

    def test_format_mixed_changes(self) -> None:
        """Test formatting multiple types of changes."""
        diff = MapDiff(
            layer_changes=[
                LayerChange("l1", "New Layer", "added"),
                LayerChange("l2", "Changed Layer", "modified"),
            ],
            table_changes=[
                LayerChange("t1", "Old Table", "removed"),
            ],
            property_changes={"values_changed": {}},
        )

        result = format_diff_summary(diff)

        assert "Added layers" in result
        assert "Modified layers" in result
        assert "Removed tables" in result
        assert "Map properties changed" in result
