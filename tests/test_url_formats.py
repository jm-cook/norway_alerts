"""Test NVE API with Språknøkkel as path parameter."""
import asyncio
import aiohttp
import json

API_BASE = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api"
COUNTY_ID = 46

async def test_format(url_pattern: str, description: str):
    """Test specific URL format."""
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"URL: {url_pattern}")
    print(f"{'='*80}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url_pattern) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"Total alerts: {len(data)}")
                    
                    # Find active alert
                    for alert in data:
                        level = alert.get("ActivityLevel", "1")
                        munis = [m.get("Name", "") for m in alert.get("MunicipalityList", [])]
                        
                        if level != "1" and "Bergen" in munis:
                            print(f"\nAlert ID {alert.get('Id')}:")
                            print(f"  LangKey: {alert.get('LangKey')}")
                            print(f"  DangerTypeName: {alert.get('DangerTypeName')}")
                            print(f"  MainText: {alert.get('MainText', '')[:100]}...")
                            return alert
                else:
                    print(f"ERROR: {response.status}")
                    text = await response.text()
                    print(f"Response: {text[:200]}")
                    
        except Exception as e:
            print(f"ERROR: {e}")
    return None

async def main():
    """Test different URL formats."""
    print("Testing NVE API URL Formats with Språknøkkel")
    
    # Format 1: County only (existing format)
    alert1 = await test_format(
        f"{API_BASE}/Warning/County/{COUNTY_ID}",
        "County only (no language)"
    )
    
    # Format 2: County with /no suffix
    alert2 = await test_format(
        f"{API_BASE}/Warning/County/{COUNTY_ID}/no",
        "County with /no suffix"
    )
    
    # Format 3: County with /en suffix
    alert3 = await test_format(
        f"{API_BASE}/Warning/County/{COUNTY_ID}/en",
        "County with /en suffix"
    )
    
    # Format 4: Språknøkkel as number before county (maybe?)
    alert4 = await test_format(
        f"{API_BASE}/Warning/1/County/{COUNTY_ID}",
        "Språknøkkel 1 before County"
    )
    
    # Format 5: Try the path structure you mentioned /Warning/{Språknøkkel}/{Startdato}/{Sluttdato}
    # Maybe it's /Warning/County/{County}/{Språknøkkel}?
    alert5 = await test_format(
        f"{API_BASE}/Warning/County/{COUNTY_ID}/1",
        "County with Språknøkkel 1 as number"
    )
    
    alert6 = await test_format(
        f"{API_BASE}/Warning/County/{COUNTY_ID}/2",
        "County with Språknøkkel 2 as number"
    )
    
    # Compare results
    print(f"\n{'='*80}")
    print("Comparison:")
    if alert1 and alert2:
        print(f"Alert1 vs Alert2 identical: {alert1 == alert2}")
    if alert1 and alert3:
        print(f"Alert1 vs Alert3 identical: {alert1 == alert3}")
    if alert5 and alert6:
        print(f"Alert5 (1) vs Alert6 (2) identical: {alert5 == alert6}")
        print(f"Alert5 LangKey: {alert5.get('LangKey')}, MainText lang: {'NO' if 'Varsel' in alert5.get('MainText', '') else 'EN'}")
        print(f"Alert6 LangKey: {alert6.get('LangKey')}, MainText lang: {'NO' if 'Varsel' in alert6.get('MainText', '') else 'EN'}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())
