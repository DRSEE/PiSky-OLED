import math
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

    def _format_altitude(self, alt_ft):
            """Helper to format altitude as Ft or Flight Level (FL)"""
            if alt_ft is None:
                return "Alt: N/A"
            
            # Rule: Above or equal to 5000ft -> Flight Level
            if alt_ft >= 5000:
                # Divide by 100 and format with 3 digits (e.g., FL050)
                fl_value = int(alt_ft / 100)
                return f"Alt:FL{fl_value:03d}"
            else:
                # Standard display in feet
                return f"Alt:{int(alt_ft)}ft"

    def render_radar_homing(self, ac):
            """Page 3: Visual radar with a stylized navigation arrow rotating on a red-dot axis"""
            with canvas(self.device) as draw:
                if not ac:
                    draw.text((5, 25), "SEARCHING SKY...", fill="white")
                    return

                # --- RADAR CIRCLE (LEFT SIDE) ---
                cx, cy, r = 32, 32, 30
                draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline="white")
                
                # Cardinal points
                draw.text((cx-3, cy-r+1), "N", fill="white")
                draw.text((cx-3, cy+r-9), "S", fill="white")
                draw.text((cx+r-7, cy-4), "E", fill="white")
                draw.text((cx-r+2, cy-4), "W", fill="white")

                # --- STYLIZED ARROW LOGIC (image_54833e.png style) ---
                bearing = ac.get("bearing", 0)
                angle_rad = math.radians(bearing - 90)

                # Define the 4 points of the stylized arrow relative to its own center (0,0)
                # Arrow shape: Top tip, Bottom-right, Inner-notch, Bottom-left
                # We scale these values to fit nicely in the 30px radius circle
                raw_points = [
                    (22, 0),    # Tip (Front)
                    (-12, 12),  # Bottom Right
                    (-5, 0),    # Inner Notch (The "V" shape back)
                    (-12, -12)  # Bottom Left
                ]

                # Rotate and translate points to the radar center (cx, cy)
                rotated_points = []
                for px, py in raw_points:
                    # Standard rotation matrix
                    rx = px * math.cos(angle_rad) - py * math.sin(angle_rad)
                    ry = px * math.sin(angle_rad) + py * math.cos(angle_rad)
                    rotated_points.append((cx + rx, cy + ry))

                # Draw the stylized arrow body
                draw.polygon(rotated_points, fill="white", outline="white")

                # --- CENTER AXIS (The "Red" Dot) ---
                # On a B&W OLED, we draw a small hollow or filled circle to represent the axis
                axis_r = 2
                draw.ellipse((cx-axis_r, cy-axis_r, cx+axis_r, cy+axis_r), fill="black", outline="white")
                draw.point((cx, cy), fill="white") # Center pivot point

                # --- DATA DISPLAY (RIGHT SIDE) ---
                callsign = ac.get("flight", "N/A").strip()
                dist = ac.get("distance", 0)
                alt_ft = ac.get("alt_baro", ac.get("altitude"))

                draw.text((70, 2), f"{callsign}", fill="white")
                draw.line((68, 14, 125, 14), fill="white")
                draw.text((70, 18), f"{dist:.1f}km", fill="white")
                draw.text((70, 33), f"BRG:{bearing:.0f}°", fill="white")
                draw.text((70, 48), self._format_altitude(alt_ft), fill="white")

    def render_moving_map(self, ac_list, my_lat, my_lon, zoom_km=15, show_labels=True):
            """Page 4: Moving Map with Dynamic Scaling and Toggleable Labels"""
            with canvas(self.device) as draw:
                cx, cy = 64, 32
                scale = 32 / zoom_km 

                # --- DYNAMIC SCALING CALCULATION ---
                # Base size 's' ranges between 3 and 8 pixels based on zoom level.
                s = max(3, min(8, 15 / (zoom_km**0.5)))

                for ac in ac_list:
                    lat, lon = ac.get("lat"), ac.get("lon")
                    if lat is not None and lon is not None:
                        # Projection for local X,Y coordinates
                        dx = (lon - my_lon) * 111.32 * math.cos(math.radians(my_lat)) * scale
                        dy = (my_lat - lat) * 111.32 * scale
                        ax, ay = cx + dx, cy + dy

                        # Only draw if aircraft is within OLED screen bounds
                        if 0 <= ax <= 128 and 0 <= ay <= 64:
                            track = ac.get("track", ac.get("t", 0))
                            angle = math.radians(track - 90)
                            
                            # --- THE ARROW (Dynamic size 's') ---
                            # Rotation axis (0,0) matches your red pivot point requirement
                            raw_points = [
                                (s * 2, 0),    # Nose
                                (-s, s * 0.8), # Right Wing
                                (0, 0),        # Notch (Pivot point / Red dot)
                                (-s, -s * 0.8) # Left Wing
                            ]
                            
                            rotated_points = []
                            for px, py in raw_points:
                                rx = px * math.cos(angle) - py * math.sin(angle)
                                ry = px * math.sin(angle) + py * math.cos(angle)
                                rotated_points.append((ax + rx, ay + ry))
                            
                            draw.polygon(rotated_points, fill="white")
                            
                            # --- CONDITIONAL LABELS ---
                            # Only shown if show_labels is True AND zoom is not too wide
                            if show_labels and zoom_km <= 50:
                                flight = ac.get("flight", "???").strip()
                                # Offset based on dynamic arrow size
                                draw.text((ax + s + 2, ay - 4), flight[:5], fill="white")

                # Center Station (Home) and Zoom indicator
                draw.line((cx-2, cy, cx+2, cy), fill="white")
                draw.line((cx, cy-2, cx, cy+2), fill="white")
                draw.text((2, 54), f"Z:{zoom_km}k", fill="white")