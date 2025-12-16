#!/usr/bin/env python3
"""Test script for Varsom Alerts integration.

This script tests the Varsom API connection and displays sample data
that will be fetched by the Home Assistant integration.
"""
import asyncio
import aiohttp
import json


async def test_varsom_api(county_id="46", warning_type="landslide", lang="en"):
    """Test the Varsom API connection."""
    
    if warning_type == "landslide":
        base_url = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10"
    else:
        base_url = "https://api01.nve.no/hydrology/forecast/flood/v1.0.10"
    
    url = f"{base_url}/api/Warning/County/{county_id}/{lang}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "varsom/1.0.0 jeremy.m.cook@gmail.com"
    }
    
    print(f"Testing Varsom API")
    print(f"URL: {url}")
    print(f"Warning Type: {warning_type}")
    print(f"County ID: {county_id}")
    print(f"Language: {lang}")
    print("=" * 80)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"ERROR: Status {response.status}")
                    return None
                
                data = await response.json()
                
                # Filter active warnings (level > 1)
                active_warnings = [w for w in data if w.get("ActivityLevel", "1") != "1"]
                
                print(f"\nTotal warnings in response: {len(data)}")
                print(f"Active warnings (level 2+): {len(active_warnings)}")
                
                if not active_warnings:
                    print("\n✓ No active warnings - all areas at GREEN level")
                    return data
                
                # Find highest level
                max_level = max(int(w.get("ActivityLevel", "1")) for w in active_warnings)
                level_names = {"1": "GREEN", "2": "YELLOW", "3": "ORANGE", "4": "RED"}
                
                print(f"\nHighest Alert Level: {max_level} ({level_names.get(str(max_level), 'UNKNOWN')})")
                print("\nActive Warnings:")
                print("-" * 80)
                
                for idx, warning in enumerate(active_warnings, 1):
                    level = warning.get("ActivityLevel", "1")
                    level_name = level_names.get(level, "UNKNOWN")
                    
                    print(f"\nAlert {idx}: Level {level_name}")
                    print(f"  ID: {warning.get('Id')}")
                    print(f"  Danger Type: {warning.get('DangerTypeName')}")
                    print(f"  Valid: {warning.get('ValidFrom')} to {warning.get('ValidTo')}")
                    
                    # Municipalities
                    munis = warning.get("MunicipalityList", [])
                    if munis:
                        muni_names = [m.get("Name") for m in munis]
                        print(f"  Municipalities: {', '.join(muni_names[:5])}")
                        if len(muni_names) > 5:
                            print(f"    ... and {len(muni_names) - 5} more")
                    
                    # Times
                    if warning.get("DangerIncreaseDateTime"):
                        print(f"  Danger Increases: {warning.get('DangerIncreaseDateTime')}")
                    if warning.get("DangerDecreaseDateTime"):
                        print(f"  Danger Decreases: {warning.get('DangerDecreaseDateTime')}")
                    
                    # Main text
                    main_text = warning.get("MainText", "")
                    if main_text:
                        print(f"  Main Text: {main_text[:100]}{'...' if len(main_text) > 100 else ''}")
                    
                    # Varsom.no URL
                    forecast_id = warning.get("Id", "")
                    if forecast_id:
                        lang_path = "en" if lang == "en" else ""
                        varsom_url = f"https://www.varsom.no/{lang_path}/flood-and-landslide-warning-service/forecastid/{forecast_id}".replace("//f", "/f")
                        print(f"  URL (with map): {varsom_url}")
                
                print("\n" + "=" * 80)
                print("✓ API test successful")
                
                # Show what the sensor would look like
                print("\nHome Assistant Sensor Preview:")
                print("-" * 80)
                print(f"State: {max_level}")
                print(f"Attributes:")
                print(f"  active_alerts: {len(active_warnings)}")
                print(f"  highest_level: {level_names.get(str(max_level), 'unknown').lower()}")
                print(f"  highest_level_numeric: {max_level}")
                print(f"  alerts: [{len(active_warnings)} alert objects]")
                
                return data
                
    except Exception as e:
        print(f"ERROR: {e}")
        return None


async def main():
    """Run tests for different counties."""
    print("Varsom API Test Script")
    print("=" * 80)
    
    # Test Vestland county (46) with landslide warnings
    print("\n\nTest 1: Vestland County - Landslide Warnings")
    await test_varsom_api(county_id="46", warning_type="landslide", lang="en")
    
    # Uncomment to test other configurations:
    # print("\n\nTest 2: Rogaland County - Landslide Warnings")
    # await test_varsom_api(county_id="11", warning_type="landslide", lang="no")
    
    # print("\n\nTest 3: Vestland County - Flood Warnings")
    # await test_varsom_api(county_id="46", warning_type="flood", lang="en")


if __name__ == "__main__":
    asyncio.run(main())
