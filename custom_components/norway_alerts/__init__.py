"""The Norway Alerts integration."""
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
    CONF_CAP_FORMAT,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NOTIFICATION_SEVERITY,
    NOTIFICATION_SEVERITY_YELLOW_PLUS,
)
from .sensor import NorwayAlertsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Norway Alerts from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    _LOGGER.debug("Setting up Norway Alerts entry: %s", entry.entry_id)
    
    # Get config from entry.options (preferred) or entry.data (fallback)
    config = entry.options if entry.options else entry.data
    
    warning_type = config.get(CONF_WARNING_TYPE) or entry.data.get(CONF_WARNING_TYPE)
    lang = config.get(CONF_LANG) or entry.data.get(CONF_LANG, "en")
    test_mode = config.get(CONF_TEST_MODE, False)
    cap_format = config.get(CONF_CAP_FORMAT, True)  # Default to True for CAP format
    enable_notifications = config.get(CONF_ENABLE_NOTIFICATIONS, False)
    notification_severity = config.get(CONF_NOTIFICATION_SEVERITY, NOTIFICATION_SEVERITY_YELLOW_PLUS)
    
    # Determine if this is a county-based or lat/lon-based configuration
    county_id = config.get(CONF_COUNTY_ID) or entry.data.get(CONF_COUNTY_ID)
    latitude = config.get(CONF_LATITUDE) or entry.data.get(CONF_LATITUDE)
    longitude = config.get(CONF_LONGITUDE) or entry.data.get(CONF_LONGITUDE)
    
    _LOGGER.debug("Config: warning_type=%s, county_id=%s, lat=%s, lon=%s, cap_format=%s", 
                  warning_type, county_id, latitude, longitude, cap_format)
    
    if county_id:
        # County-based configuration (NVE warnings)
        county_name = config.get(CONF_COUNTY_NAME) or entry.data.get(CONF_COUNTY_NAME, "Unknown")
        _LOGGER.debug("Creating county-based coordinator for %s (%s)", county_name, county_id)
        coordinator = NorwayAlertsCoordinator(
            hass, county_id, county_name, warning_type, lang, test_mode,
            enable_notifications, notification_severity, cap_format,
            latitude=None, longitude=None, config_entry=entry
        )
    else:
        # Lat/lon-based configuration (Met.no metalerts)
        _LOGGER.debug("Creating coordinate-based coordinator for lat=%s, lon=%s", latitude, longitude)
        coordinator = NorwayAlertsCoordinator(
            hass, None, None, warning_type, lang, test_mode,
            enable_notifications, notification_severity, cap_format,
            latitude=latitude, longitude=longitude, config_entry=entry
        )
    
    # Do the first refresh before setting up platforms
    _LOGGER.debug("Performing first refresh for coordinator")
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("First refresh completed successfully")
    except Exception as err:
        _LOGGER.error("Failed to initialize coordinator: %s", err, exc_info=True)
        raise ConfigEntryNotReady(f"Failed to connect to API: {err}") from err
    
    # Store coordinator in hass.data for the sensor platform
    _LOGGER.debug("Storing coordinator in hass.data")
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    _LOGGER.debug("Forwarding setup to sensor platform")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    _LOGGER.info("Norway Alerts setup completed successfully")
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
