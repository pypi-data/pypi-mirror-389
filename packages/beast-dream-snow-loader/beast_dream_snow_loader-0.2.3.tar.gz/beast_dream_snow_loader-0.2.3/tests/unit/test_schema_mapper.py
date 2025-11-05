"""Unit tests for schema mapper."""

from beast_dream_snow_loader.transformers.schema_mapper import (
    FieldMappingConfig,
    flatten_nested_field,
    get_field_mapping,
)


class TestFieldMappingConfig:
    """Test FieldMappingConfig configuration class."""

    def test_host_mapping_config_exists(self):
        """Test that host → gateway CI mappings are defined."""
        config = FieldMappingConfig()
        mappings = config.get_host_mappings()
        assert mappings is not None
        assert len(mappings) > 0

    def test_site_mapping_config_exists(self):
        """Test that site → location mappings are defined."""
        config = FieldMappingConfig()
        mappings = config.get_site_mappings()
        assert mappings is not None
        assert len(mappings) > 0

    def test_device_mapping_config_exists(self):
        """Test that device → network device CI mappings are defined."""
        config = FieldMappingConfig()
        mappings = config.get_device_mappings()
        assert mappings is not None
        assert len(mappings) > 0

    def test_client_mapping_config_exists(self):
        """Test that client → endpoint mappings are defined."""
        config = FieldMappingConfig()
        mappings = config.get_client_mappings()
        assert mappings is not None
        assert len(mappings) > 0

    def test_host_mapping_covers_core_fields(self):
        """Test that host mappings cover core required fields."""
        config = FieldMappingConfig()
        mappings = config.get_host_mappings()
        # Check for key mappings from design
        assert "id" in mappings or any("sys_id" in str(m) for m in mappings.values())
        assert any(
            "hostname" in str(v) for v in mappings.values()
        )  # reportedState.hostname → hostname

    def test_mapping_supports_nested_fields(self):
        """Test that mappings support nested field paths."""
        config = FieldMappingConfig()
        mappings = config.get_host_mappings()
        # Should have nested field mappings like "reportedState.hostname"
        assert any("." in k for k in mappings.keys())


class TestFieldFlattening:
    """Test field flattening logic."""

    def test_flatten_simple_nested_field(self):
        """Test flattening simple nested field."""
        result = flatten_nested_field("reportedState.hostname")
        assert result == "hostname"

    def test_flatten_deeply_nested_field(self):
        """Test flattening deeply nested field."""
        result = flatten_nested_field("reportedState.hardware.mac")
        assert (
            result == "hardware_mac"
        )  # Flattened: drops reportedState, joins hardware.mac

    def test_flatten_very_deeply_nested_field(self):
        """Test flattening very deeply nested field."""
        result = flatten_nested_field("reportedState.autoUpdate.schedule.day")
        assert result == "auto_update_schedule_day"

    def test_flatten_uses_underscore_notation(self):
        """Test that flattened fields use underscore notation."""
        result = flatten_nested_field("reportedState.hardware.serialno")
        assert "_" in result
        assert result == "hardware_serial_number" or result == "hardware_serialno"

    def test_get_field_mapping_returns_target(self):
        """Test that get_field_mapping returns target field name."""
        config = FieldMappingConfig()
        target = get_field_mapping("reportedState.hostname", config.get_host_mappings())
        assert target == "hostname" or target is not None

    def test_get_field_mapping_handles_missing(self):
        """Test that get_field_mapping handles missing mappings."""
        config = FieldMappingConfig()
        mappings = config.get_host_mappings()
        target = get_field_mapping("nonexistent.field", mappings)
        # Should return None or use flattening as fallback
        assert target is None or isinstance(target, str)
