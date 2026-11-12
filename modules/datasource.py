"""Données pour l'écran : API du radar ADS-B (port 5001) en priorité, aircraft.json en secours.

L'API du radar fournit déjà immatriculations, types, altitude QNH, finales, mouvements des
terrains et QNH. Si le service radar est arrêté, on lit directement tar1090 (données brutes).
"""
import json
import math
import socket
import time

import requests

RADAR_API = 'http://localhost:5001'
TAR1090 = ['http://localhost/tar1090/data/aircraft.json', 'http://localhost:8080/data/aircraft.json']
READSB_STATS = '/run/readsb/stats.json'


def _dist_brg(lat1, lon1, lat2, lon2):
    r = math.radians
    dlat, dlon = r(lat2 - lat1), r(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(dlon / 2) ** 2
    d = 2 * 6371 * math.asin(math.sqrt(a))
    y = math.sin(dlon) * math.cos(r(lat2))
    x = math.cos(r(lat1)) * math.sin(r(lat2)) - math.sin(r(lat1)) * math.cos(r(lat2)) * math.cos(dlon)
    return d, (math.degrees(math.atan2(y, x)) + 360) % 360


class DataSource:
    def __init__(self, default_lat, default_lon):
        self.lat, self.lon = default_lat, default_lon
        self.snapshot = None          # dernières données valides
        self.source = None            # 'radar' | 'tar1090' | None
        self._sys_cache = (0, {})

    # ------------------------------------------------------------ avions
    def refresh(self):
        try:
            d = requests.get(RADAR_API + '/api/stats', timeout=3).json()
            if 'error' in d:
                raise ValueError(d['error'])
            st = d.get('station') or {}
            self.lat, self.lon = st.get('lat', self.lat), st.get('lon', self.lon)
            ac = [a for a in d.get('aircraft', []) if a.get('lat') is not None]
            self.snapshot = {
                'time': time.time(), 'count': d.get('total_aircraft', 0), 'with_pos': d.get('with_position', 0),
                'range_max': d.get('range_max', 0), 'range_record': d.get('range_record', 0),
                'aircraft': ac, 'airports': d.get('airports', []), 'movements': d.get('movements', []),
                'alerts': d.get('alert_stats', {}), 'alert_range': d.get('current_alert_range'),
                'ta': (d.get('qnh') or {}).get('transition_altitude_ft'),
            }
            self.source = 'radar'
            return self.snapshot
        except Exception:
            pass
        for url in TAR1090:          # secours : données brutes
            try:
                raw = requests.get(url, timeout=2).json().get('aircraft', [])
                ac = []
                for p in raw:
                    if 'lat' not in p:
                        continue
                    dkm, brg = _dist_brg(self.lat, self.lon, p['lat'], p['lon'])
                    ac.append({'hex': p.get('hex', ''), 'callsign': (p.get('flight') or '').strip(),
                               'registration': p.get('r', ''), 'type': p.get('t', ''), 'model': '',
                               'lat': p['lat'], 'lon': p['lon'], 'distance_km': dkm, 'bearing': brg,
                               'altitude': p.get('alt_baro'), 'alt_qnh': None, 'below_ta': False,
                               'speed': p.get('gs'), 'track': p.get('track'),
                               'vertical_speed': p.get('baro_rate', p.get('geom_rate')),
                               'squawk': p.get('squawk', ''), 'military': bool(p.get('dbFlags', 0) & 1),
                               'emergency': p.get('squawk') in ('7500', '7600', '7700'), 'final': None})
                ac.sort(key=lambda a: a['distance_km'])
                dists = [a['distance_km'] for a in ac]
                self.snapshot = {'time': time.time(), 'count': len(raw), 'with_pos': len(ac),
                                 'range_max': max(dists, default=0), 'range_record': None, 'aircraft': ac,
                                 'airports': [], 'movements': [], 'alerts': {}, 'alert_range': None, 'ta': None}
                self.source = 'tar1090'
                return self.snapshot
            except Exception:
                continue
        self.source = None
        return self.snapshot

    # ------------------------------------------------------------ système
    def system(self):
        """Infos système, recalculées au plus toutes les 5 s."""
        t, cached = self._sys_cache
        if time.time() - t < 5:
            return cached
        info = {}
        try:
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                info['temp'] = int(f.read()) / 1000
        except Exception:
            info['temp'] = None
        try:
            with open('/proc/loadavg') as f:
                info['load'] = float(f.read().split()[0])
        except Exception:
            info['load'] = None
        try:
            mem = {}
            with open('/proc/meminfo') as f:
                for line in f:
                    k, v = line.split(':')
                    mem[k] = int(v.split()[0])
            info['ram'] = 100 * (1 - mem['MemAvailable'] / mem['MemTotal'])
        except Exception:
            info['ram'] = None
        try:
            with open('/proc/uptime') as f:
                info['uptime'] = float(f.read().split()[0])
        except Exception:
            info['uptime'] = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            info['ip'] = s.getsockname()[0]
            s.close()
        except Exception:
            info['ip'] = '–'
        try:
            with open(READSB_STATS) as f:
                st = json.load(f)
            last = st.get('last1min', {})
            info['msg_s'] = last.get('messages', 0) / 60
            loc = last.get('local', {})
            info['signal'], info['noise'] = loc.get('signal'), loc.get('noise')
            info['max_km'] = (last.get('max_distance') or 0) / 1000
        except Exception:
            info['msg_s'] = info['signal'] = info['noise'] = info['max_km'] = None
        self._sys_cache = (time.time(), info)
        return info
