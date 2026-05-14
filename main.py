import time
import sys
from modules.display import OLEDDisplay
from modules.adsb import ADSBManager

# --- AVGEEK CONFIGURATION ---
MY_LAT = 46.219696224968246    # Your Station Latitude
MY_LON = 7.329450323965796     # Your Station Longitude
ROTATION_SPEED = 10

def main():
    try:
        display = OLEDDisplay()
        adsb = ADSBManager()
        page = 0 
        
        print("--- PiSky-OLED Terminal ---")
        print(f"Base Station Location: {MY_LAT}, {MY_LON}")
        print("Status: Running display rotation...")

        while True:
            stats = adsb.get_aircraft_stats(MY_LAT, MY_LON)
            
            if stats:
                # --- DEBUG LOGS ---
                closest = stats.get("closest")
                farthest = stats.get("farthest")
                
                print(f"\n[DEBUG] Total Aircrafts: {stats['count']}")
                
                if closest:
                    # On print les infos reçues d'OpenSky pour voir si ça dépasse ou si c'est vide
                    print(f"[DEBUG] Closest: {closest.get('flight')} | Model: {closest.get('model')} | Dist: {closest.get('distance'):.1f}km")
                else:
                    print("[DEBUG] No closest aircraft found (missing lat/lon in data)")

                if farthest:
                    print(f"[DEBUG] Farthest: {farthest.get('flight')} | Dist: {farthest.get('distance'):.1f}km")
                
                # --- DISPLAY LOGIC ---
                if page == 0:
                    print("[DEBUG] Switching to Page: Global Status")
                    display.render_global_status(
                        count=stats["count"], 
                        farthest_ac=farthest
                    )
                    page = 1
                else:
                    print("[DEBUG] Switching to Page: Closest Focus")
                    display.render_closest_aircraft(
                        ac=closest
                    )
                    page = 0
            else:
                print("[DEBUG] Error: stats is None (check tar1090 URL)")
                display.render_error("No ADSB Data")

            time.sleep(ROTATION_SPEED)

    except KeyboardInterrupt:
        print("\n[Service] Stopping PiSky-OLED...")
        sys.exit(0)
    except Exception as e:
        print(f"[Critical Error] {e}")
        try:
            display.render_error("System Crash")
        except:
            pass

if __name__ == "__main__":
    main()