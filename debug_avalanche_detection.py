#!/usr/bin/env python3
"""Debug avalanche detection issues."""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

async def debug_avalanche_detection():
    """Debug why avalanche alerts are not being detected."""
    
    print("DEBUGGING AVALANCHE DETECTION")
    print("=" * 50)
    
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    summary_url = f"https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0/api/RegionSummary/Simple/2/{today}/{tomorrow}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(summary_url) as response:
                if response.status != 200:
                    print(f"❌ Summary API error: HTTP {response.status}")
                    return
                    
                summary_data = await response.json()
                if not summary_data:
                    print("❌ No summary data returned")
                    return
                
                print(f"✅ Found {len(summary_data)} regions in summary")
                
                # Check for active regions
                active_count = 0
                vestland_relevant_count = 0
                
                for region in summary_data:
                    region_name = region.get('Name', 'Unknown')
                    region_id = region.get('Id', 'Unknown')
                    warnings = region.get("AvalancheWarningList", [])
                    
                    for warning in warnings:
                        danger_level = warning.get("DangerLevel", 0)
                        if isinstance(danger_level, str):
                            danger_level = int(danger_level) if danger_level.isdigit() else 0
                        
                        if danger_level > 0:
                            active_count += 1
                            print(f"🟡 Active region: {region_name} (ID: {region_id}, Danger: {danger_level})")
                            
                            # Get detailed data to check Vestland relevance
                            detail_url = f"https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0/api/AvalancheWarningByRegion/Detail/{region_id}/2/{today}/{tomorrow}"
                            
                            try:
                                async with session.get(detail_url) as detail_response:
                                    if detail_response.status == 200:
                                        detail_data = await detail_response.json()
                                        
                                        if isinstance(detail_data, list) and detail_data:
                                            detail_warning = detail_data[0]
                                            municipality_list = detail_warning.get("MunicipalityList", [])
                                            county_list = detail_warning.get("CountyList", [])
                                            
                                            print(f"    Counties: {[c.get('Name', c.get('Id')) for c in county_list]}")
                                            print(f"    Municipalities: {len(municipality_list)} total")
                                            
                                            # Check Vestland relevance
                                            vestland_municipalities = 0
                                            total_municipalities = len(municipality_list)
                                            
                                            for muni in municipality_list:
                                                county_id = str(muni.get("CountyId", ""))
                                                muni_name = muni.get("Name", "Unknown")
                                                if county_id == "46":
                                                    vestland_municipalities += 1
                                                    print(f"    ✅ Vestland muni: {muni_name} (County: {county_id})")
                                                else:
                                                    print(f"    ❌ Other muni: {muni_name} (County: {county_id})")
                                            
                                            if total_municipalities > 0:
                                                relevance_score = vestland_municipalities / total_municipalities
                                                print(f"    📊 Vestland relevance: {vestland_municipalities}/{total_municipalities} = {relevance_score:.2%}")
                                                
                                                if relevance_score >= 0.3:
                                                    vestland_relevant_count += 1
                                                    print(f"    ✅ PASSES 30% threshold - would be included")
                                                else:
                                                    print(f"    ❌ FAILS 30% threshold - would be filtered out")
                                            else:
                                                print(f"    ⚠️ No municipalities found")
                            
                            except Exception as e:
                                print(f"    ❌ Error getting details: {e}")
                            
                            print()
                
                print(f"SUMMARY:")
                print(f"Total regions: {len(summary_data)}")
                print(f"Active regions: {active_count}")
                print(f"Vestland-relevant regions (>= 30%): {vestland_relevant_count}")
                
                if vestland_relevant_count == 0:
                    print("\n🔍 DIAGNOSIS:")
                    if active_count == 0:
                        print("- No active avalanche warnings in Norway today")
                    else:
                        print("- Active warnings exist but none are relevant to Vestland (>= 30% threshold)")
                        print("- Consider lowering the relevance threshold from 30% to 10% or 20%")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_avalanche_detection())