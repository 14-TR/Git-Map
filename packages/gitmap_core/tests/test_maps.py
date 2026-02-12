"""Tests for web map JSON operations module.

Tests web map extraction, layer operations, comparison functions,
and serialization. Uses mocks to avoid actual Portal/ArcGIS API calls.

Execution Context:
    Test module - run via pytest

Dependencies:
    - pytest: Test framework
    - unittest.mock: Mocking ArcGIS objects
    - gitmap_core.maps: Module under test
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from gitmap_core.maps import (
    compare_layers,
    create_empty_webmap,
    get_basemap_layers,
    get_layer_by_id,
    get_layer_ids,
    get_operational_layers,
    get_webmap_by_id,
    get_webmap_json,
    list_services,
    list_webmaps,
    load_map_json,
    save_map_json,
)


# ---- Fixtures ------------------------------------------------------------------------------------------------


@pytest.fixture
def sample_webmap_data() -> dict[str, Any]:
    """Sample web map JSON for testing."""
    return {
        "operationalLayers": [
            {
                "id": "layer-001",
                "title": "Roads",
                "layerType": "ArcGISFeatureLayer",
                "url": "https://services.example.com/roads/FeatureServer/0",
                "opacity": 1.0,
            },
            {
                "id": "layer-002",
                "title": "Parcels",
                "layerType": "ArcGISFeatureLayer",
                "url": "https://services.example.com/parcels/FeatureServer/0",
                "opacity": 0.8,
            },
            {
                "id": "layer-003",
                "title": "Buildings",
                "layerType": "ArcGISFeatureLayer",
                "url": "https://services.example.com/buildings/FeatureServer/0",
            },
        ],
        "baseMap": {
            "baseMapLayers": [
                {
                    "id": "basemap-001",
                    "title": "World Topographic Map",
                    "layerType": "ArcGISTiledMapServiceLayer",
                    "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
                },
            ],
            "title": "Topographic",
        },
        "spatialReference": {
            "wkid": 102100,
            "latestWkid": 3857,
        },
        "version": "2.28",
        "authoringApp": "ArcGIS Online",
    }


@pytest.fixture
def mock_webmap_item(sample_webmap_data: dict[str, Any]) -> MagicMock:
    """Create a mock Portal Item for web map."""
    item = MagicMock()
    item.type = "Web Map"
    item.title = "Test Web Map"
    item.id = "test-item-id-123"
    item.get_data.return_value = sample_webmap_data
    return item


@pytest.fixture
def mock_gis() -> MagicMock:
    """Create a mock GIS connection."""
    gis = MagicMock()
    return gis


@pytest.fixture
def temp_json_path() -> Path:
    """Create temporary JSON file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "map.json"


# ---- get_webmap_json Tests ----------------------------------------------------------------------------------


class TestGetWebmapJson:
    """Tests for get_webmap_json function."""

    def test_extract_webmap_json(
        self, mock_webmap_item: MagicMock, sample_webmap_data: dict
    ) -> None:
        """Test extracting web map JSON from Portal item."""
        result = get_webmap_json(mock_webmap_item)

        assert result == sample_webmap_data
        mock_webmap_item.get_data.assert_called_once()

    def test_raises_for_non_webmap_type(self) -> None:
        """Test that non-Web Map items raise RuntimeError."""
        item = MagicMock()
        item.type = "Feature Service"
        item.title = "Not a Map"

        with pytest.raises(RuntimeError) as exc_info:
            get_webmap_json(item)

        assert "is not a Web Map" in str(exc_info.value)
        assert "Feature Service" in str(exc_info.value)

    def test_raises_when_get_data_returns_none(self, mock_webmap_item: MagicMock) -> None:
        """Test that empty data raises RuntimeError."""
        mock_webmap_item.get_data.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            get_webmap_json(mock_webmap_item)

        assert "Failed to get data" in str(exc_info.value)

    def test_raises_on_extraction_error(self, mock_webmap_item: MagicMock) -> None:
        """Test that extraction errors are wrapped in RuntimeError."""
        mock_webmap_item.get_data.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError) as exc_info:
            get_webmap_json(mock_webmap_item)

        assert "Failed to extract web map JSON" in str(exc_info.value)


# ---- get_webmap_by_id Tests ---------------------------------------------------------------------------------


class TestGetWebmapById:
    """Tests for get_webmap_by_id function."""

    def test_fetch_webmap_by_id(
        self, mock_gis: MagicMock, sample_webmap_data: dict
    ) -> None:
        """Test fetching web map by item ID."""
        item = MagicMock()
        item.type = "Web Map"
        item.title = "Test Map"
        item.get_data.return_value = sample_webmap_data
        mock_gis.content.get.return_value = item

        result_item, result_data = get_webmap_by_id(mock_gis, "item-id-123")

        assert result_item == item
        assert result_data == sample_webmap_data
        mock_gis.content.get.assert_called_once_with("item-id-123")

    def test_raises_when_item_not_found(self, mock_gis: MagicMock) -> None:
        """Test that missing item raises RuntimeError."""
        mock_gis.content.get.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            get_webmap_by_id(mock_gis, "nonexistent-id")

        assert "not found" in str(exc_info.value)

    def test_raises_for_non_webmap(self, mock_gis: MagicMock) -> None:
        """Test that non-Web Map item raises RuntimeError."""
        item = MagicMock()
        item.type = "Feature Layer"
        item.title = "Layer"
        mock_gis.content.get.return_value = item

        with pytest.raises(RuntimeError) as exc_info:
            get_webmap_by_id(mock_gis, "layer-id")

        assert "is not a Web Map" in str(exc_info.value)

    def test_raises_on_fetch_error(self, mock_gis: MagicMock) -> None:
        """Test that API errors are wrapped in RuntimeError."""
        mock_gis.content.get.side_effect = Exception("Network Error")

        with pytest.raises(RuntimeError) as exc_info:
            get_webmap_by_id(mock_gis, "item-id")

        assert "Failed to fetch web map" in str(exc_info.value)


# ---- list_webmaps Tests -------------------------------------------------------------------------------------


class TestListWebmaps:
    """Tests for list_webmaps function."""

    def test_list_all_webmaps(self, mock_gis: MagicMock) -> None:
        """Test listing all web maps."""
        mock_items = [
            MagicMock(id="map-1", title="Map One", owner="user1", type="Web Map"),
            MagicMock(id="map-2", title="Map Two", owner="user2", type="Web Map"),
        ]
        mock_gis.content.search.return_value = mock_items

        result = list_webmaps(mock_gis)

        assert len(result) == 2
        assert result[0]["id"] == "map-1"
        assert result[1]["title"] == "Map Two"

    def test_list_webmaps_with_query(self, mock_gis: MagicMock) -> None:
        """Test listing with search query."""
        mock_gis.content.search.return_value = []

        list_webmaps(mock_gis, query="title:Roads")

        call_args = mock_gis.content.search.call_args
        assert "Roads" in call_args.kwargs.get("query", call_args[1].get("query", ""))

    def test_list_webmaps_filter_by_owner(self, mock_gis: MagicMock) -> None:
        """Test filtering by owner."""
        mock_gis.content.search.return_value = []

        list_webmaps(mock_gis, owner="john_doe")

        call_args = mock_gis.content.search.call_args
        query = call_args.kwargs.get("query", call_args[1].get("query", ""))
        assert "owner:john_doe" in query

    def test_list_webmaps_filter_by_tag(self, mock_gis: MagicMock) -> None:
        """Test filtering by tag."""
        mock_gis.content.search.return_value = []

        list_webmaps(mock_gis, tag="infrastructure")

        call_args = mock_gis.content.search.call_args
        query = call_args.kwargs.get("query", call_args[1].get("query", ""))
        assert "tags:infrastructure" in query

    def test_list_webmaps_max_results(self, mock_gis: MagicMock) -> None:
        """Test max_results parameter."""
        mock_gis.content.search.return_value = []

        list_webmaps(mock_gis, max_results=50)

        call_args = mock_gis.content.search.call_args
        assert call_args.kwargs.get("max_items", call_args[1].get("max_items")) == 50

    def test_list_webmaps_raises_on_error(self, mock_gis: MagicMock) -> None:
        """Test error handling."""
        mock_gis.content.search.side_effect = Exception("Search failed")

        with pytest.raises(RuntimeError) as exc_info:
            list_webmaps(mock_gis)

        assert "Failed to search web maps" in str(exc_info.value)

    def test_list_webmaps_handles_missing_attributes(self, mock_gis: MagicMock) -> None:
        """Test handling items with missing attributes."""
        # Item with some missing attributes
        item = MagicMock(spec=[])  # Empty spec means no attributes by default
        mock_gis.content.search.return_value = [item]

        result = list_webmaps(mock_gis)

        assert len(result) == 1
        assert result[0]["id"] == ""
        assert result[0]["title"] == ""


# ---- list_services Tests ------------------------------------------------------------------------------------


class TestListServices:
    """Tests for list_services function."""

    def test_list_feature_services_default(self, mock_gis: MagicMock) -> None:
        """Test listing Feature Services by default."""
        mock_items = [
            MagicMock(
                id="svc-1",
                title="Roads Service",
                owner="admin",
                type="Feature Service",
                url="https://example.com/roads",
            ),
        ]
        mock_gis.content.search.return_value = mock_items

        result = list_services(mock_gis)

        assert len(result) == 1
        assert result[0]["type"] == "Feature Service"
        assert result[0]["url"] == "https://example.com/roads"

    def test_list_services_by_type(self, mock_gis: MagicMock) -> None:
        """Test filtering by service type."""
        mock_gis.content.search.return_value = []

        list_services(mock_gis, service_type="Map Service")

        call_args = mock_gis.content.search.call_args
        query = call_args.kwargs.get("query", call_args[1].get("query", ""))
        assert 'type:"Map Service"' in query

    def test_list_services_filter_by_owner(self, mock_gis: MagicMock) -> None:
        """Test filtering by owner."""
        mock_gis.content.search.return_value = []

        list_services(mock_gis, owner="gis_admin")

        call_args = mock_gis.content.search.call_args
        query = call_args.kwargs.get("query", call_args[1].get("query", ""))
        assert "owner:gis_admin" in query

    def test_list_services_with_query(self, mock_gis: MagicMock) -> None:
        """Test with search query."""
        mock_gis.content.search.return_value = []

        list_services(mock_gis, query="utilities")

        call_args = mock_gis.content.search.call_args
        query = call_args.kwargs.get("query", call_args[1].get("query", ""))
        assert "utilities" in query

    def test_list_services_raises_on_error(self, mock_gis: MagicMock) -> None:
        """Test error handling."""
        mock_gis.content.search.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError) as exc_info:
            list_services(mock_gis)

        assert "Failed to search services" in str(exc_info.value)


# ---- Layer Operation Tests ----------------------------------------------------------------------------------


class TestLayerOperations:
    """Tests for layer extraction functions."""

    def test_get_operational_layers(self, sample_webmap_data: dict) -> None:
        """Test extracting operational layers."""
        layers = get_operational_layers(sample_webmap_data)

        assert len(layers) == 3
        assert layers[0]["id"] == "layer-001"
        assert layers[1]["title"] == "Parcels"

    def test_get_operational_layers_empty(self) -> None:
        """Test with no operational layers."""
        map_data = {"baseMap": {}}

        layers = get_operational_layers(map_data)

        assert layers == []

    def test_get_basemap_layers(self, sample_webmap_data: dict) -> None:
        """Test extracting basemap layers."""
        layers = get_basemap_layers(sample_webmap_data)

        assert len(layers) == 1
        assert layers[0]["id"] == "basemap-001"

    def test_get_basemap_layers_empty(self) -> None:
        """Test with no basemap."""
        map_data = {"operationalLayers": []}

        layers = get_basemap_layers(map_data)

        assert layers == []

    def test_get_basemap_layers_no_basemap_layers_key(self) -> None:
        """Test with basemap but no baseMapLayers key."""
        map_data = {"baseMap": {"title": "Custom"}}

        layers = get_basemap_layers(map_data)

        assert layers == []

    def test_get_layer_by_id_found(self, sample_webmap_data: dict) -> None:
        """Test finding layer by ID."""
        layer = get_layer_by_id(sample_webmap_data, "layer-002")

        assert layer is not None
        assert layer["title"] == "Parcels"

    def test_get_layer_by_id_not_found(self, sample_webmap_data: dict) -> None:
        """Test layer not found returns None."""
        layer = get_layer_by_id(sample_webmap_data, "nonexistent-layer")

        assert layer is None

    def test_get_layer_ids(self, sample_webmap_data: dict) -> None:
        """Test getting all layer IDs."""
        ids = get_layer_ids(sample_webmap_data)

        assert ids == ["layer-001", "layer-002", "layer-003"]

    def test_get_layer_ids_empty(self) -> None:
        """Test getting IDs from empty map."""
        map_data: dict = {"operationalLayers": []}

        ids = get_layer_ids(map_data)

        assert ids == []

    def test_get_layer_ids_skips_layers_without_id(self) -> None:
        """Test that layers without id are skipped."""
        map_data = {
            "operationalLayers": [
                {"id": "layer-1", "title": "Layer 1"},
                {"title": "No ID Layer"},  # Missing id
                {"id": "layer-3", "title": "Layer 3"},
            ]
        }

        ids = get_layer_ids(map_data)

        assert ids == ["layer-1", "layer-3"]


# ---- compare_layers Tests -----------------------------------------------------------------------------------


class TestCompareLayers:
    """Tests for compare_layers function."""

    def test_compare_no_changes(self) -> None:
        """Test comparing identical layer lists."""
        layers = [
            {"id": "layer-1", "title": "Roads"},
            {"id": "layer-2", "title": "Parcels"},
        ]

        result = compare_layers(layers, layers)

        assert result["added"] == []
        assert result["removed"] == []
        assert result["modified"] == []

    def test_compare_added_layers(self) -> None:
        """Test detecting added layers."""
        layers1 = [
            {"id": "layer-1", "title": "Roads"},
            {"id": "layer-2", "title": "Parcels"},
        ]
        layers2 = [{"id": "layer-1", "title": "Roads"}]

        result = compare_layers(layers1, layers2)

        assert len(result["added"]) == 1
        assert result["added"][0]["id"] == "layer-2"
        assert result["removed"] == []

    def test_compare_removed_layers(self) -> None:
        """Test detecting removed layers."""
        layers1 = [{"id": "layer-1", "title": "Roads"}]
        layers2 = [
            {"id": "layer-1", "title": "Roads"},
            {"id": "layer-2", "title": "Parcels"},
        ]

        result = compare_layers(layers1, layers2)

        assert result["added"] == []
        assert len(result["removed"]) == 1
        assert result["removed"][0]["id"] == "layer-2"

    def test_compare_modified_layers(self) -> None:
        """Test detecting modified layers."""
        layers1 = [{"id": "layer-1", "title": "Roads", "opacity": 0.5}]
        layers2 = [{"id": "layer-1", "title": "Roads", "opacity": 1.0}]

        result = compare_layers(layers1, layers2)

        assert result["added"] == []
        assert result["removed"] == []
        assert len(result["modified"]) == 1
        assert result["modified"][0]["id"] == "layer-1"
        assert result["modified"][0]["old"]["opacity"] == 1.0
        assert result["modified"][0]["new"]["opacity"] == 0.5

    def test_compare_all_changes(self) -> None:
        """Test detecting added, removed, and modified all at once."""
        layers1 = [
            {"id": "layer-1", "title": "Roads Updated"},  # modified
            {"id": "layer-3", "title": "New Layer"},  # added
        ]
        layers2 = [
            {"id": "layer-1", "title": "Roads"},  # original
            {"id": "layer-2", "title": "Removed"},  # will be removed
        ]

        result = compare_layers(layers1, layers2)

        assert len(result["added"]) == 1
        assert result["added"][0]["id"] == "layer-3"
        assert len(result["removed"]) == 1
        assert result["removed"][0]["id"] == "layer-2"
        assert len(result["modified"]) == 1
        assert result["modified"][0]["id"] == "layer-1"

    def test_compare_empty_lists(self) -> None:
        """Test comparing empty lists."""
        result = compare_layers([], [])

        assert result == {"added": [], "removed": [], "modified": []}

    def test_compare_skips_layers_without_id(self) -> None:
        """Test that layers without id are skipped in comparison."""
        layers1 = [{"title": "No ID"}]
        layers2 = [{"title": "No ID Either"}]

        result = compare_layers(layers1, layers2)

        assert result == {"added": [], "removed": [], "modified": []}


# ---- Serialization Tests ------------------------------------------------------------------------------------


class TestSerialization:
    """Tests for save_map_json and load_map_json functions."""

    def test_save_map_json(
        self, temp_json_path: Path, sample_webmap_data: dict
    ) -> None:
        """Test saving map JSON to file."""
        save_map_json(sample_webmap_data, temp_json_path)

        assert temp_json_path.exists()
        content = json.loads(temp_json_path.read_text())
        assert content == sample_webmap_data

    def test_save_map_json_formatting(
        self, temp_json_path: Path, sample_webmap_data: dict
    ) -> None:
        """Test that saved JSON is indented."""
        save_map_json(sample_webmap_data, temp_json_path)

        content = temp_json_path.read_text()
        assert "\n" in content  # Has newlines (indented)

    def test_load_map_json(
        self, temp_json_path: Path, sample_webmap_data: dict
    ) -> None:
        """Test loading map JSON from file."""
        temp_json_path.write_text(json.dumps(sample_webmap_data))

        result = load_map_json(temp_json_path)

        assert result == sample_webmap_data

    def test_load_map_json_raises_on_missing_file(self, temp_json_path: Path) -> None:
        """Test that missing file raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            load_map_json(temp_json_path)

        assert "Failed to load map JSON" in str(exc_info.value)

    def test_load_map_json_raises_on_invalid_json(self, temp_json_path: Path) -> None:
        """Test that invalid JSON raises RuntimeError."""
        temp_json_path.write_text("not valid json {{{")

        with pytest.raises(RuntimeError) as exc_info:
            load_map_json(temp_json_path)

        assert "Failed to load map JSON" in str(exc_info.value)

    def test_round_trip(
        self, temp_json_path: Path, sample_webmap_data: dict
    ) -> None:
        """Test save then load returns identical data."""
        save_map_json(sample_webmap_data, temp_json_path)
        result = load_map_json(temp_json_path)

        assert result == sample_webmap_data


# ---- create_empty_webmap Tests ------------------------------------------------------------------------------


class TestCreateEmptyWebmap:
    """Tests for create_empty_webmap function."""

    def test_create_default_empty_webmap(self) -> None:
        """Test creating default empty web map."""
        result = create_empty_webmap()

        assert result["operationalLayers"] == []
        assert result["baseMap"]["baseMapLayers"] == []
        assert result["spatialReference"]["wkid"] == 102100
        assert result["authoringApp"] == "GitMap"

    def test_create_empty_webmap_with_title(self) -> None:
        """Test creating empty web map with custom title."""
        result = create_empty_webmap(title="My Custom Map")

        # Title is not stored in structure, but baseMap has title
        assert result["baseMap"]["title"] == "Basemap"

    def test_create_empty_webmap_with_spatial_reference(self) -> None:
        """Test creating empty web map with custom spatial reference."""
        result = create_empty_webmap(spatial_reference=4326)

        assert result["spatialReference"]["wkid"] == 4326

    def test_create_empty_webmap_has_version(self) -> None:
        """Test that empty web map has version."""
        result = create_empty_webmap()

        assert "version" in result
        assert result["version"] == "2.28"

    def test_create_empty_webmap_has_authoring_version(self) -> None:
        """Test that empty web map has authoring app version."""
        result = create_empty_webmap()

        assert result["authoringAppVersion"] == "0.1.0"
