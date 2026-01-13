"""Unit tests for Norway Alerts config flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_NAME

from custom_components.norway_alerts.const import (
    DOMAIN,
    CONF_COUNTY_ID,
    CONF_COUNTY_NAME,
    CONF_WARNING_TYPE,
    CONF_LANG,
    WARNING_TYPE_LANDSLIDE,
    WARNING_TYPE_METALERTS,
)


class TestConfigFlow:
    """Test Norway Alerts config flow."""

    @pytest.mark.asyncio
    async def test_show_user_form(self, mock_hass):
        """Test initial user form is shown."""
        from custom_components.norway_alerts.config_flow import NorwayAlertsConfigFlow
        
        flow = NorwayAlertsConfigFlow()
        flow.hass = mock_hass
        
        result = await flow.async_step_user()
        
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_user_form_validation_success(self, mock_hass):
        """Test user form with valid input."""
        from custom_components.norway_alerts.config_flow import NorwayAlertsConfigFlow
        
        flow = NorwayAlertsConfigFlow()
        flow.hass = mock_hass
        
        # Initialize the flow to set up context properly
        await flow.async_step_user()
        
        with patch("custom_components.norway_alerts.config_flow.validate_api_connection", return_value=True):
            result = await flow.async_step_user({
                CONF_NAME: "Test Alerts",
                CONF_COUNTY_ID: "46",
                CONF_COUNTY_NAME: "Vestland",
                CONF_WARNING_TYPE: WARNING_TYPE_LANDSLIDE,
                CONF_LANG: "en",
            })
        
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Test Alerts"

    @pytest.mark.asyncio
    async def test_options_flow(self, mock_hass):
        """Test options flow."""
        from custom_components.norway_alerts.config_flow import NorwayAlertsOptionsFlow
        
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry"
        config_entry.data = {
            CONF_NAME: "Test Alerts",
            CONF_COUNTY_ID: "46",
            CONF_COUNTY_NAME: "Vestland",
            CONF_WARNING_TYPE: WARNING_TYPE_LANDSLIDE,
        }
        config_entry.options = {}
        
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_update_entry = AsyncMock()
        
        flow = NorwayAlertsOptionsFlow(config_entry)
        flow.hass = mock_hass
        
        result = await flow.async_step_init()
        
        assert result["type"] == data_entry_flow.FlowResultType.FORM
