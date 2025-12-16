#!/usr/bin/env python3
"""Test script to investigate alert ID discrepancies."""
import asyncio
import aiohttp
import json
from datetime import datetime


async def fetch_and_analyze_alerts():
    """Fetch alerts and analyze IDs."""
    
    # Vestland county
    county_id = "46"
    lang = "en"
    
    # Try both landslide and flood APIs
    apis = {
        "landslide": "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10",
        "flood": "https://api01.nve.no/hydrology/forecast/flood/v1.0.10"
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "varsom/1.0.0 jeremy.m.cook@gmail.com"
    }
    
    for api_name, base_url in apis.items():
        url = f"{base_url}/api/Warning/County/{county_id}/{lang}"
        
        print(f"\n{'='*80}")
        print(f"Fetching {api_name.upper()} alerts from:")
        print(f"{url}")
        print(f"{'='*80}\n")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"ERROR: Status {response.status}")
                        continue
                    
                    data = await response.json()
                    
                    print(f"Total alerts received: {len(data)}\n")
                    
                    # Look for alerts affecting Bergen
                    bergen_alerts = []
                    for alert in data:
                        munis = alert.get("MunicipalityList", [])
                        muni_names = [m.get("Name", "") for m in munis]
                        if "Bergen" in muni_names:
                            bergen_alerts.append(alert)
                    
                    print(f"Alerts affecting Bergen: {len(bergen_alerts)}\n")
                    
                    # Check for specific IDs
                    target_ids = ["584732", "584744"]
                    
                    for target_id in target_ids:
                        found = False
                        for alert in data:
                            if alert.get("Id") == target_id:
                                found = True
                                print(f"✓ FOUND Alert ID {target_id}:")
                                print(f"  Municipalities: {[m.get('Name') for m in alert.get('MunicipalityList', [])]}")
                                print(f"  Main text: {alert.get('MainText', '')[:80]}...")
                                print(f"  Valid from: {alert.get('ValidFrom')}")
                                print(f"  Valid to: {alert.get('ValidTo')}")
                                
                                # Check if there's a MasterId field
                                if "MasterId" in alert:
                                    print(f"  MasterId: {alert.get('MasterId')}")
                                
                                # Construct URL
                                varsom_url = f"https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/{target_id}"
                                print(f"  URL: {varsom_url}")
                                print()
                                break
                        
                        if not found:
                            print(f"✗ Alert ID {target_id} NOT FOUND in {api_name} API\n")
                    
                    # Show all Bergen alert IDs
                    if bergen_alerts:
                        print(f"\nAll Bergen alert IDs in {api_name} API:")
                        for alert in bergen_alerts:
                            alert_id = alert.get("Id")
                            level = alert.get("ActivityLevel")
                            munis = [m.get("Name") for m in alert.get("MunicipalityList", [])]
                            main_text = alert.get("MainText", "")[:60]
                            
                            print(f"  ID: {alert_id}")
                            print(f"    Level: {level}")
                            print(f"    Municipalities: {munis}")
                            print(f"    Text: {main_text}...")
                            
                            # Check for MasterId
                            if "MasterId" in alert:
                                print(f"    MasterId: {alert.get('MasterId')}")
                            
                            print()
                    
                    # Save full response for inspection
                    filename = f"response_{api_name}_{county_id}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"Full response saved to: {filename}")
                    
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()


async def test_specific_alert_endpoints():
    """Test fetching specific alerts by ID."""
    
    print(f"\n{'='*80}")
    print("Testing specific alert ID endpoints")
    print(f"{'='*80}\n")
    
    base_url = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10"
    headers = {
        "Accept": "application/json",
        "User-Agent": "varsom/1.0.0 jeremy.m.cook@gmail.com"
    }
    
    test_ids = ["584732", "584744"]
    
    for alert_id in test_ids:
        url = f"{base_url}/api/Warning/{alert_id}"
        print(f"Fetching: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✓ Alert exists")
                        print(f"  Id: {data.get('Id')}")
                        if "MasterId" in data:
                            print(f"  MasterId: {data.get('MasterId')}")
                        print(f"  Municipalities: {[m.get('Name') for m in data.get('MunicipalityList', [])]}")
                    elif response.status == 404:
                        print(f"  ✗ Alert not found (404)")
                    else:
                        print(f"  ✗ Unexpected status")
                    
                    print()
                    
        except Exception as e:
            print(f"  ERROR: {e}\n")


async def main():
    """Run all tests."""
    print("NVE API Alert ID Investigation")
    print(f"Date: {datetime.now()}")
    
    await fetch_and_analyze_alerts()
    await test_specific_alert_endpoints()
    
    print(f"\n{'='*80}")
    print("Investigation complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
