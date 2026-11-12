"""PiSky-OLED : tableau de bord ADS-B sur écran SSD1306 128x64 (I2C).

Pages en rotation : tableau de bord, avion le plus proche, radar, terrains, système.
Écran d'alerte prioritaire (urgence 7500/7600/7700, militaire dans la zone d'alerte).
Protection de l'OLED : décalage d'1 pixel toutes les 2 min et luminosité réduite la nuit.
"""
import datetime as dt
import sys
import time

from PIL import Image

from modules.datasource import DataSource
from modules.display import Screens

# Position par défaut (remplacée par celle des Réglages du radar quand l'API répond)
MY_LAT = 48.8566
MY_LON = 2.3522

# Durée d'affichage de chaque page (secondes) ; 0 = page désactivée
PAGE_DURATIONS = {'dashboard': 6, 'closest': 8, 'radar': 15, 'airports': 8, 'system': 5}
DATA_REFRESH_S = 3            # rafraîchissement des données
FPS = {'radar': 4}            # images / s (1 par défaut)
ALERT_SHOW_S = 10             # durée de l'écran d'alerte
ALERT_REPEAT_S = 60           # rappel tant que l'alerte dure
NIGHT = (22, 7)               # luminosité réduite de 22 h à 7 h
CONTRAST_DAY, CONTRAST_NIGHT = 255, 8
PIXEL_SHIFT_S = 120


def open_device():
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    return ssd1306(i2c(port=1, address=0x3C))


def find_alert(snap):
    """Avion en alerte le plus prioritaire : (avion, libellé) ou (None, None)."""
    if not snap:
        return None, None
    for a in snap['aircraft']:
        if a.get('emergency'):
            meaning = {'7700': 'URGENCE 7700', '7600': 'PANNE RADIO 7600', '7500': 'DETOURNEMENT 7500'}
            return a, meaning.get(a.get('squawk'), 'URGENCE')
    rng = snap.get('alert_range')
    for a in snap['aircraft']:
        if a.get('military') and (rng is None or a['distance_km'] / 1.852 < rng):
            return a, 'MILITAIRE'
    return None, None


def main():
    device = open_device()
    data = DataSource(MY_LAT, MY_LON)
    screens = Screens()
    pages = [p for p in Screens.PAGES if PAGE_DURATIONS.get(p)]
    page_i, page_start = 0, time.time()
    last_data = 0
    alert_seen = {}            # hex -> dernier affichage
    alert_until, alert_ac, alert_kind = 0, None, None
    contrast = None
    print('--- PiSky-OLED ---')

    while True:
        now_t = time.time()
        now = dt.datetime.now()

        if now_t - last_data >= DATA_REFRESH_S:
            data.refresh()
            last_data = now_t
            ac, kind = find_alert(data.snapshot)
            if ac and now_t - alert_seen.get(ac['hex'], 0) > ALERT_REPEAT_S:
                alert_seen[ac['hex']] = now_t
                alert_until, alert_ac, alert_kind = now_t + ALERT_SHOW_S, ac, kind

        # luminosité jour / nuit
        night = now.hour >= NIGHT[0] or now.hour < NIGHT[1]
        want = CONTRAST_NIGHT if night else CONTRAST_DAY
        if want != contrast:
            device.contrast(want)
            contrast = want

        sysinfo = data.system()
        if now_t < alert_until:
            # rafraîchir l'avion en alerte avec les dernières données
            fresh = next((a for a in (data.snapshot or {}).get('aircraft', []) if a['hex'] == alert_ac['hex']), alert_ac)
            img = screens.render_alert(data.snapshot, sysinfo, fresh, alert_kind, now)
            fps = 4
        else:
            page = pages[page_i]
            dur = PAGE_DURATIONS[page]
            if now_t - page_start >= dur:
                page_i = (page_i + 1) % len(pages)
                page_start = now_t
                page = pages[page_i]
                dur = PAGE_DURATIONS[page]
            img = screens.render(page, data.snapshot, sysinfo, (now_t - page_start) / dur, now)
            fps = FPS.get(page, 1)

        # décalage d'un pixel (anti-marquage)
        shift = int(now_t // PIXEL_SHIFT_S) % 4
        if shift:
            dx, dy = [(0, 0), (1, 0), (1, 1), (0, 1)][shift]
            moved = Image.new('1', img.size, 0)
            moved.paste(img.crop((0, 0, img.width - dx, img.height - dy)), (dx, dy))
            img = moved

        device.display(img.convert(device.mode))
        time.sleep(max(0.05, 1 / fps - (time.time() - now_t)))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n[PiSky] arrêt')
        sys.exit(0)
