import datetime
from luma.oled.device import ssd1306
from luma.core.interface.serial import i2c
from luma.core.render import canvas

class OLEDDisplay:
    def __init__(self, port=1, address=0x3C):
        serial = i2c(port=port, address=address)
        self.device = ssd1306(serial)

    def render_global_status(self, count, farthest_ac):
        """Page 1: Overview with Farthest aircraft record"""
        with canvas(self.device) as draw:
            draw.text((6, 0), "PiSky Overview", fill="white")
            draw.line((0, 12, 128, 12), fill="white")
            draw.text((6, 20), f"total aircraft: {count}", fill="white")
            
            if farthest_ac:
                callsign = farthest_ac.get("flight", "N/A").strip()
                dist = farthest_ac.get("distance", 0)
                draw.text((6, 35), f"Max range :", fill="white")
                draw.text((6, 50), f"{callsign} at {dist:.1f}km", fill="white")
            else:
                draw.text((5, 35), "No range data", fill="white")

    def render_closest_aircraft(self, ac):
        with canvas(self.device) as draw:
            if not ac:
                draw.text((5, 25), "SEARCHING SKY...", fill="white")
                return

            # --- PREPARATION DES DONNEES ---
            callsign = ac.get("flight", "N/A").strip()
            registration = ac.get("registration", "N/A")
            
            # Logique du modèle
            model = ac.get("model")
            if not model or model == "N/A":
                model = ac.get("t", f"HEX:{ac.get('hex', '???')}")
            
            # On réduit drastiquement la longueur du modèle pour faire de la place
            model_display = (model[:16] + '..') if len(model) > 17 else model
                
            dist = ac.get("distance", 0)
            bearing = ac.get("bearing", 0)
            
            from modules.geo_utils import GeoUtils
            cardinal = GeoUtils.bearing_to_cardinal(bearing)

            # --- RENDU GRAPHIQUE ---
            # Ligne 1 : Callsign + Témoin d'activité
            draw.text((5, 0), f"CLOSEST: {callsign}", fill="white")
            
            import datetime
            if datetime.datetime.now().second % 2 == 0:
                draw.text((118, 0), "*", fill="white")
            
            draw.line((0, 12, 128, 12), fill="white")
            
            # Ligne 2 : Registration (Immatriculation)
            draw.text((5, 16), f"REG: {registration}", fill="white")
            
            # Ligne 3 : Modèle
            draw.text((5, 30), f"MOD: {model_display}", fill="white")
            
            # Ligne 4 : Distance
            draw.text((5, 42), f"DST: {dist:.1f} km", fill="white")
            
            # Ligne 5 : Position (Bearing + Cardinal)
            # On la place tout en bas pour aérer
            draw.text((5, 54), f"POS: {bearing:.0f}' ({cardinal})", fill="white")