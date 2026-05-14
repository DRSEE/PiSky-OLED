import requests
from modules.geo_utils import GeoUtils
from modules.aircraft import get_aircraft_info

class ADSBManager:
    def __init__(self, url="http://localhost/tar1090/data/aircraft.json"):
        self.url = url

    def get_aircraft_stats(self, my_lat, my_lon):
        try:
            # We use your list of URLs logic
            response = requests.get(self.url, timeout=2)
            data = response.json()
            aircrafts = data.get("aircraft", [])
            
            closest = None
            farthest = None
            min_dist = float('inf')
            max_dist = 0

            for ac in aircrafts:
                if "lat" in ac and "lon" in ac:
                    dist = GeoUtils.calculate_distance(my_lat, my_lon, ac["lat"], ac["lon"])
                    bearing = GeoUtils.calculate_bearing(my_lat, my_lon, ac["lat"], ac["lon"])
                    
                    ac_data = ac.copy()
                    ac_data["distance"] = dist
                    ac_data["bearing"] = bearing
                    ac_data["icao"] = ac.get("hex", "").lower()

                    if dist < min_dist:
                        min_dist = dist
                        closest = ac_data
                    
                    if dist > max_dist:
                        max_dist = dist
                        farthest = ac_data

            # Enrich ONLY the closest aircraft with OpenSky data
            if closest and closest.get("icao"):
                info = get_aircraft_info(closest["icao"])
                if info:
                    closest["model"] = info["model"]
                    closest["registration"] = info["registration"]
                else:
                    closest["model"] = closest.get("t", "Unknown")

            return {
                "count": len(aircrafts),
                "closest": closest,
                "farthest": farthest
            }
        except Exception:
            return None