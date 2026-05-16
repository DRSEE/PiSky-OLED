import time
import sys
import math
from modules.display import OLEDDisplay
from modules.adsb import ADSBManager

# --- AVGEEK CONFIGURATION ---
MY_LAT = 46.219696224968246    # Your Station Latitude
MY_LON = 7.329450323965796     # Your Station Longitude


# --- PAGE CONFIGURATION ---
# Durations in seconds. Set Page 3 to 15s to enjoy the new map!
PAGE_DURATIONS = {0: 5, 1: 5, 2: 15, 3: 3} 
REFRESH_RATE_RADAR = 0.5 # Fast refresh for Moving Map & Compass
REFRESH_RATE_STATIC = 1  # Refresh rate for static text pages

# Initialize global tracking variables
page = 0 
last_page_switch = time.time()

def main():
    # Use 'global' keyword to modify variables defined outside the function
    global page, last_page_switch
    
    try:
        # Initialize hardware and data manager
        display = OLEDDisplay()
        adsb = ADSBManager()
        
        print("--- PiSky-OLED Terminal ---")
        print(f"Base Station Location: {MY_LAT}, {MY_LON}")
        print("Status: Running display rotation...")

        while True:
            # 1. Fetch live aircraft data from ADSB module
            stats = adsb.get_aircraft_stats(MY_LAT, MY_LON)
            
            if stats:
                all_aircraft = stats.get("all_aircraft", [])
                closest = stats.get("closest")
                farthest = stats.get("farthest")
                
                # Calculate time elapsed since the last page change
                current_time = time.time()
                elapsed = current_time - last_page_switch

                # --- DISPLAY ROTATION LOGIC ---
                
                # PAGE 0: Global Statistics
                if page == 0:
                    display.render_global_status(count=stats["count"], farthest_ac=farthest)
                    if elapsed >= PAGE_DURATIONS[0]:
                        page = 1
                        last_page_switch = current_time

                # PAGE 1: Closest Aircraft Details (Text)
                elif page == 1:
                    display.render_closest_aircraft(ac=closest)
                    if elapsed >= PAGE_DURATIONS[1]:
                        page = 2
                        last_page_switch = current_time

                # PAGE 2: Radar Homing (Dynamic Arrow for closest AC)
                elif page == 2:
                    display.render_radar_homing(ac=closest)
                    if elapsed >= PAGE_DURATIONS[2]:
                        page = 3
                        last_page_switch = current_time
                    else:
                        # Short sleep for smooth arrow animation
                        time.sleep(REFRESH_RATE_RADAR)
                        continue # Restart loop immediately to refresh data

                # PAGE 3: Moving Map (All nearby aircraft)
                elif page == 3:
                    display.render_moving_map(all_aircraft, MY_LAT, MY_LON, zoom_km=15, show_labels=True)
                    if elapsed >= PAGE_DURATIONS[3]:
                        page = 0
                        last_page_switch = current_time
                    else:
                        # Short sleep for smooth map movement
                        time.sleep(REFRESH_RATE_RADAR)
                        continue

            # Standard idle time for static pages
            time.sleep(REFRESH_RATE_STATIC)

    except KeyboardInterrupt:
        print("\n[Service] Stopping PiSky-OLED...")
        sys.exit(0)
    except Exception as e:
        print(f"[Critical Error] {e}")
        try:
            # Attempt to show the error message on the OLED
            display.render_error(f"Error: {str(e)[:15]}")
        except:
            pass

if __name__ == "__main__":
    main()