"""Test NVE API with Språknøkkel query parameter for language selection."""
import asyncio
import aiohttp
import json

API_BASE = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api"
COUNTY_ID = 46

async def test_spraknokkel(lang_key: int, lang_name: str):
    """Test API with specific Språknøkkel value."""
    # Try without the /no or /en path suffix
    url = f"{API_BASE}/Warning/County/{COUNTY_ID}"
    params = {"Språknøkkel": lang_key}
    
    print(f"\n{'='*80}")
    print(f"Testing Språknøkkel: {lang_key} ({lang_name})")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"{'='*80}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                print(f"Actual URL: {response.url}")
                
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
                            print(f"  MainText: {alert.get('MainText', '')[:80]}...")
                            
                            # Save
                            filename = f"alert_langkey_{lang_key}.json"
                            with open(filename, "w", encoding="utf-8") as f:
                                json.dump(alert, f, indent=2, ensure_ascii=False)
                            print(f"  Saved to: {filename}")
                            break
                else:
                    print(f"ERROR: {response.status}")
                    
        except Exception as e:
            print(f"ERROR: {e}")

async def main():
    """Test both language keys."""
    print("Testing NVE API Språknøkkel Parameter")
    
    # Test Norwegian (0 or 1?)
    await test_spraknokkel(0, "Norwegian (0)")
    
    # Test English (1 or 2?)
    await test_spraknokkel(1, "English (1)")
    
    print(f"\n{'='*80}")
    print("Test complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())
