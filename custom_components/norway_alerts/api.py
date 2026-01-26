"""API client classes for different warning types."""

import asyncio
import datetime as dt
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any

import aiohttp

from .const import (
    API_BASE_LANDSLIDE, 
    API_BASE_FLOOD, 
    API_BASE_AVALANCHE,
    API_BASE_METALERTS
)

_LOGGER = logging.getLogger(__name__)


def _load_version_from_manifest() -> str:
    """Load version from manifest.json at module import time."""
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            return manifest.get("version", "2.0.0")
    except Exception as e:
        _LOGGER.warning("Could not read version from manifest.json: %s", e)
        return "2.0.0"


# Load version at module import time (before event loop starts)
_VERSION = _load_version_from_manifest()


def _get_user_agent() -> str:
    """Get User-Agent string with version from manifest."""
    return f"norway_alerts/{_VERSION} jeremy.m.cook@gmail.com"


class BaseWarningAPI(ABC):
    """Base class for warning API clients."""
    
    def __init__(self, county_id: str, county_name: str, lang: str = "en"):
        self.county_id = county_id
        self.county_name = county_name
        self.lang = lang
        self.warning_type = self._get_warning_type()
    
    @abstractmethod
    def _get_warning_type(self) -> str:
        """Return the warning type identifier."""
        pass
    
    @abstractmethod
    async def fetch_warnings(self) -> List[Dict[str, Any]]:
        """Fetch warnings from the API."""
        pass


class CountyBasedAPI(BaseWarningAPI):
    """Base class for county-based APIs (landslide/flood)."""
    
    async def _fetch_county_warnings(self, base_url: str, warning_type: str) -> List[Dict[str, Any]]:
        """Fetch warnings using county-based API."""
        lang_key = "2" if self.lang == "en" else "1"
        url = f"{base_url}/Warning/County/{self.county_id}/{lang_key}"
        
        headers = {
            "Accept": "application/json",
            "User-Agent": _get_user_agent()
        }
        
        _LOGGER.debug("Fetching %s warnings from: %s", warning_type, url)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with asyncio.timeout(10):
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            _LOGGER.error("Error fetching %s data: %s", warning_type, response.status)
                            return []

                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            json_data = await response.json()
                            if json_data:
                                _LOGGER.info("Successfully fetched %s warnings (count: %d)", warning_type, len(json_data))
                                return json_data
                            else:
                                _LOGGER.info("No %s warnings found", warning_type)
                                return []
                        else:
                            _LOGGER.error("Unexpected content type for %s: %s", warning_type, content_type)
                            return []
                        
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching %s warnings: %s", warning_type, err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error fetching %s warnings: %s", warning_type, err)
            return []


class LandslideAPI(CountyBasedAPI):
    """API client for landslide warnings."""
    
    def _get_warning_type(self) -> str:
        return "landslide"
    
    async def fetch_warnings(self) -> List[Dict[str, Any]]:
        """Fetch landslide warnings from NVE API."""
        warnings = await self._fetch_county_warnings(API_BASE_LANDSLIDE, "landslide")
        # Add warning type to each warning
        for warning in warnings:
            warning["_warning_type"] = "landslide"
        return warnings


class FloodAPI(CountyBasedAPI):
    """API client for flood warnings."""
    
    def _get_warning_type(self) -> str:
        return "flood"
    
    async def fetch_warnings(self) -> List[Dict[str, Any]]:
        """Fetch flood warnings from NVE API."""
        warnings = await self._fetch_county_warnings(API_BASE_FLOOD, "flood")
        # Add warning type to each warning
        for warning in warnings:
            warning["_warning_type"] = "flood"
        return warnings


class AvalancheAPI(BaseWarningAPI):
    """API client for avalanche warnings."""
    
    def _get_warning_type(self) -> str:
        return "avalanche"
    
    def _extract_weather_value(self, warning: Dict[str, Any], measurement_type: str, field: str) -> str:
        """Extract weather values from the complex MountainWeather structure."""
        try:
            mountain_weather = warning.get("MountainWeather", {})
            measurement_types = mountain_weather.get("MeasurementTypes", [])
            
            for measurement in measurement_types:
                if measurement.get("Name", "").lower() == measurement_type.lower():
                    return str(measurement.get(field, ""))
            return ""
        except (KeyError, TypeError, AttributeError):
            return ""
    
    async def fetch_warnings(self) -> List[Dict[str, Any]]:
        """Fetch avalanche warnings from NVE API."""
        try:
            today = dt.datetime.now().strftime("%Y-%m-%d")
            tomorrow = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Language key: 2 = Norwegian, 1 = English  
            summary_url = f"{API_BASE_AVALANCHE}/api/RegionSummary/Simple/2/{today}/{tomorrow}"
            
            _LOGGER.info("Fetching avalanche summary from: %s", summary_url)
            
            async with aiohttp.ClientSession() as session:
                # Get region summary to find active regions
                async with session.get(summary_url) as response:
                    if response.status != 200:
                        _LOGGER.error("Error fetching avalanche warnings summary: HTTP %d", response.status)
                        return []
                    
                    summary_data = await response.json()
                    if not summary_data:
                        _LOGGER.info("No avalanche warnings found")
                        return []
                    
                    # Find regions with active warnings
                    active_regions = []
                    for region in summary_data:
                        if "AvalancheWarningList" in region and region["AvalancheWarningList"]:
                            for warning in region["AvalancheWarningList"]:
                                danger_level = warning.get("DangerLevel", 0)
                                if isinstance(danger_level, str):
                                    danger_level = int(danger_level) if danger_level.isdigit() else 0
                                if danger_level > 0:
                                    active_regions.append(warning.get("RegionId"))
                                    break
                    
                    _LOGGER.debug("Found %d active avalanche regions", len(active_regions))
                    
                    # Get detailed data for active regions
                    warnings = []
                    for region_id in active_regions:
                        detail_url = f"{API_BASE_AVALANCHE}/api/AvalancheWarningByRegion/Detail/{region_id}/2/{today}/{tomorrow}"
                        
                        try:
                            async with session.get(detail_url) as detail_response:
                                if detail_response.status == 200:
                                    detail_data = await detail_response.json()
                                    
                                    if isinstance(detail_data, list):
                                        for warning in detail_data:
                                            danger_level = warning.get("DangerLevel", 0)
                                            if isinstance(danger_level, str):
                                                danger_level = int(danger_level) if danger_level.isdigit() else 0
                                            if danger_level > 0:
                                                # Calculate county relevance score
                                                municipality_list = warning.get("MunicipalityList", [])
                                                county_list = warning.get("CountyList", [])
                                                
                                                # Check if this region has relevance to target county
                                                # First check by county name in CountyList since CountyId is often empty
                                                county_list = warning.get("CountyList", [])
                                                county_names = [county.get("Name", "") for county in county_list]
                                                is_relevant = self.county_name in county_names
                                                
                                                # If not found by county name, fall back to municipality CountyId check
                                                if not is_relevant:
                                                    target_county_municipalities = 0
                                                    total_municipalities = len(municipality_list)
                                                    
                                                    for municipality in municipality_list:
                                                        muni_county_id = municipality.get("CountyId")
                                                        if str(muni_county_id) == str(self.county_id):
                                                            target_county_municipalities += 1
                                                    
                                                    # Calculate relevance score (0.0 to 1.0)
                                                    relevance_score = target_county_municipalities / total_municipalities if total_municipalities > 0 else 0
                                                    
                                                    # Only include regions with some relevance (>= 10% of municipalities)
                                                    is_relevant = relevance_score >= 0.1
                                                
                                                if is_relevant:
                                                    region_name = warning.get("RegionName", "Unknown")
                                                    _LOGGER.debug("Including avalanche region '%s': relevant to %s (county in region or municipalities match)", 
                                                                region_name, self.county_name)
                                                    converted_warning = {
                                                        "Id": warning.get("RegionId"),
                                                        "ActivityLevel": str(warning.get("DangerLevel", 1)),
                                                        "DangerLevel": f"Level {warning.get('DangerLevel', 1)}",
                                                        "DangerTypeName": "Skredfare",
                                                        "MainText": warning.get("MainText", "Snøskredvarsel"),
                                                        "RegionName": warning.get("RegionName", "Ukjent område"),
                                                        "ValidFrom": warning.get("ValidFrom"),
                                                        "ValidTo": warning.get("ValidTo"),
                                                        "PublishTime": warning.get("PublishTime"),
                                                        "CountyList": warning.get("CountyList", []),
                                                        "MunicipalityList": warning.get("MunicipalityList", []),
                                                        "_region_id": warning.get("RegionId"),
                                                        "_region_name": warning.get("RegionName"),
                                                        "_warning_type": "avalanches",  # Plural to match icon naming
                                                        "UtmZone": warning.get("UtmZone"),
                                                        "UtmEast": warning.get("UtmEast"),
                                                        "UtmNorth": warning.get("UtmNorth"),
                                                        
                                                        # Avalanche-specific attributes (instead of generic WarningText/AdviceText/ConsequenceText)
                                                        "AvalancheDanger": warning.get("AvalancheDanger", ""),
                                                        "EmergencyWarning": warning.get("EmergencyWarning", ""),
                                                        "AvalancheProblems": warning.get("AvalancheProblems", []),
                                                        "AvalancheAdvices": warning.get("AvalancheAdvices", []),
                                                        "SnowSurface": warning.get("SnowSurface", ""),
                                                        "CurrentWeaklayers": warning.get("CurrentWeaklayers", ""),
                                                        "LatestAvalancheActivity": warning.get("LatestAvalancheActivity", ""),
                                                        "LatestObservations": warning.get("LatestObservations", ""),
                                                        "Author": warning.get("Author", ""),
                                                        "DangerLevelName": warning.get("DangerLevelName", ""),
                                                        "ExposedHeightFill": warning.get("ExposedHeightFill", 0),
                                                        "ExposedHeight1": warning.get("ExposedHeight1", 0),
                                                        
                                                        # Flattened mountain weather for easy template access
                                                        "WindSpeed": self._extract_weather_value(warning, "wind", "Speed"),
                                                        "WindDirection": self._extract_weather_value(warning, "wind", "Direction"),
                                                        "Temperature": self._extract_weather_value(warning, "temperature", "Value"),
                                                        "Precipitation": self._extract_weather_value(warning, "precipitation", "Value"),
                                                        "MountainWeather": warning.get("MountainWeather", {}),  # Keep raw data too
                                                    }
                                                    warnings.append(converted_warning)
                        except Exception as e:
                            _LOGGER.debug("Error fetching details for region %s: %s", region_id, e)
                            continue
                    
                    _LOGGER.info("Successfully fetched avalanche warnings for %s: %d", self.county_name, len(warnings))
                    return warnings
                        
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching avalanche warnings: %s", err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error fetching avalanche warnings: %s", err)
            return []


# MetAlerts API (originally authored by @kutern84 and @svenove for met_alerts integration)
# Adapted for inclusion in the Norway Alerts integration to unify Norwegian geohazard services
# Original source: https://github.com/kurtern84/met_alerts
# License: MIT (see original repository)
class MetAlertsAPI(BaseWarningAPI):
    """API client for Met.no weather alerts (metalerts).
    
    Original implementation by @kutern84 and @svenove in the met_alerts integration.
    This is an adapted version to integrate metalerts into the Norway Alerts integration,
    unifying all Norwegian geohazard services.
    """
    
    def __init__(self, latitude: float = None, longitude: float = None, county_id: str = None, county_name: str = None, lang: str = "en", test_mode: bool = False):
        """Initialize the MetAlerts API client.
        
        Can operate in two modes:
        1. Location-based: Uses latitude/longitude for geographic filtering
        2. County-based: Uses county_id for administrative filtering
        """
        # Call parent with county values (may be empty for lat/lon mode)
        super().__init__(county_id or "", county_name or "", lang)
        self.latitude = latitude
        self.longitude = longitude
        self.test_mode = test_mode
    
    def _get_warning_type(self) -> str:
        return "metalerts"
    
    def _extract_times_from_title(self, title: str) -> tuple[str, str | None, str | None]:
        """Extract timestamps from alert title.
        
        Original implementation from met_alerts integration by @kutern84 and @svenove.
        """
        import re
        timestamps = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}", title)
        
        if len(timestamps) >= 2:
            starttime = timestamps[0]
            endtime = timestamps[1]
            # Remove the timestamps from the title
            title = title.replace(starttime, "").replace(endtime, "").strip(", ").strip()
            return title, starttime, endtime
        else:
            return title, None, None
    
    async def fetch_warnings(self) -> List[Dict[str, Any]]:
        """Fetch weather alerts from Met.no metalerts API.
        
        Implementation adapted from met_alerts integration by @kutern84 and @svenove.
        Returns alerts converted to the common Norway Alerts warning format.
        """
        # Use test endpoint if in test mode
        if self.test_mode:
            url = f"{API_BASE_METALERTS}/example.json"
            _LOGGER.info("Test mode: Using Met.no example endpoint: %s", url)
        elif self.latitude is not None and self.longitude is not None:
            # Coordinate-based filtering
            url = f"{API_BASE_METALERTS}/current.json?lat={self.latitude}&lon={self.longitude}&lang={self.lang}"
        elif self.county_id:
            # County-based filtering
            url = f"{API_BASE_METALERTS}/current.json?county={self.county_id}&lang={self.lang}"
        else:
            raise ValueError("MetAlerts requires either lat/lon coordinates or county_id")
        
        headers = {
            "Accept": "application/json",
            "User-Agent": _get_user_agent()
        }
        
        _LOGGER.debug("Fetching metalerts from: %s", url)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with asyncio.timeout(10):
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            _LOGGER.error("Error fetching metalerts data: %s", response.status)
                            return []
                        
                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" not in content_type:
                            _LOGGER.error("Unexpected content type for metalerts: %s", content_type)
                            return []
                        
                        json_data = await response.json()
                        if not json_data:
                            _LOGGER.info("No metalerts found")
                            return []
                        
                        features = json_data.get("features", [])
                        _LOGGER.info("Successfully fetched %d metalerts", len(features))
                        
                        # Convert metalerts format to common Norway Alerts warning format
                        warnings = []
                        for feature in features:
                            props = feature.get("properties", {})
                            
                            # Extract basic information
                            title, starttime, endtime = self._extract_times_from_title(props.get("title", ""))
                            
                            # Parse awareness_level (format: "2; orange; Moderate")
                            awareness_level = props.get("awareness_level", "")
                            try:
                                awareness_level_numeric, awareness_level_color, awareness_level_name = awareness_level.split("; ")
                                activity_level = awareness_level_numeric
                            except ValueError:
                                awareness_level_numeric = "1"
                                awareness_level_color = "yellow"
                                awareness_level_name = "Minor"
                                activity_level = "1"
                            
                            # Get resource URL
                            resources = props.get("resources", [])
                            resource_url = ""
                            map_url = None
                            if resources and len(resources) > 0:
                                resource_url = resources[0].get("uri", "")
                                # Extract PNG map URL
                                for resource in resources:
                                    if resource.get("mimeType") == "image/png":
                                        map_url = resource.get("uri")
                                        break
                            
                            # Convert to Norway Alerts warning format
                            # Map event types for icon compatibility
                            event_type = props.get("event", "").lower()
                            # Handle special mappings for icons
                            if event_type == "gale":
                                icon_event_type = "wind"
                            elif event_type == "icing":
                                icon_event_type = "ice"
                            elif event_type == "blowingsnow":
                                icon_event_type = "snow"
                            else:
                                icon_event_type = event_type
                            
                            converted_warning = {
                                "Id": props.get("id", ""),
                                "ActivityLevel": activity_level,
                                "DangerLevel": f"Level {activity_level}",
                                "DangerTypeName": props.get("event", "Weather warning"),
                                "MainText": props.get("description", ""),
                                "RegionName": props.get("area", ""),
                                "ValidFrom": starttime or props.get("eventEndingTime", ""),
                                "ValidTo": endtime or props.get("eventEndingTime", ""),
                                "PublishTime": "",  # Not provided by metalerts
                                "_warning_type": icon_event_type,
                                
                                # Metalerts-specific attributes (preserving original structure)
                                "title": title,
                                "starttime": starttime,
                                "endtime": endtime,
                                "description": props.get("description", ""),
                                "awareness_level": awareness_level,
                                "awareness_level_numeric": awareness_level_numeric,
                                "awareness_level_color": awareness_level_color,
                                "awareness_level_name": awareness_level_name,
                                "certainty": props.get("certainty", ""),
                                "severity": props.get("severity", ""),
                                "instruction": props.get("instruction", ""),
                                "contact": props.get("contact", ""),
                                "resources": resources,
                                "area": props.get("area", ""),
                                "event": props.get("event", ""),
                                "event_awareness_name": props.get("eventAwarenessName", ""),
                                "consequences": props.get("consequences", ""),
                                "map_url": map_url,
                                "resource_url": resource_url,
                                "awareness_type": props.get("awareness_type", ""),
                                "ceiling": props.get("ceiling"),
                                "county": props.get("county", []),
                                "geographic_domain": props.get("geographicDomain", ""),
                                "risk_matrix_color": props.get("riskMatrixColor", ""),
                                "trigger_level": props.get("triggerLevel"),
                                "web": props.get("web", ""),
                            }
                            warnings.append(converted_warning)
                        
                        return warnings
        
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching metalerts: %s", err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error fetching metalerts: %s", err)
            return []


class WarningAPIFactory:
    """Factory for creating warning API clients."""
    
    def __init__(self, county_id: str = "", county_name: str = "", latitude: float = None, longitude: float = None, lang: str = "en", test_mode: bool = False):
        self.county_id = county_id
        self.county_name = county_name
        self.latitude = latitude
        self.longitude = longitude
        self.lang = lang
        self.test_mode = test_mode
    
    def get_api(self, warning_type: str) -> BaseWarningAPI:
        """Create appropriate API client for warning type."""
        if warning_type == "landslide":
            return LandslideAPI(self.county_id, self.county_name, self.lang)
        elif warning_type == "flood":
            return FloodAPI(self.county_id, self.county_name, self.lang)
        elif warning_type == "avalanche":
            return AvalancheAPI(self.county_id, self.county_name, self.lang)
        elif warning_type == "metalerts":
            # MetAlerts (weather) - supports both lat/lon and county
            if self.latitude is not None and self.longitude is not None:
                # Location-based mode
                return MetAlertsAPI(latitude=self.latitude, longitude=self.longitude, lang=self.lang, test_mode=self.test_mode)
            elif self.county_id:
                # County-based mode  
                return MetAlertsAPI(county_id=self.county_id, county_name=self.county_name, lang=self.lang, test_mode=self.test_mode)
            else:
                raise ValueError("MetAlerts requires either lat/lon coordinates or county_id")
        else:
            raise ValueError(f"Unknown warning type: {warning_type}")
    
    @staticmethod
    def create_api(warning_type: str, county_id: str = "", county_name: str = "", latitude: float = None, longitude: float = None, lang: str = "en") -> BaseWarningAPI:
        """Create appropriate API client for warning type (static method)."""
        if warning_type == "landslide":
            return LandslideAPI(county_id, county_name, lang)
        elif warning_type == "flood":
            return FloodAPI(county_id, county_name, lang)
        elif warning_type == "avalanche":
            return AvalancheAPI(county_id, county_name, lang)
        elif warning_type == "metalerts":
            if latitude is None or longitude is None:
                raise ValueError("Latitude and longitude are required for metalerts")
            return MetAlertsAPI(latitude, longitude, lang)
        else:
            raise ValueError(f"Unknown warning type: {warning_type}")