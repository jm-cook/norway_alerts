"""API client classes for different warning types."""

import asyncio
import datetime as dt
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

import aiohttp

from .const import (
    API_BASE_LANDSLIDE, 
    API_BASE_FLOOD, 
    API_BASE_AVALANCHE
)

_LOGGER = logging.getLogger(__name__)


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
            "User-Agent": "varsom/1.0.0 jeremy.m.cook@gmail.com"
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
                                                        "_warning_type": "avalanche",
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
                                                        "MountainWeather": warning.get("MountainWeather", {}),
                                                        "Author": warning.get("Author", ""),
                                                        "DangerLevelName": warning.get("DangerLevelName", ""),
                                                        "ExposedHeightFill": warning.get("ExposedHeightFill", 0),
                                                        "ExposedHeight1": warning.get("ExposedHeight1", 0),
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


class WarningAPIFactory:
    """Factory for creating warning API clients."""
    
    def __init__(self, county_id: str, county_name: str, lang: str = "en"):
        self.county_id = county_id
        self.county_name = county_name
        self.lang = lang
    
    def get_api(self, warning_type: str) -> BaseWarningAPI:
        """Create appropriate API client for warning type."""
        if warning_type == "landslide":
            return LandslideAPI(self.county_id, self.county_name, self.lang)
        elif warning_type == "flood":
            return FloodAPI(self.county_id, self.county_name, self.lang)
        elif warning_type == "avalanche":
            return AvalancheAPI(self.county_id, self.county_name, self.lang)
        else:
            raise ValueError(f"Unknown warning type: {warning_type}")
    
    @staticmethod
    def create_api(warning_type: str, county_id: str, county_name: str, lang: str = "en") -> BaseWarningAPI:
        """Create appropriate API client for warning type (static method)."""
        if warning_type == "landslide":
            return LandslideAPI(county_id, county_name, lang)
        elif warning_type == "flood":
            return FloodAPI(county_id, county_name, lang)
        elif warning_type == "avalanche":
            return AvalancheAPI(county_id, county_name, lang)
        else:
            raise ValueError(f"Unknown warning type: {warning_type}")