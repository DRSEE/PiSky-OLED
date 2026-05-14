import requests
import time
from luma.oled.device import ssd1306
from luma.core.interface.serial import i2c
from luma.core.render import canvas

# Configuration de l'écran
try:
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial)
except Exception as e:
    print(f"Erreur écran : {e}")
    exit()

# URL de tes données
URL = "http://localhost/tar1090/data/aircraft.json"

print("Démarrage du monitoring ADSB...")

while True:
    try:
        # Récupération des données
        response = requests.get(URL, timeout=5)
        data = response.json()
        
        # On compte les avions dans la liste 'aircraft'
        # On filtre ceux qui ont au moins une position ou un hex pour être sûr
        nb_avions = len(data.get("aircraft", []))
        
        # Mise à jour de l'écran
        with canvas(device) as draw:
            draw.text((5, 0), "ADSB EXCHANGE", fill="white")
            draw.line((0, 12, 128, 12), fill="white")
            draw.text((5, 25), f"AVIONS: {nb_avions}", fill="white")
            draw.text((5, 45), f"IP: 192.168.0.35", fill="white")
            
    except Exception as e:
        with canvas(device) as draw:
            draw.text((0, 0), "Erreur de lecture", fill="white")
            print(f"Erreur : {e}")

    time.sleep(1)