"""Rendu des pages de l'écran OLED SSD1306 (128 x 64, monochrome).

Chaque page est dessinée dans une image PIL 1 bit, puis envoyée à l'écran.
Gros chiffres en police vectorielle (DejaVu Bold), petits libellés en police bitmap
(nette à petite taille). Rendu indépendant du matériel : `render()` renvoie une image,
ce qui permet aussi de générer des aperçus PNG sans écran (voir preview.py).
"""
import datetime as dt
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 128, 64
FONT_DIR = '/usr/share/fonts/truetype/dejavu/'


def _font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except Exception:
        return ImageFont.load_default()


TINY = ImageFont.load_default()                 # bitmap 6x11, net
S = _font('DejaVuSans-Bold.ttf', 10)
M = _font('DejaVuSans-Bold.ttf', 13)
L = _font('DejaVuSans-Bold.ttf', 17)
XL = _font('DejaVuSans-Bold.ttf', 28)
MONO = _font('DejaVuSansMono-Bold.ttf', 11)

CARD = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']


# ------------------------------------------------------------------ outils de dessin

def tw(draw, text, font):
    """Largeur d'un texte en pixels."""
    try:
        return int(draw.textlength(text, font=font))
    except AttributeError:
        return draw.textsize(text, font=font)[0]


def text_r(draw, x_right, y, text, font, fill=1):
    draw.text((x_right - tw(draw, text, font), y), text, font=font, fill=fill)


def text_c(draw, cx, y, text, font, fill=1):
    draw.text((cx - tw(draw, text, font) // 2, y), text, font=font, fill=fill)


def header(draw, title, right=''):
    """Bandeau inversé de 11 px en haut de l'écran."""
    draw.rectangle((0, 0, W - 1, 10), fill=1)
    draw.text((3, 0), title, font=TINY, fill=0)
    if right:
        text_r(draw, W - 3, 0, right, TINY, fill=0)


def progress(draw, frac):
    """Fine barre de progression de la page en bas de l'écran."""
    draw.line((0, H - 1, int((W - 1) * max(0, min(1, frac))), H - 1), fill=1)


def plane_icon(draw, x, y, track, size=4, fill=1):
    """Petite silhouette d'avion orientée selon la route."""
    a = math.radians((track or 0) - 90)
    pts = [(2.2, 0), (-1.4, 1.5), (-0.7, 0), (-1.4, -1.5)]
    draw.polygon([(x + size * (px * math.cos(a) - py * math.sin(a)),
                   y + size * (px * math.sin(a) + py * math.cos(a))) for px, py in pts], fill=fill)


def arrow(draw, cx, cy, brg, r, fill=1):
    """Flèche de direction (relèvement) dans un cercle."""
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fill)
    a = math.radians(brg - 90)
    pt = lambda ang, k: (cx + k * math.cos(ang), cy + k * math.sin(ang))
    draw.polygon([pt(a, r - 2), pt(a + 2.5, (r - 2) * .8), pt(a + math.pi, (r - 2) * .25), pt(a - 2.5, (r - 2) * .8)], fill=fill)


def fmt_alt(a):
    alt = a.get('altitude')
    if alt == 'ground':
        return 'SOL'
    if alt is None:
        return '---'
    if a.get('below_ta') and a.get('alt_qnh') is not None:
        return f"{a['alt_qnh']:,}".replace(',', ' ') + 'ft'
    return f'FL{max(0, round(alt / 100)):03d}'


def name(a):
    return a.get('callsign') or a.get('registration') or (a.get('hex') or '?').upper()


def vs_mark(draw, x, y, vs):
    """Triangle montée / descente."""
    if vs is None or abs(vs) < 300:
        draw.line((x, y + 3, x + 5, y + 3), fill=1)
    elif vs > 0:
        draw.polygon([(x, y + 6), (x + 6, y + 6), (x + 3, y)], fill=1)
    else:
        draw.polygon([(x, y), (x + 6, y), (x + 3, y + 6)], fill=1)


# ------------------------------------------------------------------ pages

class Screens:
    PAGES = ['dashboard', 'closest', 'radar', 'airports', 'system']

    def render(self, page, snap, sysinfo, frac=0.0, now=None):
        img = Image.new('1', (W, H), 0)
        d = ImageDraw.Draw(img)
        now = now or dt.datetime.now()
        if snap is None:
            self.no_data(d, now)
        else:
            getattr(self, page)(d, snap, sysinfo, now)
        if page != 'alert':
            progress(d, frac)
        return img

    # ---------- 0. Tableau de bord
    def dashboard(self, d, s, sysi, now):
        header(d, 'ADS-B RADAR', now.strftime('%H:%M'))
        n = str(s['count'])
        d.text((4, 13), n, font=XL, fill=1)
        d.text((6, 45), 'avions', font=TINY, fill=1)
        d.line((62, 15, 62, 58), fill=1)
        rows = [('Pos.', str(s['with_pos'])), ('Max', f"{s['range_max']:.0f}km")]
        q = next((ap.get('qnh', {}).get('qnh') for ap in s.get('airports', []) if ap.get('qnh', {}).get('qnh')), None)
        if q:
            rows.insert(0, ('QNH', f'{q:.0f}'))
        if sysi.get('msg_s') is not None:
            rows.append(('Msg/s', f"{sysi['msg_s']:.0f}"))
        for i, (k, v) in enumerate(rows[:4]):
            y = 14 + i * 11
            d.text((67, y), k, font=TINY, fill=1)
            text_r(d, 125, y, v, TINY)

    # ---------- 1. Avion le plus proche
    def closest(self, d, s, sysi, now):
        ac = s['aircraft'][0] if s['aircraft'] else None
        if not ac:
            header(d, 'PLUS PROCHE')
            text_c(d, 64, 28, 'Ciel vide', M)
            return
        header(d, 'PLUS PROCHE', f"{ac['distance_km']:.1f} km")
        d.text((2, 12), name(ac)[:9], font=L, fill=1)
        sub = ' '.join(x for x in (ac.get('registration'), ac.get('type')) if x) or (ac.get('hex') or '').upper()
        d.text((3, 31), sub[:17], font=TINY, fill=1)
        arrow(d, 113, 25, ac.get('bearing') or 0, 11)
        text_c(d, 113, 37, CARD[round((ac.get('bearing') or 0) / 45) % 8], TINY)
        d.line((0, 45, W - 1, 45), fill=1)
        d.text((2, 48), fmt_alt(ac), font=M, fill=1)
        vs_mark(d, 72, 51, ac.get('vertical_speed'))
        text_r(d, 125, 48, f"{ac['speed']:.0f}kt" if ac.get('speed') is not None else '', M)
        if ac.get('final'):
            f = ac['final']
            tag = f"FIN {f['rwy']}"
            x = 125 - tw(d, tag, TINY) - 3
            d.rectangle((x - 2, 31, 126, 41), fill=1)
            d.text((x, 31), tag, font=TINY, fill=0)

    # ---------- 2. Radar (avions proches, balayage animé)
    def radar(self, d, s, sysi, now):
        cx, cy, r = 32, 32, 30
        ac = s['aircraft']
        near = [a for a in ac if a['distance_km'] <= 60]
        rng = 15 if near and near[min(2, len(near) - 1)]['distance_km'] < 12 else 30 if near and near[min(2, len(near) - 1)]['distance_km'] < 25 else 60
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=1)
        d.ellipse((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), outline=1)
        for k in range(0, 360, 30):         # graduations
            a = math.radians(k - 90)
            d.point((cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)), fill=1)
        d.rectangle((cx - 3, cy - r - 1, cx + 3, cy - r + 7), fill=0)
        text_c(d, cx, cy - r - 2, 'N', TINY)
        sweep = (now.second * 6 + now.microsecond / 1e6 * 6) * 4 % 360   # un tour / 15 s
        a = math.radians(sweep - 90)
        d.line((cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)), fill=1)
        d.point((cx, cy), fill=1)
        for p in near:
            if p['distance_km'] > rng:
                continue
            rad = math.radians((p.get('bearing') or 0) - 90)
            k = p['distance_km'] / rng * (r - 3)
            plane_icon(d, cx + k * math.cos(rad), cy + k * math.sin(rad), p.get('track'), 2.4)
        # liste à droite
        d.text((68, 0), f'{rng} km', font=TINY, fill=1)
        text_r(d, 127, 0, f"{len([p for p in near if p['distance_km'] <= rng])} av", TINY)
        d.line((66, 11, 127, 11), fill=1)
        for i, p in enumerate(ac[:4]):
            y = 13 + i * 12
            d.text((68, y), name(p)[:7], font=TINY, fill=1)
            text_r(d, 127, y, f"{p['distance_km']:.0f}", TINY)

    # ---------- 3. Terrains surveillés
    def airports(self, d, s, sysi, now):
        aps = s.get('airports') or []
        header(d, 'TERRAINS', now.strftime('%H:%M'))
        if not aps:
            text_c(d, 64, 26, 'API radar absente', TINY)
            return
        for i, ap in enumerate(aps[:3]):
            y = 13 + i * 13
            icao = ap['icao']
            d.text((2, y), icao, font=S, fill=1)
            fin = next((a for a in s['aircraft'] if (a.get('final') or {}).get('airport') == icao), None)
            if fin:
                tag = f"FIN{fin['final']['rwy']} {name(fin)[:6]}"
                w = tw(d, tag, TINY)
                d.rectangle((126 - w - 3, y, 127, y + 10), fill=1)
                d.text((126 - w - 1, y), tag, font=TINY, fill=0)
            else:
                q = (ap.get('qnh') or {}).get('qnh')
                n = sum(1 for a in s['aircraft'] if a.get('airport') == icao and (a.get('airport_nm') or 99) < 5)
                d.text((34, y + 1), f"Q{q:.0f}" if q else 'Q---', font=TINY, fill=1)
                text_r(d, 126, y + 1, f'{n} av.', TINY)
        d.line((0, 52, W - 1, 52), fill=1)
        mv = (s.get('movements') or [None])[0]
        if mv:
            t = dt.datetime.fromtimestamp(mv['time']).strftime('%H:%M')
            lab = {'landing': 'ATT', 'takeoff': 'DEC', 'touch_and_go': 'T&G', 'pattern': 'TDP'}.get(mv['type'], '?')
            txt = f"{t} {lab} {mv.get('airport', '')}{(' ' + mv['runway']) if mv.get('runway') else ''}"
            d.text((2, 53), txt[:21], font=TINY, fill=1)
        else:
            d.text((2, 53), 'Aucun mouvement', font=TINY, fill=1)

    # ---------- 4. Système
    def system(self, d, s, sysi, now):
        header(d, 'SYSTEME', sysi.get('ip', ''))
        up = sysi.get('uptime') or 0
        rows = [
            ('CPU', f"{sysi['temp']:.0f}°C  {sysi['load']:.2f}" if sysi.get('temp') is not None else '--'),
            ('RAM', f"{sysi['ram']:.0f}%" if sysi.get('ram') is not None else '--'),
            ('Uptime', f"{int(up // 86400)}j {int(up % 86400 // 3600)}h{int(up % 3600 // 60):02d}"),
            ('RX', f"{sysi['msg_s']:.0f} msg/s" if sysi.get('msg_s') is not None else '--'),
            ('Sig/Bruit', f"{sysi['signal']:.0f}/{sysi['noise']:.0f}dB" if sysi.get('signal') is not None else '--'),
        ]
        for i, (k, v) in enumerate(rows):
            y = 12 + i * 10
            d.text((3, y), k, font=TINY, fill=1)
            text_r(d, 125, y, v, TINY)

    # ---------- Alerte (prioritaire)
    def alert(self, d, s, sysi, now, ac=None, kind=''):
        blink = now.microsecond < 500000
        d.rectangle((0, 0, W - 1, H - 1), outline=1)
        if blink:
            d.rectangle((2, 2, W - 3, 16), fill=1)
        text_c(d, 64, 3, kind, TINY, fill=0 if blink else 1)
        if ac:
            text_c(d, 64, 19, name(ac)[:10], L)
            text_c(d, 64, 39, ' '.join(x for x in (ac.get('registration'), ac.get('type')) if x)[:20], TINY)
            text_c(d, 64, 50, f"{ac['distance_km']:.0f} km  {fmt_alt(ac)}", TINY)

    def render_alert(self, snap, sysinfo, ac, kind, now=None):
        img = Image.new('1', (W, H), 0)
        self.alert(ImageDraw.Draw(img), snap, sysinfo, now or dt.datetime.now(), ac, kind)
        return img

    def no_data(self, d, now):
        header(d, 'ADS-B RADAR', now.strftime('%H:%M'))
        text_c(d, 64, 24, 'En attente', M)
        text_c(d, 64, 42, 'des donnees...', TINY)
