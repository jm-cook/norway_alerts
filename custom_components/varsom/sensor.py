"""Varsom Alerts sensor platform."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_LANG,
    CONF_COUNTY_ID,
    CONF_COUNTY_NAME,
    CONF_WARNING_TYPE,
    CONF_MUNICIPALITY_FILTER,
    CONF_TEST_MODE,
    API_BASE_LANDSLIDE,
    API_BASE_FLOOD,
    WARNING_TYPE_LANDSLIDE,
    WARNING_TYPE_FLOOD,
    WARNING_TYPE_BOTH,
    ACTIVITY_LEVEL_NAMES,
    ICON_DATA_URLS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Varsom Alerts sensor from a config entry."""
    # Get config from entry.options (preferred) or entry.data (fallback)
    # Options are used when user updates config, data is from initial setup
    config = entry.options if entry.options else entry.data
    
    county_id = config.get(CONF_COUNTY_ID) or entry.data.get(CONF_COUNTY_ID)
    county_name = config.get(CONF_COUNTY_NAME) or entry.data.get(CONF_COUNTY_NAME, "Unknown")
    warning_type = config.get(CONF_WARNING_TYPE) or entry.data.get(CONF_WARNING_TYPE)
    lang = config.get(CONF_LANG) or entry.data.get(CONF_LANG, "en")
    municipality_filter = config.get(CONF_MUNICIPALITY_FILTER, "")
    test_mode = config.get(CONF_TEST_MODE, False)
    
    coordinator = VarsomAlertsCoordinator(hass, county_id, county_name, warning_type, lang, test_mode)
    await coordinator.async_config_entry_first_refresh()
    
    # Create sensors
    entities = [
        # Main sensor with all county alerts
        VarsomAlertsSensor(coordinator, entry.entry_id, county_name, warning_type, municipality_filter, is_main=True),
    ]
    
    # If municipality filter is set, create an additional "My Area" sensor
    if municipality_filter:
        entities.append(
            VarsomAlertsSensor(coordinator, entry.entry_id, county_name, warning_type, municipality_filter, is_main=False)
        )
    
    async_add_entities(entities)


class VarsomAlertsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Varsom Alerts data."""

    def __init__(self, hass, county_id, county_name, warning_type, lang, test_mode=False):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.county_id = county_id
        self.county_name = county_name
        self.warning_type = warning_type
        self.lang = lang
        self.test_mode = test_mode

    async def _fetch_warnings(self, base_url: str, danger_type_label: str):
        """Fetch warnings from a specific API endpoint."""
        # NVE API uses Språknøkkel (language key) as path parameter:
        # 1 = Norwegian (LangKey: 1), 2 = English (LangKey: 2)
        lang_key = "2" if self.lang == "en" else "1"
        url = f"{base_url}/Warning/County/{self.county_id}/{lang_key}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "varsom/1.0.0 jeremy.m.cook@gmail.com"
        }
        
        _LOGGER.debug("Fetching %s warnings from: %s", danger_type_label, url)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with asyncio.timeout(10):
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            _LOGGER.error("Error fetching %s data: %s", danger_type_label, response.status)
                            return []

                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" not in content_type:
                            _LOGGER.error("Unexpected Content-Type for %s: %s", danger_type_label, content_type)
                            return []

                        json_data = await response.json()
                        _LOGGER.info("Successfully fetched %s warnings (count: %d)", danger_type_label, len(json_data))
                        return json_data
                        
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching %s warnings: %s", danger_type_label, err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error fetching %s warnings: %s", danger_type_label, err)
            return []

    async def _async_update_data(self):
        """Fetch data from API."""
        all_warnings = []
        
        try:
            # Inject test alert if test mode is enabled
            if self.test_mode:
                test_alert = {
                    "Id": 999999,
                    "ActivityLevel": "3",  # Orange
                    "DangerLevel": "Moderate", 
                    "DangerTypeName": "Jordskred",
                    "MainText": "Test Alert - Orange Landslide Warning for Testville", 
                    "WarningText": "Det er moderat fare for jordskred i Testville kommune. Væte og temperaturendringer kan utløse skred i bratte skråninger.",
                    "AdviceText": "Unngå opphold under bratte fjellsider og i skredfarlige områder. Vær særlig oppmerksom ved ferdsel i terrenget.",
                    "ConsequenceText": "Jordskred kan medføre skade på infrastruktur og fare for liv og helse. Mindre veier kan bli stengt.",
                    "EmergencyWarning": "Test emergency warning text for Testville landslide alert",
                    "LangKey": 2,
                    "ValidFrom": "2025-12-16T00:00:00",
                    "ValidTo": "2025-12-17T23:59:59", 
                    "NextWarningTime": "2025-12-17T08:00:00",
                    "PublishTime": "2025-12-16T08:00:00",
                    "DangerIncreaseDateTime": "2025-12-16T12:00:00",
                    "DangerDecreaseDateTime": "2025-12-17T06:00:00",
                    "Author": "Test System",
                    "MunicipalityList": [
                        {
                            "Id": "9999", 
                            "Name": "Testville",
                            "CountyId": "46",
                            "CountyName": "Vestland"
                        }
                    ],
                    "_warning_type": "landslide"
                }
                all_warnings.append(test_alert)
                _LOGGER.info("Test mode: Injected fake orange landslide alert for Testville")
            
            # Fetch landslide warnings
            if self.warning_type in [WARNING_TYPE_LANDSLIDE, WARNING_TYPE_BOTH]:
                landslide_warnings = await self._fetch_warnings(API_BASE_LANDSLIDE, "landslide")
                for warning in landslide_warnings:
                    warning["_warning_type"] = "landslide"
                all_warnings.extend(landslide_warnings)
            
            # Fetch flood warnings
            if self.warning_type in [WARNING_TYPE_FLOOD, WARNING_TYPE_BOTH]:
                flood_warnings = await self._fetch_warnings(API_BASE_FLOOD, "flood")
                for warning in flood_warnings:
                    warning["_warning_type"] = "flood"
                all_warnings.extend(flood_warnings)
            
            _LOGGER.info("Total warnings fetched: %d", len(all_warnings))
            return all_warnings
            
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")


class VarsomAlertsSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Varsom Alerts sensor with all alerts in attributes."""

    def __init__(self, coordinator: VarsomAlertsCoordinator, entry_id: str, county_name: str, warning_type: str, municipality_filter: str = "", is_main: bool = True):
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        # Create sensor name based on warning type
        warning_type_label = warning_type.replace("_", " ").title()
        
        if is_main:
            # Main sensor shows all county alerts
            self._attr_name = f"Varsom {warning_type_label} {county_name}"
            self._attr_unique_id = f"{entry_id}_alerts"
            self._use_filter = False
        else:
            # Filtered sensor shows only selected municipalities
            self._attr_name = f"Varsom {warning_type_label} My Area"
            self._attr_unique_id = f"{entry_id}_alerts_filtered"
            self._use_filter = True
        
        self._attr_has_entity_name = False
        self._county_name = county_name
        self._warning_type = warning_type
        self._municipality_filter = municipality_filter.strip()
        self._is_main = is_main
    
    def _filter_alerts(self, alerts):
        """Filter alerts by municipality if filter is set."""
        if not self._municipality_filter:
            _LOGGER.debug("No municipality filter set, returning all %d alerts", len(alerts))
            return alerts
        
        _LOGGER.info("Filtering %d alerts with municipality filter: '%s'", len(alerts), self._municipality_filter)
        
        # Split filter by comma for multiple municipalities
        filter_terms = [term.strip().lower() for term in self._municipality_filter.split(",")]
        _LOGGER.debug("Filter terms: %s", filter_terms)
        
        filtered = []
        for alert in alerts:
            municipalities = alert.get("MunicipalityList", [])
            muni_names = [m.get("Name", "").lower() for m in municipalities]
            
            _LOGGER.debug("Checking alert ID %s with municipalities: %s", alert.get("Id"), muni_names)
            
            # Check if any municipality matches any filter term
            matches = False
            for filter_term in filter_terms:
                for muni_name in muni_names:
                    if filter_term in muni_name:
                        matches = True
                        _LOGGER.debug("  -> MATCH: '%s' in '%s'", filter_term, muni_name)
                        break
                if matches:
                    break
            
            if matches:
                filtered.append(alert)
            else:
                _LOGGER.debug("  -> NO MATCH for alert ID %s", alert.get("Id"))
        
        _LOGGER.info("Filtered to %d alerts matching '%s'", len(filtered), self._municipality_filter)
        return filtered

    @property
    def native_value(self):
        """Return the state of the sensor (highest activity level)."""
        if not self.coordinator.data:
            return "1"  # Green - no alerts
        
        # Apply municipality filter if this is the filtered sensor
        data_to_use = self._filter_alerts(self.coordinator.data) if self._use_filter else self.coordinator.data
        
        # Filter out green level (1) and unknown level (0) alerts
        active_alerts = [
            alert for alert in data_to_use
            if alert.get("ActivityLevel", "1") not in ("0", "1")
        ]
        
        if not active_alerts:
            return "1"  # Green - no active warnings
        
        # Find highest activity level
        max_level = max(int(alert.get("ActivityLevel", "1")) for alert in active_alerts)
        return str(max_level)

    @property
    def extra_state_attributes(self):
        """Return the state attributes with all alerts."""
        if not self.coordinator.data:
            return {
                "active_alerts": 0,
                "highest_level": "green",
                "highest_level_numeric": 1,
                "alerts": [],
                "county_name": self._county_name,
                "county_id": self.coordinator.county_id,
                "municipality_filter": self._municipality_filter if self._use_filter else None,
            }
        
        # Apply municipality filter if this is the filtered sensor
        data_to_use = self._filter_alerts(self.coordinator.data) if self._use_filter else self.coordinator.data
        
        # Filter out green level (1) and unknown level (0) alerts
        active_alerts = [
            alert for alert in data_to_use
            if alert.get("ActivityLevel", "1") not in ("0", "1")
        ]
        
        # Determine highest level
        if active_alerts:
            max_level = max(int(alert.get("ActivityLevel", "1")) for alert in active_alerts)
        else:
            max_level = 1
        
        # Build alerts array - deduplicate by master_id to avoid showing same warning multiple times
        alerts_dict = {}  # Use dict with master_id as key to deduplicate
        
        for alert in active_alerts:
            # NVE API may have multiple ID fields - try to find the correct one for Varsom.no URL
            forecast_id = alert.get("Id", "")
            master_id = alert.get("MasterId", "")
            reg_obs_id = alert.get("RegObsId", "")
            
            # Log ID fields for debugging URL issues
            _LOGGER.debug(
                "Alert IDs - Id: %s, MasterId: %s, RegObsId: %s", 
                forecast_id, master_id, reg_obs_id
            )
            
            # Use MasterId if available, otherwise fall back to Id
            # MasterId appears to be the correct ID for Varsom.no URLs
            url_id = master_id if master_id else forecast_id
            
            activity_level = alert.get("ActivityLevel", "1")
            
            # Construct varsom.no URL - path differs by language
            if self.coordinator.lang == "en":
                varsom_url = f"https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/{url_id}" if url_id else None
            else:
                varsom_url = f"https://www.varsom.no/flom-og-jordskred/varsling/varselid/{url_id}" if url_id else None
            
            # Get municipality list
            municipalities = [m.get("Name", "") for m in alert.get("MunicipalityList", [])]
            
            # Check if we already have an alert with this master_id
            if url_id in alerts_dict:
                # Merge municipality lists (avoid duplicates)
                existing_munis = set(alerts_dict[url_id]["municipalities"])
                existing_munis.update(municipalities)
                alerts_dict[url_id]["municipalities"] = sorted(list(existing_munis))
                _LOGGER.debug("Merged duplicate alert %s, municipalities now: %s", url_id, alerts_dict[url_id]["municipalities"])
            else:
                # New alert - add to dict
                alert_dict = {
                    "id": forecast_id,
                    "master_id": master_id,
                    "level": int(activity_level),
                    "level_name": ACTIVITY_LEVEL_NAMES.get(activity_level, "unknown"),
                    "danger_type": alert.get("DangerTypeName", ""),
                    "warning_type": alert.get("_warning_type", "unknown"),
                    "municipalities": municipalities,
                    "valid_from": alert.get("ValidFrom", ""),
                    "valid_to": alert.get("ValidTo", ""),
                    "danger_increases": alert.get("DangerIncreaseDateTime"),
                    "danger_decreases": alert.get("DangerDecreaseDateTime"),
                    "main_text": alert.get("MainText", ""),
                    "warning_text": alert.get("WarningText", ""),
                    "advice_text": alert.get("AdviceText", ""),
                    "consequence_text": alert.get("ConsequenceText", ""),
                    "url": varsom_url,
                }
                alerts_dict[url_id] = alert_dict
        
        # Convert dict back to list
        alerts_list = list(alerts_dict.values())
        
        # Sort by level (highest first), then by valid_from
        alerts_list.sort(key=lambda x: (x["level"], x.get("valid_from", "")), reverse=True)
        
        return {
            "active_alerts": len(alerts_list),
            "highest_level": ACTIVITY_LEVEL_NAMES.get(str(max_level), "green"),
            "highest_level_numeric": max_level,
            "alerts": alerts_list,
            "county_name": self._county_name,
            "county_id": self.coordinator.county_id,
            "municipality_filter": self._municipality_filter if self._use_filter else None,
        }

    @property
    def entity_picture(self):
        """Return embedded Yr.no warning icon based on warning type and level."""
        state = self.native_value
        
        # Determine warning type from coordinator data
        warning_type = None
        if self.coordinator.data:
            for alert in self.coordinator.data:
                alert_warning_type = alert.get("_warning_type", "")
                if alert_warning_type:
                    warning_type = alert_warning_type
                    break
        
        # Map level to color
        level_color = ACTIVITY_LEVEL_NAMES.get(state)
        
        if not level_color or level_color == "green" or not warning_type:
            return None
        
        # Get base64 encoded SVG from const
        icon_key = f"{warning_type}-{level_color}"
        return ICON_DATA_URLS.get(icon_key)
