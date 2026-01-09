"""Varsom Alerts sensor platform."""
import logging
from datetime import timedelta

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
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_WARNING_TYPE,
    CONF_MUNICIPALITY_FILTER,
    CONF_TEST_MODE,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NOTIFICATION_SEVERITY,
    WARNING_TYPE_LANDSLIDE,
    WARNING_TYPE_FLOOD,
    WARNING_TYPE_AVALANCHE,
    WARNING_TYPE_METALERTS,
    ACTIVITY_LEVEL_NAMES,
    ICON_DATA_URLS,
    NOTIFICATION_SEVERITY_ALL,
    NOTIFICATION_SEVERITY_YELLOW_PLUS,
    NOTIFICATION_SEVERITY_ORANGE_PLUS,
    NOTIFICATION_SEVERITY_RED_ONLY,
)
from .api import WarningAPIFactory

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Varsom Alerts sensor from a config entry."""
    # Get coordinator from hass.data (created in __init__.py)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.debug("Setting up sensor for entry %s", entry.entry_id)
    
    # Get config from entry.options (preferred) or entry.data (fallback)
    config = entry.options if entry.options else entry.data
    
    warning_type = config.get(CONF_WARNING_TYPE) or entry.data.get(CONF_WARNING_TYPE)
    municipality_filter = config.get(CONF_MUNICIPALITY_FILTER, "")
    
    # Determine if this is a county-based or lat/lon-based configuration
    county_id = config.get(CONF_COUNTY_ID) or entry.data.get(CONF_COUNTY_ID)
    latitude = config.get(CONF_LATITUDE) or entry.data.get(CONF_LATITUDE)
    longitude = config.get(CONF_LONGITUDE) or entry.data.get(CONF_LONGITUDE)
    
    if county_id:
        # County-based configuration (NVE warnings)
        county_name = config.get(CONF_COUNTY_NAME) or entry.data.get(CONF_COUNTY_NAME, "Unknown")
        
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
    else:
        # Lat/lon-based configuration (Met.no metalerts)
        # Create a descriptive location name
        location_name = f"({latitude:.2f}, {longitude:.2f})"
        entities = [
            VarsomAlertsSensor(coordinator, entry.entry_id, location_name, warning_type, "", is_main=True),
        ]
    
    async_add_entities(entities)


class VarsomAlertsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Varsom Alerts data."""

    def __init__(self, hass, county_id, county_name, warning_type, lang, test_mode=False, 
                 enable_notifications=False, notification_severity=NOTIFICATION_SEVERITY_YELLOW_PLUS,
                 latitude=None, longitude=None):
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
        self.enable_notifications = enable_notifications
        self.notification_severity = notification_severity
        self.latitude = latitude
        self.longitude = longitude
        self.previous_alerts = {}  # Track previous alerts for change detection

    # Old _fetch_warnings method removed - replaced by API classes

    # Old _fetch_avalanche_warnings method removed - replaced by AvalancheAPI class

    async def _async_update_data(self):
        """Fetch data from API using the API factory."""
        all_warnings = []
        
        try:
            # Inject test alert if test mode is enabled
            if self.test_mode:
                # Determine primary warning type for test alert
                test_warning_type = self.warning_type  # Use configured type directly
                
                # Create warning type specific content
                if test_warning_type == WARNING_TYPE_FLOOD:
                    danger_type_name = "Flom"
                    main_text = "Test Alert - Orange Flood Warning for Testville"
                    warning_text = "Det er moderat fare for flom i Testville kommune. Nedbør og snøsmelting kan føre til oversvømmelse."
                    advice_text = "Unngå opphold i flomfarlige områder. Vær særlig oppmerksom ved ferdsel nær bekker og elver."
                    consequence_text = "Flom kan medføre skade på bygninger og infrastruktur. Veier kan bli stengt på grunn av flom."
                    emergency_text = "Test emergency warning text for Testville flood alert"
                elif test_warning_type == WARNING_TYPE_AVALANCHE:
                    danger_type_name = "Skredfare" 
                    main_text = "Test Alert - Orange Avalanche Warning for Testville"
                    warning_text = "Det er moderat fare for snøskred i Testville kommune. Værforhold kan utløse skred i bratte områder."
                    advice_text = "Unngå skredfarlige områder. Vær særlig forsiktig i bratt terreng over tregrensen."
                    consequence_text = "Snøskred kan medføre alvorlig fare for liv og helse. Transportruter kan bli stengt."
                    emergency_text = "Test emergency warning text for Testville avalanche alert"
                elif test_warning_type == WARNING_TYPE_METALERTS:
                    danger_type_name = "Wind"
                    main_text = "Orange wind warning"
                    warning_text = "Strong winds expected with gusts up to 25 m/s. This may cause damage to infrastructure and disrupt outdoor activities."
                    advice_text = "Secure loose objects. Avoid unnecessary travel. Stay informed about weather updates."
                    consequence_text = "Damage to infrastructure possible. Travel disruptions expected. Outdoor activities hazardous."
                    emergency_text = "Test emergency weather warning"
                else:  # landslide
                    danger_type_name = "Jordskred"
                    main_text = "Test Alert - Orange Landslide Warning for Testville"
                    warning_text = "Det er moderat fare for jordskred i Testville kommune. Væte og temperaturendringer kan utløse skred i bratte skråninger."
                    advice_text = "Unngå opphold under bratte fjellsider og i skredfarlige områder. Vær særlig oppmerksom ved ferdsel i terrenget."
                    consequence_text = "Jordskred kan medføre skade på infrastruktur og fare for liv og helse. Mindre veier kan bli stengt."
                    emergency_text = "Test emergency warning text for Testville landslide alert"
                
                # Create base test alert structure
                # For metalerts, use the actual event type (wind) not the generic "metalerts"
                # For avalanche, use plural "avalanches" to match icon naming
                if test_warning_type == WARNING_TYPE_METALERTS:
                    warning_type_for_icon = "wind"
                elif test_warning_type == WARNING_TYPE_AVALANCHE:
                    warning_type_for_icon = "avalanches"
                else:
                    warning_type_for_icon = test_warning_type
                
                test_alert = {
                    "Id": 999999,
                    "ActivityLevel": "3",  # Orange
                    "DangerLevel": "Moderate", 
                    "DangerTypeName": danger_type_name,
                    "MainText": main_text, 
                    "_warning_type": warning_type_for_icon
                }
                
                # Add type-specific fields
                if test_warning_type == WARNING_TYPE_METALERTS:
                    # Metalerts (CAP format) - coordinate-based
                    test_alert.update({
                        "ValidFrom": "2025-12-19T00:00:00+01:00",
                        "ValidTo": "2025-12-20T23:59:59+01:00",
                        "PublishTime": "",  # Not provided by metalerts
                        "RegionName": "Vestland, Bergen",
                        # CAP-specific fields matching met_alerts integration
                        "title": "Orange wind warning 2025-12-19T00:00:00+01:00, 2025-12-20T23:59:59+01:00",
                        "starttime": "2025-12-19T00:00:00+01:00",
                        "endtime": "2025-12-20T23:59:59+01:00",
                        "event": "Wind",
                        "event_awareness_name": "orange; wind",
                        "description": warning_text,
                        "instruction": advice_text,
                        "consequences": consequence_text,
                        "certainty": "Likely",
                        "severity": "Moderate",
                        "awareness_level": "3; orange; Moderate",
                        "awareness_level_numeric": "3",
                        "awareness_level_color": "orange",
                        "awareness_level_name": "Moderate",
                        "awareness_type": "2; wind",
                        "contact": "Norwegian Meteorological Institute",
                        "county": ["Vestland"],
                        "area": "Vestland, Bergen",
                        "geographic_domain": "land",
                        "risk_matrix_color": "orange",
                        "trigger_level": "moderate",
                        "ceiling": None,
                        "resources": [
                            {
                                "uri": "https://www.met.no/vaer-og-klima/ekstremvaervarsler-og-andre-faremeldinger",
                                "mimeType": "text/html"
                            }
                        ],
                        "resource_url": "https://www.met.no/vaer-og-klima/ekstremvaervarsler-og-andre-faremeldinger",
                        "map_url": None,
                        "web": "https://www.met.no",
                    })
                else:
                    # NVE warnings (landslide, flood, avalanche) - county-based
                    test_alert.update({
                        "WarningText": warning_text,
                        "AdviceText": advice_text,
                        "ConsequenceText": consequence_text,
                        "EmergencyWarning": emergency_text,
                        "LangKey": 2,
                        "ValidFrom": "2025-12-19T00:00:00",
                        "ValidTo": "2025-12-20T23:59:59", 
                        "NextWarningTime": "2025-12-20T08:00:00",
                        "PublishTime": "2025-12-19T08:00:00",
                        "DangerIncreaseDateTime": "2025-12-19T12:00:00",
                        "DangerDecreaseDateTime": "2025-12-20T06:00:00",
                        "Author": "Test System",
                        "MunicipalityList": [
                            {
                                "Id": "9999", 
                                "Name": "Testville",
                                "CountyId": "46",
                                "CountyName": "Vestland"
                            }
                        ],
                    })
                
                all_warnings.append(test_alert)
                _LOGGER.info("Test mode: Injected fake orange %s alert", test_warning_type)
            
            # Use API factory to get appropriate API client and fetch warnings
            api_factory = WarningAPIFactory(
                county_id=self.county_id, 
                county_name=self.county_name, 
                latitude=self.latitude,
                longitude=self.longitude,
                lang=self.lang
            )
            
            # Fetch warnings for the configured warning type
            api_client = api_factory.get_api(self.warning_type)
            warnings = await api_client.fetch_warnings()
            all_warnings.extend(warnings)
            _LOGGER.info("Fetched %d %s warnings", len(warnings), self.warning_type)
            
            _LOGGER.info("Total warnings fetched: %d", len(all_warnings))
            
            # Debug: log warning types breakdown
            warning_types_count = {}
            for warning in all_warnings:
                wtype = warning.get("_warning_type", "unknown")
                warning_types_count[wtype] = warning_types_count.get(wtype, 0) + 1
            _LOGGER.info("Warning types breakdown: %s", warning_types_count)
            
            # Send notifications if enabled
            if self.enable_notifications:
                await self._send_notifications(all_warnings)
            
            return all_warnings
            
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    async def _send_notifications(self, current_alerts):
        """Send notifications for new or changed alerts."""
        try:
            # Create a dictionary of current alerts by ID and activity level
            current_alert_states = {}
            for alert in current_alerts:
                alert_id = str(alert.get("Id", "unknown"))
                activity_level = str(alert.get("ActivityLevel", "1"))
                warning_type = alert.get("_warning_type", "unknown")
                region_name = alert.get("RegionName") or alert.get("MunicipalityName", "Unknown area")
                current_alert_states[alert_id] = {
                    "activity_level": activity_level,
                    "warning_type": warning_type,
                    "region_name": region_name,
                    "alert": alert
                }
            
            # Check for new or upgraded alerts
            notifications_sent = []
            
            for alert_id, alert_info in current_alert_states.items():
                activity_level = alert_info["activity_level"]
                warning_type = alert_info["warning_type"]
                region_name = alert_info["region_name"]
                alert = alert_info["alert"]
                
                # Check if this alert meets notification severity threshold
                if not self._should_notify(activity_level):
                    continue
                
                # Check if this is a new alert or severity increase
                previous_alert = self.previous_alerts.get(alert_id)
                
                if previous_alert is None:
                    # New alert
                    await self._send_alert_notification(alert, "New", warning_type, region_name, activity_level)
                    notifications_sent.append(f"New {warning_type} alert: {region_name}")
                    
                elif int(activity_level) > int(previous_alert["activity_level"]):
                    # Severity increased
                    await self._send_alert_notification(alert, "Upgraded", warning_type, region_name, activity_level)
                    notifications_sent.append(f"Upgraded {warning_type} alert: {region_name}")
            
            # Check for resolved alerts (present in previous but not current)
            for prev_alert_id, prev_alert_info in self.previous_alerts.items():
                if prev_alert_id not in current_alert_states:
                    # Alert resolved
                    prev_warning_type = prev_alert_info["warning_type"]
                    prev_region_name = prev_alert_info["region_name"]
                    await self._send_resolved_notification(prev_warning_type, prev_region_name)
                    notifications_sent.append(f"Resolved {prev_warning_type} alert: {prev_region_name}")
            
            # Update previous alerts state
            self.previous_alerts = current_alert_states.copy()
            
            if notifications_sent:
                _LOGGER.info("Sent %d notifications: %s", len(notifications_sent), notifications_sent)
                
        except Exception as err:
            _LOGGER.error("Error sending notifications: %s", err)

    def _should_notify(self, activity_level: str) -> bool:
        """Check if this activity level should trigger a notification."""
        try:
            level_int = int(activity_level)
            
            if self.notification_severity == NOTIFICATION_SEVERITY_ALL:
                return level_int >= 1
            elif self.notification_severity == NOTIFICATION_SEVERITY_YELLOW_PLUS:
                return level_int >= 2
            elif self.notification_severity == NOTIFICATION_SEVERITY_ORANGE_PLUS:
                return level_int >= 3  
            elif self.notification_severity == NOTIFICATION_SEVERITY_RED_ONLY:
                return level_int >= 4
            
            return False
        except (ValueError, TypeError):
            return False

    async def _send_alert_notification(self, alert, status, warning_type, region_name, activity_level):
        """Send a notification for a new or upgraded alert."""
        try:
            # Get activity level name and emoji
            level_name = ACTIVITY_LEVEL_NAMES.get(activity_level, "unknown")
            level_emoji = {"1": "🟢", "2": "🟡", "3": "🟠", "4": "🔴", "5": "⚫"}.get(activity_level, "⚪")
            
            # Format warning type nicely
            warning_type_display = warning_type.replace("_", " ").title()
            
            # Create notification title and message
            title = f"{level_emoji} {status} {warning_type_display} Warning"
            
            main_text = alert.get("MainText", "")
            if len(main_text) > 100:
                main_text = main_text[:97] + "..."
            
            message = f"{region_name} - {level_name.title()} danger level"
            if main_text:
                message += f"\n\n{main_text}"
            
            # Send persistent notification to Home Assistant
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": f"varsom_{self.county_id}_{warning_type}_{alert.get('Id', 'unknown')}",
                },
                blocking=False,
            )
            
        except Exception as err:
            _LOGGER.error("Error sending alert notification: %s", err)

    async def _send_resolved_notification(self, warning_type, region_name):
        """Send a notification for a resolved alert."""
        try:
            warning_type_display = warning_type.replace("_", " ").title()
            
            title = f"✅ Resolved {warning_type_display} Warning"
            message = f"{region_name} - Warning no longer active"
            
            # Send persistent notification
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": f"varsom_resolved_{self.county_id}_{warning_type}_{region_name}",
                },
                blocking=False,
            )
            
        except Exception as err:
            _LOGGER.error("Error sending resolved notification: %s", err)


class VarsomAlertsSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Varsom Alerts sensor with all alerts in attributes."""

    def __init__(self, coordinator: VarsomAlertsCoordinator, entry_id: str, county_name: str, warning_type: str, municipality_filter: str = "", is_main: bool = True):
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        # Create sensor name based on warning type
        warning_type_label = warning_type.replace("_", " ").title()
        
        if is_main:
            # Main sensor shows all alerts for the location
            self._attr_name = f"Norway Alerts {warning_type_label} {county_name}"
            self._attr_unique_id = f"{entry_id}_alerts"
            self._use_filter = False
        else:
            # Filtered sensor shows only selected municipalities
            self._attr_name = f"Norway Alerts {warning_type_label} My Area"
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
            base_attrs = {
                "active_alerts": 0,
                "highest_level": "green",
                "highest_level_numeric": 1,
                "alerts": [],
            }
            
            # Add location-specific attributes
            if self.coordinator.county_id:
                # County-based (NVE) attributes
                base_attrs.update({
                    "county_name": self._county_name,
                    "county_id": self.coordinator.county_id,
                    "municipality_filter": self._municipality_filter if self._use_filter else None,
                })
            else:
                # Coordinate-based (Met.no) attributes
                base_attrs.update({
                    "latitude": self.coordinator.latitude,
                    "longitude": self.coordinator.longitude,
                })
            
            return base_attrs
        
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
            
            # Construct varsom.no URL - different structure for different warning types
            warning_type = alert.get("_warning_type", "")
            
            if warning_type == "avalanche":
                # Avalanche warnings - link to general avalanche page since specific region URLs don't exist
                # Could potentially use UTM coordinates for mapping in the future
                if self.coordinator.lang == "en":
                    varsom_url = "https://www.varsom.no/en/avalanche-bulletins"  
                else:
                    varsom_url = "https://www.varsom.no/snoskredvarsling"
            else:
                # Landslide/flood warnings use forecast-based URLs
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
                # Generate individual icon for this alert
                level_color = ACTIVITY_LEVEL_NAMES.get(activity_level, "green")
                if warning_type and level_color != "green":
                    icon_key = f"{warning_type}-{level_color}"
                    # Try to get icon, fall back to generic if not found
                    individual_icon = ICON_DATA_URLS.get(icon_key)
                    if not individual_icon:
                        generic_key = f"generic-{level_color}"
                        individual_icon = ICON_DATA_URLS.get(generic_key)
                        _LOGGER.debug("Icon not found for %s, using %s", icon_key, generic_key)
                else:
                    individual_icon = None
                
                # New alert - create base dict with common fields only
                alert_dict = {
                    "id": forecast_id,
                    "level": int(activity_level),
                    "level_name": ACTIVITY_LEVEL_NAMES.get(activity_level, "unknown"),
                    "danger_type": alert.get("DangerTypeName", ""),
                    "warning_type": alert.get("_warning_type", "unknown"),
                    "valid_from": alert.get("ValidFrom", ""),
                    "valid_to": alert.get("ValidTo", ""),
                    "main_text": alert.get("MainText", ""),
                    "entity_picture": individual_icon,
                }
                
                # Add warning-type-specific attributes
                if warning_type == "metalerts":
                    # Met.no weather alerts - use CAP-based fields
                    alert_dict.update({
                        "title": alert.get("title", ""),
                        "event": alert.get("event", ""),
                        "event_type": alert.get("event", "").lower().replace(" ", "_") if alert.get("event") else "",
                        "areas": alert.get("area", "").split(", ") if alert.get("area") else [],
                        "description": alert.get("description", ""),
                        "instruction": alert.get("instruction", ""),
                        "consequences": alert.get("consequences", ""),
                        "certainty": alert.get("certainty", ""),
                        "severity": alert.get("severity", ""),
                        "awareness_level": alert.get("awareness_level", ""),
                        "awareness_level_numeric": alert.get("awareness_level_numeric", ""),
                        "awareness_level_color": alert.get("awareness_level_color", ""),
                        "awareness_level_name": alert.get("awareness_level_name", ""),
                        "awareness_type": alert.get("awareness_type", ""),
                        "event_awareness_name": alert.get("event_awareness_name", ""),
                        "contact": alert.get("contact", ""),
                        "county": alert.get("county", []),
                        "starttime": alert.get("starttime", ""),
                        "endtime": alert.get("endtime", ""),
                        "resources": alert.get("resources", []),
                        "map_url": alert.get("map_url"),
                        "resource_url": alert.get("resource_url", ""),
                        "web": alert.get("web", ""),
                        "geographic_domain": alert.get("geographic_domain", ""),
                        "risk_matrix_color": alert.get("risk_matrix_color", ""),
                        "trigger_level": alert.get("trigger_level"),
                        "ceiling": alert.get("ceiling"),
                    })
                    # Override URL for Met.no alerts
                    alert_dict["url"] = alert.get("resource_url") or "https://www.met.no/vaer-og-klima/ekstremvaervarsler-og-andre-faremeldinger"
                elif warning_type == "avalanches":
                    # Avalanche warnings - NVE specific fields
                    alert_dict.update({
                        # NVE common fields
                        "master_id": master_id,
                        "municipalities": municipalities,
                        "danger_increases": alert.get("DangerIncreaseDateTime"),
                        "danger_decreases": alert.get("DangerDecreaseDateTime"),
                        "url": varsom_url,
                        
                        # Geographical data
                        "region_id": alert.get("_region_id", alert.get("RegionId")),
                        "region_name": alert.get("_region_name", alert.get("RegionName")),
                        "utm_zone": alert.get("UtmZone"),
                        "utm_east": alert.get("UtmEast"),
                        "utm_north": alert.get("UtmNorth"),
                        
                        # Avalanche-specific information (instead of warning_text/advice_text/consequence_text)
                        "avalanche_danger": alert.get("AvalancheDanger", ""),
                        "emergency_warning": alert.get("EmergencyWarning", ""),
                        "avalanche_problems": alert.get("AvalancheProblems", []),
                        "avalanche_advices": alert.get("AvalancheAdvices", []),
                        "snow_surface": alert.get("SnowSurface", ""),
                        "current_weaklayers": alert.get("CurrentWeaklayers", ""),
                        "latest_avalanche_activity": alert.get("LatestAvalancheActivity", ""),
                        "latest_observations": alert.get("LatestObservations", ""),
                        "forecaster": alert.get("Author", ""),
                        "danger_level_name": alert.get("DangerLevelName", ""),
                        "exposed_height": alert.get("ExposedHeight1", alert.get("ExposedHeightFill", 0)),
                        
                        # Simplified weather fields for easy template access
                        "wind_speed": alert.get("WindSpeed", ""),
                        "wind_direction": alert.get("WindDirection", ""),
                        "temperature": alert.get("Temperature", ""),
                        "precipitation": alert.get("Precipitation", ""),
                        "mountain_weather": alert.get("MountainWeather", {}),  # Keep complex structure too
                    })
                else:
                    # Landslide and flood warnings - NVE generic attributes
                    alert_dict.update({
                        # NVE common fields
                        "master_id": master_id,
                        "municipalities": municipalities,
                        "danger_increases": alert.get("DangerIncreaseDateTime"),
                        "danger_decreases": alert.get("DangerDecreaseDateTime"),
                        "url": varsom_url,
                        
                        # Generic warning fields
                        "warning_text": alert.get("WarningText", ""),
                        "advice_text": alert.get("AdviceText", ""),
                        "consequence_text": alert.get("ConsequenceText", ""),
                    })
                alerts_dict[url_id] = alert_dict
        
        # Convert dict back to list
        alerts_list = list(alerts_dict.values())
        
        # Sort by level (highest first), then by valid_from
        alerts_list.sort(key=lambda x: (x["level"], x.get("valid_from", "")), reverse=True)
        
        result = {
            "active_alerts": len(alerts_list),
            "highest_level": ACTIVITY_LEVEL_NAMES.get(str(max_level), "green"),
            "highest_level_numeric": max_level,
            "alerts": alerts_list,
        }
        
        # Add location-specific attributes
        if self.coordinator.county_id:
            # County-based (NVE) attributes
            result.update({
                "county_name": self._county_name,
                "county_id": self.coordinator.county_id,
                "municipality_filter": self._municipality_filter if self._use_filter else None,
            })
        else:
            # Coordinate-based (Met.no) attributes
            result.update({
                "latitude": self.coordinator.latitude,
                "longitude": self.coordinator.longitude,
            })
        
        return result

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
        icon = ICON_DATA_URLS.get(icon_key)
        
        # Fall back to generic icon if specific type not found
        if not icon:
            generic_key = f"generic-{level_color}"
            icon = ICON_DATA_URLS.get(generic_key)
            _LOGGER.debug("Icon not found for %s, using %s", icon_key, generic_key)
        
        return icon
