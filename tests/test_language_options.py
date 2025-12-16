"""Test NVE API language options to verify what text is returned."""
import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api"
COUNTY_ID = 46  # Vestland

async def test_language_option(lang: str):
    """Test API with specific language option."""
    url = f"{API_BASE}/Warning/County/{COUNTY_ID}/{lang}"
    
    print(f"\n{'='*80}")
    print(f"Testing language: {lang}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"Total alerts received: {len(data)}")
                    
                    # Find an alert with Bergen and activity level > 1
                    for alert in data:
                        activity_level = alert.get("ActivityLevel", "1")
                        municipalities = [m.get("Name", "") for m in alert.get("MunicipalityList", [])]
                        
                        if activity_level != "1" and "Bergen" in municipalities:
                            print(f"\nSample active alert (ID: {alert.get('Id')}):")
                            print(f"  LangKey: {alert.get('LangKey')}")
                            print(f"  DangerTypeName: {alert.get('DangerTypeName')}")
                            print(f"  MainText (first 100 chars): {alert.get('MainText', '')[:100]}")
                            print(f"  WarningText (first 100 chars): {alert.get('WarningText', '')[:100]}")
                            print(f"  ActivityLevel: {activity_level}")
                            print(f"  Municipalities (first 5): {municipalities[:5]}")
                            
                            # Save full alert
                            filename = f"sample_alert_{lang}.json"
                            with open(filename, "w", encoding="utf-8") as f:
                                json.dump(alert, f, indent=2, ensure_ascii=False)
                            print(f"  Full alert saved to: {filename}")
                            break
                else:
                    print(f"ERROR: Status {response.status}")
                    text = await response.text()
                    print(f"Response: {text[:500]}")
                    
        except Exception as e:
            print(f"ERROR: {e}")

async def main():
    """Test both language options."""
    print(f"NVE API Language Test")
    print(f"Date: {datetime.now()}")
    
    # Test Norwegian
    await test_language_option("no")
    
    # Test English
    await test_language_option("en")
    
    print(f"\n{'='*80}")
    print("Language test complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())
