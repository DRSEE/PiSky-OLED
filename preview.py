"""Génère des aperçus PNG de toutes les pages, sans écran (données réelles du radar).

    python3 preview.py [dossier_sortie]
Les images sont agrandies x6 et teintées comme un OLED bleu/blanc pour faciliter la relecture.
"""
import datetime as dt
import os
import sys

from PIL import Image

from main import MY_LAT, MY_LON, find_alert
from modules.datasource import DataSource
from modules.display import Screens

out = sys.argv[1] if len(sys.argv) > 1 else 'preview'
os.makedirs(out, exist_ok=True)
data = DataSource(MY_LAT, MY_LON)
snap = data.refresh()
sysinfo = data.system()
sc = Screens()
now = dt.datetime.now()


def save(img, name):
    big = img.convert('L').resize((128 * 6, 64 * 6), Image.NEAREST)
    rgb = Image.merge('RGB', (big.point(lambda v: v * 200 // 255), big.point(lambda v: v * 235 // 255), big))
    canvas = Image.new('RGB', (128 * 6 + 24, 64 * 6 + 24), (20, 20, 24))
    canvas.paste(rgb, (12, 12))
    canvas.save(os.path.join(out, name + '.png'))


for i, p in enumerate(Screens.PAGES):
    save(sc.render(p, snap, sysinfo, 0.6, now), f'{i}_{p}')
ac, kind = find_alert(snap)
demo = ac or (snap['aircraft'][0] if snap and snap['aircraft'] else None)
save(sc.render_alert(snap, sysinfo, demo, kind or 'MILITAIRE (demo)', now.replace(microsecond=100000)), '9_alert')
print('source :', data.source, '| aperçus dans', out)
