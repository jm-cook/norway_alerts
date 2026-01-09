"""The Varsom Alerts integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_LANG,
    CONF_COUNTY_ID,
    CONF_COUNTY_NAME,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_WARNING_TYPE,
    CONF_TEST_MODE,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NOTIFICATION_SEVERITY,
    NOTIFICATION_SEVERITY_YELLOW_PLUS,
)
from .sensor import VarsomAlertsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Varsom Alerts from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Get config from entry.options (preferred) or entry.data (fallback)
    config = entry.options if entry.options else entry.data
    
    warning_type = config.get(CONF_WARNING_TYPE) or entry.data.get(CONF_WARNING_TYPE)
    lang = config.get(CONF_LANG) or entry.data.get(CONF_LANG, "en")
    test_mode = config.get(CONF_TEST_MODE, False)
    enable_notifications = config.get(CONF_ENABLE_NOTIFICATIONS, False)
    notification_severity = config.get(CONF_NOTIFICATION_SEVERITY, NOTIFICATION_SEVERITY_YELLOW_PLUS)
    
    # Determine if this is a county-based or lat/lon-based configuration
    county_id = config.get(CONF_COUNTY_ID) or entry.data.get(CONF_COUNTY_ID)
    latitude = config.get(CONF_LATITUDE) or entry.data.get(CONF_LATITUDE)
    longitude = config.get(CONF_LONGITUDE) or entry.data.get(CONF_LONGITUDE)
    
    if county_id:
        # County-based configuration (NVE warnings)
        county_name = config.get(CONF_COUNTY_NAME) or entry.data.get(CONF_COUNTY_NAME, "Unknown")
        coordinator = VarsomAlertsCoordinator(
            hass, county_id, county_name, warning_type, lang, test_mode,
            enable_notifications, notification_severity,
            latitude=None, longitude=None
        )
    else:
        # Lat/lon-based configuration (Met.no metalerts)
        coordinator = VarsomAlertsCoordinator(
            hass, None, None, warning_type, lang, test_mode,
            enable_notifications, notification_severity,
            latitude=latitude, longitude=longitude
        )
    
    # Do the first refresh before setting up platforms
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to initialize coordinator: %s", err)
        raise ConfigEntryNotReady(f"Failed to connect to API: {err}") from err
    
    # Store coordinator in hass.data for the sensor platform
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
