"""Render PNG previews of every page without an OLED (uses live radar data).

    python3 preview.py [output_dir]        # quick previews
    python3 preview.py docs/images --demo  # README images: IP masked + animated radar GIF

Images are upscaled and tinted like a white/blue OLED to make them easy to review.
"""
import datetime as dt
import os
import sys

from PIL import Image, ImageDraw

from main import MY_LAT, MY_LON, find_alert
from modules.datasource import DataSource
from modules.display import Screens

args = [a for a in sys.argv[1:] if not a.startswith('--')]
demo = '--demo' in sys.argv
out = args[0] if args else 'preview'
scale = 4 if demo else 6
os.makedirs(out, exist_ok=True)

data = DataSource(MY_LAT, MY_LON)
snap = data.refresh()
sysinfo = dict(data.system())
if demo:
    sysinfo['ip'] = '192.168.1.42'          # never publish the real address
sc = Screens()
now = dt.datetime.now()


def oled(img):
    """Upscale a 1-bit frame and put it in a dark bezel."""
    big = img.convert('L').resize((128 * scale, 64 * scale), Image.NEAREST)
    rgb = Image.merge('RGB', (big.point(lambda v: v * 205 // 255), big.point(lambda v: v * 235 // 255), big))
    pad = 6 * scale // 2
    frame = Image.new('RGB', (rgb.width + 2 * pad, rgb.height + 2 * pad), (18, 19, 23))
    ImageDraw.Draw(frame).rectangle((1, 1, frame.width - 2, frame.height - 2), outline=(48, 50, 58), width=2)
    frame.paste(rgb, (pad, pad))
    return frame


names = {'dashboard': 'dashboard', 'closest': 'closest', 'radar': 'radar', 'airports': 'airports', 'system': 'system'}
for i, p in enumerate(Screens.PAGES):
    fname = names[p] if demo else f'{i}_{p}'
    oled(sc.render(p, snap, sysinfo, 0.6, now)).save(os.path.join(out, fname + '.png'))

ac, kind = find_alert(snap)
target = ac or (snap['aircraft'][0] if snap and snap['aircraft'] else None)
oled(sc.render_alert(snap, sysinfo, target, 'ALERT (DEMO)' if demo else (kind or 'MILITAIRE (demo)'),
                     now.replace(microsecond=100000))).save(os.path.join(out, 'alert.png' if demo else '9_alert.png'))

if demo:
    # animated radar: one full sweep (15 s) in 30 frames
    frames = [oled(sc.render('radar', snap, sysinfo, k / 30, now + dt.timedelta(seconds=k * 0.5)))
              .quantize(colors=4) for k in range(30)]
    frames[0].save(os.path.join(out, 'radar.gif'), save_all=True, append_images=frames[1:], duration=120, loop=0,
                   optimize=True)

print('source:', data.source, '| previews in', out)
