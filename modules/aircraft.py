import requests
import time
from threading import Lock

# In-memory cache to avoid hitting OpenSky API limits
aircraft_cache = {}
cache_lock = Lock()
CACHE_DURATION = 86400  # 24 hours in seconds

def get_aircraft_info(hex_code):
    """Fetch aircraft metadata from OpenSky API with local caching"""
    hex_code = hex_code.strip().lower()
    
    with cache_lock:
        if hex_code in aircraft_cache:
            cached = aircraft_cache[hex_code]
            if time.time() - cached['timestamp'] < CACHE_DURATION:
                return cached['data']

    try:
        url = f"https://opensky-network.org/api/metadata/aircraft/icao/{hex_code}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            result = {
                'registration':     data.get('registration', 'N/A'),
                'model':            data.get('model', 'N/A'),
                'operator':         data.get('operator', 'N/A'),
                'typecode':         data.get('typecode', 'N/A')
            }

            with cache_lock:
                aircraft_cache[hex_code] = {
                    'data': result,
                    'timestamp': time.time()
                }
            return result
    except Exception:
        pass

    return None
