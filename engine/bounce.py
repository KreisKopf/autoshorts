"""Musik-Kugel: Eine Kugel fällt und springt – bei jedem Ton der Melodie trifft sie genau eine Glasscheibe, die klingt und zerspringt.

Wie es funktioniert: Aus der Melodie (Tonhöhe + Zeitpunkt jeder Note) wird rückwärts ein Flugweg gebaut. Zwischen zwei Tönen fliegt die
Kugel eine echte Wurfparabel (Schwerkraft); am Ort jedes Aufpralls steht eine Scheibe, deren Neigung genau die Richtungsänderung der
Kugel erklärt. Deshalb trifft jeder Aufprall exakt einen Ton. Der Ton wird selbst erzeugt (Glockenspiel-Klang + Glas-Klirren).

Nur gemeinfreie Melodien (Komponist seit über 70 Jahren tot bzw. Volkslied): bekannte Chart-Songs sind auch nachgespielt geschützt
(Content ID sperrt oder kassiert das Video)."""
import colorsys
import math
import random
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .state import log

W, H, FPS, SR = 1080, 1920, 30, 44100
G = 2600.0                       # Schwerkraft (px/s²)
BOX = (150, 520, 930, 1580)      # Bereich, in dem die Kugel springt (x0, y0, x1, y1)
BALL_R = 22
PANE_LEN, PANE_W = 118, 18
SHOW_AHEAD = 2.6                 # so lange vor dem Aufprall erscheint eine Scheibe (s)

# Melodien: (Name, Komponist/Herkunft, Tempo in Schlägen pro Minute, [(MIDI-Ton oder None für Pause, Dauer in Schlägen), ...])
_C = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def _n(s):
    """'E5' → MIDI-Nummer, 'r' → Pause."""
    if s in ("r", "-"):
        return None
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + _C[name]


def _seq(text):
    """'E5:.25 D#5:.25 …' → [(midi, dauer), …]"""
    out = []
    for tok in text.split():
        n, d = tok.split(":")
        out.append((_n(n), float(d)))
    return out


SONGS = {
    "fuer_elise": ("Für Elise", "Ludwig van Beethoven", 72, _seq(
        "E5:.25 D#5:.25 E5:.25 D#5:.25 E5:.25 B4:.25 D5:.25 C5:.25 A4:.75 C4:.25 E4:.25 A4:.25 B4:.75 E4:.25 G#4:.25 B4:.25 C5:.75 "
        "E4:.25 E5:.25 D#5:.25 E5:.25 D#5:.25 E5:.25 B4:.25 D5:.25 C5:.25 A4:.75 C4:.25 E4:.25 A4:.25 B4:.75 E4:.25 C5:.25 B4:.25 A4:1 "
        "r:.25 E5:.25 D#5:.25 E5:.25 D#5:.25 E5:.25 B4:.25 D5:.25 C5:.25 A4:.75 C4:.25 E4:.25 A4:.25 B4:.75 E4:.25 G#4:.25 B4:.25 C5:.75 "
        "E4:.25 E5:.25 D#5:.25 E5:.25 D#5:.25 E5:.25 B4:.25 D5:.25 C5:.25 A4:.75 C4:.25 E4:.25 A4:.25 B4:.75 E4:.25 C5:.25 B4:.25 A4:1.5")),
    "ode_freude": ("Ode an die Freude", "Ludwig van Beethoven", 132, _seq(
        "E4:1 E4:1 F4:1 G4:1 G4:1 F4:1 E4:1 D4:1 C4:1 C4:1 D4:1 E4:1 E4:1.5 D4:.5 D4:2 "
        "E4:1 E4:1 F4:1 G4:1 G4:1 F4:1 E4:1 D4:1 C4:1 C4:1 D4:1 E4:1 D4:1.5 C4:.5 C4:2 "
        "D4:1 D4:1 E4:1 C4:1 D4:1 E4:.5 F4:.5 E4:1 C4:1 D4:1 E4:.5 F4:.5 E4:1 D4:1 C4:1 D4:1 G3:2 "
        "E4:1 E4:1 F4:1 G4:1 G4:1 F4:1 E4:1 D4:1 C4:1 C4:1 D4:1 E4:1 D4:1.5 C4:.5 C4:2")),
    "bergkoenig": ("In der Halle des Bergkönigs", "Edvard Grieg", 132, _seq(
        ("B3:.5 C#4:.5 D4:.5 E4:.5 F#4:.5 D4:.5 F#4:1 F4:.5 C#4:.5 F4:1 E4:.5 C4:.5 E4:1 "
         "B3:.5 C#4:.5 D4:.5 E4:.5 F#4:.5 D4:.5 F#4:.5 B4:.5 A4:.5 F#4:.5 D4:.5 F#4:.5 A4:2 ") * 1
        + ("B4:.5 C#5:.5 D5:.5 E5:.5 F#5:.5 D5:.5 F#5:1 F5:.5 C#5:.5 F5:1 E5:.5 C5:.5 E5:1 "
           "B4:.5 C#5:.5 D5:.5 E5:.5 F#5:.5 D5:.5 F#5:.5 B5:.5 A5:.5 F#5:.5 D5:.5 F#5:.5 A5:2"))),
    "korobeiniki": ("Korobeiniki (die Tetris-Melodie)", "russisches Volkslied", 150, _seq(
        "E5:1 B4:.5 C5:.5 D5:1 C5:.5 B4:.5 A4:1 A4:.5 C5:.5 E5:1 D5:.5 C5:.5 B4:1.5 C5:.5 D5:1 E5:1 C5:1 A4:1 A4:1 r:1 "
        "r:.5 D5:1 F5:.5 A5:1 G5:.5 F5:.5 E5:1.5 C5:.5 E5:1 D5:.5 C5:.5 B4:1 B4:.5 C5:.5 D5:1 E5:1 C5:1 A4:1 A4:1 r:1 "
        "E5:1 B4:.5 C5:.5 D5:1 C5:.5 B4:.5 A4:1 A4:.5 C5:.5 E5:1 D5:.5 C5:.5 B4:1.5 C5:.5 D5:1 E5:1 C5:1 A4:1 A4:2")),
    "jingle_bells": ("Jingle Bells", "James Lord Pierpont", 160, _seq(
        "E4:1 E4:1 E4:2 E4:1 E4:1 E4:2 E4:1 G4:1 C4:1.5 D4:.5 E4:4 F4:1 F4:1 F4:1.5 F4:.5 F4:1 E4:1 E4:1 E4:.5 E4:.5 "
        "E4:1 D4:1 D4:1 E4:1 D4:2 G4:2 E4:1 E4:1 E4:2 E4:1 E4:1 E4:2 E4:1 G4:1 C4:1.5 D4:.5 E4:4 "
        "F4:1 F4:1 F4:1.5 F4:.5 F4:1 E4:1 E4:1 E4:.5 E4:.5 G4:1 G4:1 F4:1 D4:1 C4:4")),
    "nachtmusik": ("Eine kleine Nachtmusik", "Wolfgang Amadeus Mozart", 132, _seq(
        "G4:1 r:.5 D4:.5 G4:1 r:.5 D4:.5 G4:.5 D4:.5 G4:.5 B4:.5 D5:2 C5:1 r:.5 A4:.5 C5:1 r:.5 A4:.5 C5:.5 A4:.5 F#4:.5 A4:.5 D4:2 "
        "G4:1 r:.5 D4:.5 G4:1 r:.5 D4:.5 G4:.5 D4:.5 G4:.5 B4:.5 D5:2 C5:1 r:.5 A4:.5 C5:1 r:.5 A4:.5 C5:.5 A4:.5 F#4:.5 A4:.5 G4:2")),
    "funkel": ("Morgen kommt der Weihnachtsmann / Twinkle Twinkle", "französisches Volkslied", 120, _seq(
        "C5:1 C5:1 G5:1 G5:1 A5:1 A5:1 G5:2 F5:1 F5:1 E5:1 E5:1 D5:1 D5:1 C5:2 G5:1 G5:1 F5:1 F5:1 E5:1 E5:1 D5:2 "
        "G5:1 G5:1 F5:1 F5:1 E5:1 E5:1 D5:2 C5:1 C5:1 G5:1 G5:1 A5:1 A5:1 G5:2 F5:1 F5:1 E5:1 E5:1 D5:1 D5:1 C5:2")),
}


def notes(song, start=0.9):
    """[(Zeit s, MIDI)] der Melodie; kurze Melodien laufen zweimal (das zweite Mal etwas schneller)."""
    _name, _who, bpm, seq = SONGS[song]
    beat = 60.0 / bpm
    out, t = [], start
    total = sum(d for _, d in seq) * beat
    rounds = 2 if total < 26 else 1
    for r in range(rounds):
        b = beat * (0.88 if r else 1.0)
        for m, d in seq:
            if m is not None:
                out.append((round(t, 4), m))
            t += d * b
        t += b
    return out, t + 0.6


# ------------------------------------------------------------------ Flugweg

def path(hits, seed=0):
    """Aufprallpunkte und Geschwindigkeiten: zwischen zwei Tönen eine echte Wurfparabel, am Aufprall eine Scheibe, deren Lage die
    Richtungsänderung erklärt. Gibt [{t, p, v_in, v_out, n}] und die Startposition zurück."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = BOX
    start = (540.0 + rnd.uniform(-120, 120), y0 - 60.0)
    t_prev, p, v = 0.0, start, (0.0, 0.0)
    out = []
    recent = []
    for i, (t, _m) in enumerate(hits):
        dt = max(0.05, t - t_prev)
        if i == 0:                                       # erster Ton: aus der Ruhe fallen
            p_hit = (p[0] + v[0] * dt, p[1] + v[1] * dt + 0.5 * G * dt * dt)
            v_in = (v[0], v[1] + G * dt)
        else:
            p_hit, v_in = p, v
        # nächstes Ziel suchen: im Feld, nicht auf alten Scheiben, gleich schnell wie vorher (sieht nach echtem Abprall aus)
        nxt = hits[i + 1][0] if i + 1 < len(hits) else t + 0.6
        dn = max(0.05, nxt - t)
        reach = 90 + 1100 * min(dn, 0.7)
        best, best_s = None, 1e18
        sp_in = math.hypot(*v_in)
        for _ in range(140):
            tx = p_hit[0] + rnd.uniform(-1, 1) * reach
            ty = p_hit[1] + rnd.uniform(-0.8, 0.6) * reach
            if not (x0 <= tx <= x1 and y0 <= ty <= y1):     # außerhalb: verwerfen statt an den Rand ziehen (sonst Scheiben übereinander)
                continue
            vo = ((tx - p_hit[0]) / dn, (ty - p_hit[1] - 0.5 * G * dn * dn) / dn)
            sp = math.hypot(*vo)
            dv = (vo[0] - v_in[0], vo[1] - v_in[1])
            if math.hypot(*dv) < 120:                     # kaum Richtungswechsel: keine sichtbare Scheibe möglich
                continue
            # Scheitelpunkt der Parabel darf nicht über den Bildrand fliegen
            apex_y = p_hit[1] - (vo[1] ** 2) / (2 * G) if vo[1] < 0 else p_hit[1]
            s = abs(sp - sp_in) * (0.6 if i else 0.2) + max(0, 400 - apex_y) * 8 + max(0, sp - 2600) * 2
            s += max(0, 130 - math.hypot(tx - p_hit[0], ty - p_hit[1])) * 40   # nächste Scheibe nicht direkt neben der letzten
            s += sum(max(0, 170 - math.hypot(tx - q[0], ty - q[1])) * 8 for qt, q in recent if t - qt < SHOW_AHEAD + 0.4)   # Scheiben, die gleichzeitig zu sehen sind, überlappen nicht
            if s < best_s:
                best, best_s = (tx, ty, vo), s
        if best is None:
            tx, ty = 540.0, (y0 + y1) / 2
            best = (tx, ty, ((tx - p_hit[0]) / dn, (ty - p_hit[1] - 0.5 * G * dn * dn) / dn))
        v_out = best[2]
        dvx, dvy = v_out[0] - v_in[0], v_out[1] - v_in[1]
        ln = math.hypot(dvx, dvy) or 1.0
        n = (dvx / ln, dvy / ln)                          # Flächennormale der Scheibe (zeigt dahin, wohin die Kugel abprallt)
        out.append({"t": t, "p": p_hit, "v_in": v_in, "v_out": v_out, "n": n})
        recent.append((t, p_hit))
        p = (best[0], best[1])
        v = (v_out[0], v_out[1] + G * dn)
        t_prev = t
    return out, start


def ball_at(t, segs, start):
    """Position der Kugel zur Zeit t."""
    if not segs or t <= segs[0]["t"]:
        return (start[0], start[1] + 0.5 * G * t * t)
    prev = segs[0]
    for s in segs[1:]:
        if t < s["t"]:
            break
        prev = s
    dt = t - prev["t"]
    return (prev["p"][0] + prev["v_out"][0] * dt, prev["p"][1] + prev["v_out"][1] * dt + 0.5 * G * dt * dt)


# ------------------------------------------------------------------ Ton

def _freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def audio(hits, total, out: Path, seed=0):
    """Glockenspiel-Ton je Aufprall + leises Glasklirren + etwas Raumhall, als WAV."""
    rng = np.random.default_rng(seed)
    n = int((total + 1.5) * SR)
    y = np.zeros(n, dtype=np.float64)
    L = int(1.6 * SR)
    tt = np.arange(L) / SR
    for t, m in hits:
        f = _freq(m)
        note = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3.2) * 0.62
                + np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 6.0) * 0.22
                + np.sin(2 * np.pi * 3.01 * f * tt) * np.exp(-tt * 9.0) * 0.12
                + np.sin(2 * np.pi * 5.4 * f * tt) * np.exp(-tt * 22.0) * 0.06)
        att = np.minimum(1.0, tt / 0.003)
        note *= att
        k = int(0.07 * SR)                               # Glas-Klirren: kurzes, helles Rauschen
        crack = rng.standard_normal(k) * np.exp(-np.arange(k) / SR * 70)
        crack = np.diff(np.concatenate([[0.0], crack])) * 0.18
        i = int(t * SR)
        seg = note[: max(0, min(L, n - i))]
        y[i:i + len(seg)] += seg
        y[i:i + min(k, n - i)] += crack[: max(0, min(k, n - i))]
    ir_n = int(1.1 * SR)                                 # einfacher Raumhall
    ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 4.5) * 0.02
    ir[0] = 1.0
    nfft = 1 << int(math.ceil(math.log2(n + ir_n)))
    wet = np.fft.irfft(np.fft.rfft(y, nfft) * np.fft.rfft(ir, nfft), nfft)[:n]
    y = wet / max(1e-6, np.max(np.abs(wet))) * 0.85
    fade = int(0.8 * SR)
    y[-fade:] *= np.linspace(1, 0, fade)
    st = np.stack([y, y], axis=1)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------ Bild

def _hue_col(h, s=0.62, v=0.95):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def _background(seed):
    rnd = random.Random(seed)
    bg = Image.new("RGB", (W, H), (12, 12, 22))
    d = ImageDraw.Draw(bg)
    for y in range(0, H, 6):                             # dunkler Verlauf
        k = y / H
        d.rectangle((0, y, W, y + 6), fill=(int(14 + 10 * k), int(13 + 6 * k), int(26 + 16 * k)))
    for _ in range(90):                                  # feine Sterne
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(0.8, 2.2)
        c = rnd.randint(60, 120)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, c + 20))
    return bg


def _font(size):
    """Poppins wie im Rest der Videos; fehlt sie, eine fette Systemschrift – nie die winzige Pixel-Ersatzschrift."""
    from PIL import ImageFont
    from .overlays import font
    f = font(size)
    if isinstance(f, ImageFont.FreeTypeFont) and isinstance(getattr(f, "path", None), str):   # echte Schriftdatei, nicht der Ersatz
        return f
    for p in ("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def _text_center(d, y, text, size, fill):
    f = _font(size)
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2 + 3, y + 3), text, font=f, fill=(0, 0, 0))
    d.text(((W - w) / 2, y), text, font=f, fill=fill)


def render(song, out: Path, seed=0, title_top="Erkennst du das Lied?", reveal=True, work: Path = None):
    """Ganzes Video rendern (Bild + Ton). Gibt (Dauer, Pfad zum Vorschaubild) zurück. work = Ordner für Zwischendateien."""
    name, who, _bpm, _seq_ = SONGS[song]
    hits, total = notes(song)
    segs, start = path(hits, seed)
    rnd = random.Random(seed)
    hue0 = rnd.random()
    work = Path(work) if work else out.parent
    wav = work / "bounce.wav"
    audio(hits, total, wav, seed)
    bg = _background(seed)
    panes = []
    for i, s in enumerate(segs):
        nx, ny = s["n"]
        cx, cy = s["p"][0] - nx * (BALL_R + PANE_W / 2), s["p"][1] - ny * (BALL_R + PANE_W / 2)
        ang = math.atan2(ny, nx) + math.pi / 2           # Scheibe liegt quer zur Normale
        col = _hue_col(hue0 + 0.75 * i / max(1, len(segs)) + (hits[i][1] % 12) * 0.004)
        shards = [(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-260, 260), rnd.uniform(-420, -60), rnd.uniform(-9, 9), rnd.uniform(10, 26))
                  for _ in range(7)]
        panes.append({"t": s["t"], "c": (cx, cy), "a": ang, "col": col, "shards": shards, "v": s["v_out"]})
    n_frames = int(total * FPS)
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    trail = []
    thumb = work / "bounce_thumb.jpg"
    try:
        for fi in range(n_frames):
            t = fi / FPS
            fr = bg.copy()
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            d = ImageDraw.Draw(fr, "RGBA")
            for pn in panes:
                dtp = pn["t"] - t
                cx, cy = pn["c"]
                ca, sa = math.cos(pn["a"]), math.sin(pn["a"])
                if 0 < dtp <= SHOW_AHEAD:                # Scheibe wartet (blendet ein)
                    k = min(1.0, (SHOW_AHEAD - dtp) / 0.35)
                    hl = PANE_LEN / 2 * (0.6 + 0.4 * k)
                    pts = []
                    for sx, sy in ((-hl, -PANE_W / 2), (hl, -PANE_W / 2), (hl, PANE_W / 2), (-hl, PANE_W / 2)):
                        pts.append((cx + sx * ca - sy * sa, cy + sx * sa + sy * ca))
                    a = int(255 * k)
                    d.polygon(pts, fill=pn["col"] + (int(a * 0.55),), outline=pn["col"] + (a,), width=3)
                    for j in (-2, -1, 0, 1, 2):          # Glas-Lichtpunkte wie im Vorbild
                        px, py = cx + j * hl * 0.36 * ca, cy + j * hl * 0.36 * sa
                        d.ellipse((px - 2.5, py - 2.5, px + 2.5, py + 2.5), fill=(255, 255, 255, int(a * 0.8)))
                elif -0.9 < dtp <= 0:                    # zersprungen: Splitter fliegen und fallen
                    age = -dtp
                    if age < 0.18:                       # Lichtblitz am Aufprall
                        r = 30 + 260 * age
                        gd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=pn["col"] + (int(255 * (1 - age / 0.18)),), width=6)
                    for (ox, oy, vx, vy, rot, sz) in pn["shards"]:
                        sx_ = cx + ox * PANE_LEN * 0.4 + (vx + pn["v"][0] * 0.12) * age
                        sy_ = cy + oy * 10 + (vy + pn["v"][1] * 0.12) * age + 0.5 * G * 0.55 * age * age
                        rr = sz * (1 - age / 0.9)
                        ang = rot * age
                        tri = [(sx_ + rr * math.cos(ang + q), sy_ + rr * math.sin(ang + q)) for q in (0, 2.3, 4.1)]
                        d.polygon(tri, fill=pn["col"] + (int(230 * (1 - age / 0.9)),))
            bx, by = ball_at(t, segs, start)
            trail.append((bx, by))
            trail = trail[-8:]
            for j, (tx, ty) in enumerate(trail[:-1]):    # kurze Leuchtspur
                r = BALL_R * (0.35 + 0.65 * j / len(trail))
                d.ellipse((tx - r, ty - r, tx + r, ty + r), fill=(255, 255, 255, int(40 + 90 * j / len(trail))))
            gd.ellipse((bx - BALL_R * 2.2, by - BALL_R * 2.2, bx + BALL_R * 2.2, by + BALL_R * 2.2), fill=(255, 255, 255, 50))
            fr = Image.alpha_composite(fr.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(10))).convert("RGB")
            d = ImageDraw.Draw(fr)
            d.ellipse((bx - BALL_R, by - BALL_R, bx + BALL_R, by + BALL_R), fill=(250, 250, 245))
            if reveal and t > total - 3.2:               # Auflösung am Ende
                _text_center(d, 180, name, 64, (255, 230, 120))
                _text_center(d, 262, who, 40, (220, 220, 230))
            else:
                _text_center(d, 180, title_top, 64, (255, 255, 255))
                _text_center(d, 262, "Jede Scheibe ist ein Ton", 40, (200, 200, 215))
            if fi == int(min(total * 0.4, 8) * FPS):
                fr.save(thumb, quality=90)
            ff.stdin.write(fr.tobytes())
        ff.stdin.close()
        if ff.wait() != 0:
            raise RuntimeError("ffmpeg (Musik-Kugel) fehlgeschlagen")
    finally:
        if ff.poll() is None:
            ff.kill()
    log(f"Musik-Kugel: {name} – {len(hits)} Töne, {total:.0f} s")
    return total, thumb


def pick_song(used):
    """Melodie, die am längsten nicht dran war."""
    order = list(SONGS)
    random.shuffle(order)
    return sorted(order, key=lambda s: used.index(s) if s in used else -1)[0]


def meta(song):
    """Titel, Beschreibung, Hashtags fürs Hochladen (Name des Lieds erst in der Beschreibung – im Video wird geraten)."""
    name, who, _b, _s = SONGS[song]
    titles = ["Erkennst du dieses Lied? 🎵", "Diese Kugel spielt ein Lied, das jeder kennt", "Jede Scheibe ein Ton – welches Lied ist das?",
              "Nach drei Tönen weißt du es 🎶"]
    title = random.choice(titles)
    desc = (f"Jede Glasscheibe ist ein Ton – erkennst du das Lied, bevor die Kugel fertig ist? 🎵\n"
            f"Auflösung am Ende: {name} ({who}).\n"
            "Wie viele Töne hast du gebraucht? Schreib es in die Kommentare!")
    tags = ["#musik", "#melodie", "#satisfying", "#erkennstdudaslied", "#klassik", "#shorts"]
    return title, desc, tags, name
