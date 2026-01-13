"""Unit tests for Norway Alerts sensor platform."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from custom_components.norway_alerts.const import (
    CONF_WARNING_TYPE, 
    WARNING_TYPE_LANDSLIDE,
    CONF_COUNTY_ID,
    CONF_COUNTY_NAME,
    CONF_LANG,
)


class TestNorwayAlertsCoordinator:
    """Test Norway Alerts coordinator."""

    @pytest.mark.asyncio
    async def test_coordinator_update_with_alerts(self, mock_hass, mock_county_api_response):
        """Test coordinator update when alerts exist."""
        from custom_components.norway_alerts.sensor import NorwayAlertsCoordinator
        
        coordinator = NorwayAlertsCoordinator(
            hass=mock_hass,
            county_id="46",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
            lang="en",
        )
        
        with patch.object(coordinator._api, "fetch_warnings", return_value=mock_county_api_response):
            await coordinator._async_update_data()
        
        assert coordinator.data is not None
        assert len(coordinator.data.get("active_alerts", [])) == 1

    @pytest.mark.asyncio
    async def test_coordinator_update_no_alerts(self, mock_hass):
        """Test coordinator update when no alerts exist."""
        from custom_components.norway_alerts.sensor import NorwayAlertsCoordinator
        
        coordinator = NorwayAlertsCoordinator(
            hass=mock_hass,
            county_id="46",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
            lang="en",
        )
        
        with patch.object(coordinator._api, "fetch_warnings", return_value=[]):
            await coordinator._async_update_data()
        
        assert coordinator.data is not None
        assert len(coordinator.data.get("active_alerts", [])) == 0


class TestNorwayAlertsSensor:
    """Test Norway Alerts sensor entity."""

    def test_sensor_creation(self):
        """Test sensor can be created."""
        from custom_components.norway_alerts.sensor import NorwayAlertsSensor, NorwayAlertsCoordinator
        
        mock_hass = MagicMock()
        coordinator = NorwayAlertsCoordinator(
            hass=mock_hass,
            county_id="46",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
            lang="en",
        )
        
        sensor = NorwayAlertsSensor(
            coordinator=coordinator,
            entry_id="test_entry",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
        )
        
        assert sensor is not None
        assert sensor.name == "Vestland Landslide"

    def test_sensor_state_with_alerts(self):
        """Test sensor state when alerts exist."""
        from custom_components.norway_alerts.sensor import NorwayAlertsSensor, NorwayAlertsCoordinator
        
        mock_hass = MagicMock()
        coordinator = NorwayAlertsCoordinator(
            hass=mock_hass,
            county_id="46",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
            lang="en",
        )
        
        # Mock coordinator data
        coordinator.data = {
            "active_alerts": [{"ActivityLevel": "2"}],
            "highest_level_numeric": 2,
            "highest_level": "yellow",
        }
        
        sensor = NorwayAlertsSensor(
            coordinator=coordinator,
            entry_id="test_entry",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
        )
        
        assert sensor.native_value == 1  # One alert

    def test_sensor_state_no_alerts(self):
        """Test sensor state when no alerts exist."""
        from custom_components.norway_alerts.sensor import NorwayAlertsSensor, NorwayAlertsCoordinator
        
        mock_hass = MagicMock()
        coordinator = NorwayAlertsCoordinator(
            hass=mock_hass,
            county_id="46",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
            lang="en",
        )
        
        # Mock coordinator data with no alerts
        coordinator.data = {
            "active_alerts": [],
            "highest_level_numeric": 0,
            "highest_level": "green",
        }
        
        sensor = NorwayAlertsSensor(
            coordinator=coordinator,
            entry_id="test_entry",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
        )
        
        assert sensor.native_value == 0
