"""Unit tests for Norway Alerts sensor platform."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from homeassistant.helpers import frame

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
        
        # Mock frame.report_usage to avoid frame helper issues in Python 3.13
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = NorwayAlertsCoordinator(
                hass=mock_hass,
                county_id="46",
                county_name="Vestland",
                warning_type=WARNING_TYPE_LANDSLIDE,
                lang="en",
            )
        
        # Mock the WarningAPIFactory and API client
        with patch("custom_components.norway_alerts.sensor.WarningAPIFactory") as mock_factory:
            mock_api = AsyncMock()
            mock_api.fetch_warnings = AsyncMock(return_value=mock_county_api_response)
            mock_factory.return_value.get_api.return_value = mock_api
            
            result = await coordinator._async_update_data()
        
        assert result is not None
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_coordinator_update_no_alerts(self, mock_hass):
        """Test coordinator update when no alerts exist."""
        from custom_components.norway_alerts.sensor import NorwayAlertsCoordinator
        
        # Mock frame.report_usage to avoid frame helper issues in Python 3.13
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = NorwayAlertsCoordinator(
                hass=mock_hass,
                county_id="46",
                county_name="Vestland",
                warning_type=WARNING_TYPE_LANDSLIDE,
                lang="en",
            )
        
        # Mock the WarningAPIFactory and API client
        with patch("custom_components.norway_alerts.sensor.WarningAPIFactory") as mock_factory:
            mock_api = AsyncMock()
            mock_api.fetch_warnings = AsyncMock(return_value=[])
            mock_factory.return_value.get_api.return_value = mock_api
            
            result = await coordinator._async_update_data()
        
        assert result is not None
        assert len(result) == 0


class TestNorwayAlertsSensor:
    """Test Norway Alerts sensor entity."""

    def test_sensor_creation(self):
        """Test sensor can be created."""
        from custom_components.norway_alerts.sensor import NorwayAlertsSensor, NorwayAlertsCoordinator
        
        mock_hass = MagicMock()
        
        # Mock frame.report_usage to avoid frame helper issues in Python 3.13
        with patch("homeassistant.helpers.frame.report_usage"):
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
        assert sensor.name == "Norway Alerts Landslide Vestland"

    def test_sensor_state_with_alerts(self):
        """Test sensor state when alerts exist."""
        from custom_components.norway_alerts.sensor import NorwayAlertsSensor, NorwayAlertsCoordinator
        
        mock_hass = MagicMock()
        
        # Mock frame.report_usage to avoid frame helper issues in Python 3.13
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = NorwayAlertsCoordinator(
                hass=mock_hass,
                county_id="46",
                county_name="Vestland",
                warning_type=WARNING_TYPE_LANDSLIDE,
                lang="en",
            )
        
        # Mock coordinator data - it returns a list of alerts
        coordinator.data = [{"ActivityLevel": "2", "Id": 123}]
        
        sensor = NorwayAlertsSensor(
            coordinator=coordinator,
            entry_id="test_entry",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
        )
        
        assert sensor.native_value == 1  # One alert

    def test_sensor_state_no_alerts(self):
        """Test sensor state when no alerts exist."""
        
        # Mock frame.report_usage to avoid frame helper issues in Python 3.13
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = NorwayAlertsCoordinator(
                hass=mock_hass,
                county_id="46",
                county_name="Vestland",
                warning_type=WARNING_TYPE_LANDSLIDE,
                lang="en",
        )
        
        # Mock coordinator data with no alerts (empty list)
        coordinator.data = []
        
        sensor = NorwayAlertsSensor(
            coordinator=coordinator,
            entry_id="test_entry",
            county_name="Vestland",
            warning_type=WARNING_TYPE_LANDSLIDE,
        )
        
        assert sensor.native_value == 0
