#!/usr/bin/env python3
"""Test the current AvalancheAPI with updated logic."""

import asyncio
import sys
import os

# Add the custom components path to find the API
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_components', 'varsom'))

# We'll need to mock some imports that aren't available outside HA
class MockLogger:
    def info(self, msg, *args): print(f"INFO: {msg % args if args else msg}")
    def debug(self, msg, *args): print(f"DEBUG: {msg % args if args else msg}")
    def error(self, msg, *args): print(f"ERROR: {msg % args if args else msg}")

# Create a mock _LOGGER
_LOGGER = MockLogger()

# Mock the const module
class MockConst:
    API_BASE_AVALANCHE = "https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0"

sys.modules['custom_components.varsom.const'] = MockConst

# Now we can import and test the AvalancheAPI
import aiohttp
import datetime as dt
from typing import List, Dict, Any

class AvalancheAPI:
    """Simplified version to test the logic."""
    
    def __init__(self, county_id: str, county_name: str, lang: str = "en"):
        self.county_id = county_id
        self.county_name = county_name
        self.lang = lang

    async def fetch_warnings(self) -> List[Dict[str, Any]]:
        """Fetch avalanche warnings from NVE API."""
        try:
            today = dt.datetime.now().strftime("%Y-%m-%d")
            tomorrow = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
            
            API_BASE_AVALANCHE = "https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0"
            summary_url = f"{API_BASE_AVALANCHE}/api/RegionSummary/Simple/2/{today}/{tomorrow}"
            
            print(f"Testing AvalancheAPI for {self.county_name} (ID: {self.county_id})")
            print(f"Fetching from: {summary_url}")
            
            async with aiohttp.ClientSession() as session:
                # Get region summary to find active regions
                async with session.get(summary_url) as response:
                    if response.status != 200:
                        print(f"Error fetching summary: HTTP {response.status}")
                        return []
                    
                    summary_data = await response.json()
                    if not summary_data:
                        print("No avalanche warnings found")
                        return []
                    
                    print(f"Found {len(summary_data)} regions in summary")
                    
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
                    
                    print(f"Found {len(active_regions)} active avalanche regions")
                    
                    # Get detailed data for active regions
                    warnings = []
                    relevant_count = 0
                    
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
                                                # NEW LOGIC: Check county names first
                                                county_list = warning.get("CountyList", [])
                                                county_names = [county.get("Name", "") for county in county_list]
                                                is_relevant = self.county_name in county_names
                                                
                                                region_name = warning.get("RegionName", "Unknown")
                                                print(f"  Region: {region_name}")
                                                print(f"    Counties: {county_names}")
                                                print(f"    Target: {self.county_name}")
                                                print(f"    Match: {is_relevant}")
                                                
                                                if is_relevant:
                                                    relevant_count += 1
                                                    print(f"    ✅ INCLUDED!")
                                                    warnings.append({
                                                        "RegionName": region_name,
                                                        "DangerLevel": danger_level,
                                                        "Counties": county_names
                                                    })
                                                else:
                                                    print(f"    ❌ Filtered out")
                                                print()
                        except Exception as e:
                            print(f"Error fetching details for region {region_id}: {e}")
                            continue
                    
                    print(f"SUMMARY: {relevant_count}/{len(active_regions)} regions relevant to {self.county_name}")
                    return warnings
                        
        except Exception as err:
            print(f"Error: {err}")
            return []

async def test_avalanche_api():
    """Test the AvalancheAPI with new county name logic."""
    api = AvalancheAPI("46", "Vestland", "en")
    warnings = await api.fetch_warnings()
    
    if warnings:
        print(f"\n✅ SUCCESS: Found {len(warnings)} avalanche warnings for Vestland:")
        for warning in warnings:
            print(f"  • {warning['RegionName']}: Level {warning['DangerLevel']}")
            print(f"    Counties: {warning['Counties']}")
    else:
        print("\n❌ FAIL: No avalanche warnings found for Vestland")

if __name__ == "__main__":
    asyncio.run(test_avalanche_api())