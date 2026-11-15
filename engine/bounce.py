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
    "wiegenlied": ("Guten Abend, gut' Nacht (Wiegenlied)", "Johannes Brahms", 100, _seq(
        "E4:.5 E4:.5 G4:2 E4:.5 E4:.5 G4:2 E4:.5 G4:.5 C5:1 B4:1.5 A4:.5 A4:1 G4:1 D4:.5 E4:.5 F4:1 D4:1 D4:.5 E4:.5 F4:2 "
        "D4:.5 F4:.5 B4:.5 A4:.5 G4:1 B4:1 C5:2 C4:.5 C4:.5 C5:2 A4:.5 F4:.5 G4:2 E4:.5 C4:.5 F4:1 G4:1 A4:1 G4:2 "
        "C4:.5 C4:.5 C5:2 A4:.5 F4:.5 G4:2 E4:.5 C4:.5 F4:1 E4:1 D4:1 C4:3")),
    "greensleeves": ("Greensleeves", "englisches Volkslied", 112, _seq(
        "A4:1 C5:2 D5:1 E5:1.5 F5:.5 E5:1 D5:2 B4:1 G4:1.5 A4:.5 B4:1 C5:2 A4:1 A4:1.5 G#4:.5 A4:1 B4:2 G#4:1 E4:2 "
        "A4:1 C5:2 D5:1 E5:1.5 F5:.5 E5:1 D5:2 B4:1 G4:1.5 A4:.5 B4:1 C5:1.5 B4:.5 A4:1 G#4:1.5 F#4:.5 G#4:1 A4:3")),
    "saints": ("When the Saints Go Marching In", "Gospel (traditionell)", 150, _seq(
        "C4:1 E4:1 F4:1 G4:4 r:1 C4:1 E4:1 F4:1 G4:4 r:1 C4:1 E4:1 F4:1 G4:2 E4:2 C4:2 E4:2 D4:4 r:1 "
        "E4:1 E4:1 D4:1 C4:3 C4:1 E4:2 G4:2 G4:1 F4:3 r:1 E4:1 F4:1 G4:1 E4:2 C4:2 D4:2 C4:4")),
    "auld_lang_syne": ("Auld Lang Syne (Nehmt Abschied, Brüder)", "schottisches Volkslied", 100, _seq(
        "C4:1 F4:1.5 F4:.5 F4:1 A4:1 G4:1.5 F4:.5 G4:1 A4:1 F4:1.5 F4:.5 A4:1 C5:1 D5:3 D5:1 C5:1.5 A4:.5 A4:1 F4:1 "
        "G4:1.5 F4:.5 G4:1 A4:1 F4:1.5 D4:.5 D4:1 C4:1 F4:3")),
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


# ------------------------------------------------------------------ eigenes Lied (aus der App hochgeladen)

def _decode(path, sr=22050, start=0.0, dur=None):
    args = ["ffmpeg", "-v", "error", "-ss", f"{start:.2f}", "-i", str(path)] + (["-t", f"{dur:.2f}"] if dur else []) + \
           ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(args, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def song_hits(path, length=40.0):
    """Töne und Beats in einem Lied finden: den mitreißendsten Abschnitt (meist der Refrain: lauteste {length} s) und darin die
    deutlichen Einsätze (Spektral-Fluss mit beweglicher Schwelle). Gibt (Startzeit im Lied, Dauer, [(Zeit, Tonhöhe)]) zurück."""
    sr = 11025
    y = _decode(path, sr)
    if len(y) < sr * 8:
        raise RuntimeError("Lied zu kurz")
    total = len(y) / sr
    length = min(length, total - 1)
    hop = int(sr * 0.5)                                  # lautester Abschnitt (Refrain) – nicht ganz am Anfang oder Ende
    rms = np.sqrt(np.convolve(y ** 2, np.ones(hop) / hop, mode="valid")[::hop])
    win = int(length / 0.5)
    best, best_e = 0.0, -1.0
    for k in range(int(len(rms) * 0.12), max(int(len(rms) * 0.12) + 1, len(rms) - win)):
        e_ = float(np.mean(rms[k:k + win]))
        if e_ > best_e:
            best, best_e = k * 0.5, e_
    seg = y[int(best * sr): int((best + length) * sr)]
    n_fft, hp = 1024, 128
    frames = np.lib.stride_tricks.sliding_window_view(seg, n_fft)[::hp] * np.hanning(n_fft)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    logm = np.log1p(mag * 10)
    flux = np.maximum(0, np.diff(logm, axis=0)).sum(axis=1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-6)
    med = np.array([np.median(flux[max(0, i - 24): i + 24]) for i in range(len(flux))])
    dt = hp / sr
    peaks = [i for i in range(1, len(flux) - 1) if flux[i] > flux[i - 1] and flux[i] >= flux[i + 1] and flux[i] > med[i] + 0.9]
    peaks.sort(key=lambda i: -flux[i])
    chosen = []
    for i in peaks:                                      # stärkste Einsätze zuerst, mindestens 0,17 s Abstand, höchstens ~4 pro Sekunde
        tt = (i + 1) * dt + 0.67 * n_fft / sr             # Versatz des Analysefensters (gemessen: Einsatz liegt im hinteren Fensterteil)
        if all(abs(tt - c) >= 0.17 for c, _ in chosen):
            band = mag[i + 1][int(180 * n_fft / sr): int(1800 * n_fft / sr)]
            f = (np.argmax(band) + int(180 * n_fft / sr)) * sr / n_fft
            chosen.append((tt, int(round(69 + 12 * math.log2(max(f, 30) / 440)))))
        if len(chosen) >= length * 4:
            break
    chosen.sort()
    return best, length, chosen


def file_song(path, work, lead=0.9):
    """Eigenes Lied vorbereiten: Abschnitt schneiden (weich ein/aus), Töne finden, leises Glasklirren auf jeden Aufprall legen."""
    start, length, found = song_hits(path)
    hits = [(round(t + lead, 4), m) for t, m in found]
    total = lead + length + 0.6
    clip = Path(work) / "song_clip.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(path),
                    "-af", f"afade=t=in:d=0.4,afade=t=out:st={length - 1.5:.2f}:d=1.5,adelay={int(lead * 1000)}|{int(lead * 1000)},"
                           f"apad=pad_dur=0.6,loudnorm=I=-14:TP=-1.5", "-ac", "2", "-ar", str(SR), str(clip)], check=True)
    tink = Path(work) / "tink.wav"
    audio(hits, total, tink, 1)
    out = Path(work) / "bounce.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-i", str(tink), "-filter_complex",
                    "[1:a]volume=0.18[t];[0:a][t]amix=inputs=2:duration=first:normalize=0", str(out)], check=True)
    return hits, total, out


# ------------------------------------------------------------------ Flugweg

RESTITUTION = (0.86, 1.08)       # wie viel Schwung ein Abprall behält (Glas federt leicht nach)
SPRINGY = (1.0, 2.0)             # nur wenn ein langer Ton sonst nicht erreichbar ist: federnde Scheibe (Winkel bleibt echt)


def _reflect(v, n, e):
    """Echter Abprall: die Geschwindigkeit senkrecht zur Scheibe dreht um (mal e), die entlang der Scheibe bleibt."""
    vn = v[0] * n[0] + v[1] * n[1]
    return (v[0] - (1 + e) * vn * n[0], v[1] - (1 + e) * vn * n[1])


def _fly(p, v, dt):
    return (p[0] + v[0] * dt, p[1] + v[1] * dt + 0.5 * G * dt * dt), (v[0], v[1] + G * dt)


def _ok_target(q, v, dt):
    """Landet die Kugel im Feld und fliegt dabei nicht oben aus dem Bild?"""
    x0, y0, x1, y1 = BOX
    if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1):
        return False
    if v[1] < 0:                                         # steigt: der Scheitelpunkt darf nicht oben aus dem Bild (über den Titel) fliegen
        p_y = q[1] - v[1] * dt - 0.5 * G * dt * dt
        if p_y - v[1] ** 2 / (2 * G) < 380:
            return False
    return True


def _candidates(p, v_in, t, dn, rnd, recent):
    """Mögliche echte Abpraller an diesem Punkt, beste zuerst (erst normale, dann federnde Scheiben)."""
    x0, y0, x1, y1 = BOX
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sp_in = math.hypot(*v_in)
    a_in = math.atan2(-v_in[1], -v_in[0])                # Richtung, aus der die Kugel kommt
    out = []
    for e_rng in (RESTITUTION, SPRINGY):
        cands = []
        for _ in range(200):
            ang = a_in + rnd.uniform(-1.45, 1.45)        # Normale zeigt zur Kugel hin (sonst kein Aufprall)
            n = (math.cos(ang), math.sin(ang))
            if n[0] * v_in[0] + n[1] * v_in[1] > -0.15 * sp_in:
                continue
            vo = _reflect(v_in, n, rnd.uniform(*e_rng))
            q, v_next = _fly(p, vo, dn)
            if not _ok_target(q, vo, dn):
                continue
            sp = math.hypot(*vo)
            sc = max(0, sp - 2700) * 3 + max(0, 500 - sp) * 2
            sc += (abs(q[0] - cx) / (x1 - x0) + abs(q[1] - cy) / (y1 - y0)) * 120          # lieber in der Mitte bleiben
            sc += max(0, 130 - math.hypot(q[0] - p[0], q[1] - p[1])) * 30                 # nächste Scheibe nicht direkt daneben
            sc += sum(max(0, 170 - math.hypot(q[0] - r[0], q[1] - r[1])) * 8 for rt, r in recent if t - rt < SHOW_AHEAD + 0.4)
            cands.append((sc, n, vo, q, v_next))
        out += sorted(cands, key=lambda c: c[0])[:14]
    return out


MAX_AIR = 1.35                   # länger kann die Kugel nicht fliegen, ohne oben aus dem Bild zu steigen (Schwerkraft)


def with_ghosts(hits):
    """Lange Pausen (Haltetöne, Pausen, ruhige Stellen im Lied): stille Zwischen-Aufpralle einfügen (Tonhöhe None = kein Ton),
    damit die Kugel nie physikalisch unmöglich lange in der Luft hängt."""
    out = []
    for k, (t, m) in enumerate(hits):
        out.append((t, m))
        if k + 1 < len(hits):
            gap = hits[k + 1][0] - t
            n = int(gap / MAX_AIR)
            for j in range(1, n + 1):
                out.append((round(t + gap * j / (n + 1), 4), None))
    return out


def path(hits, seed=0):
    """Flugweg mit echter Physik: zwischen zwei Tönen eine Wurfparabel, an jedem Ton ein echter Abprall an einer Scheibe
    (Einfallswinkel = Ausfallswinkel, etwas Schwungverlust; nur wo ein langer Ton es verlangt, federt die Scheibe stärker).
    Gesucht wird je Ton die Neigung der Scheibe, mit der die Kugel genau zum nächsten Ton wieder auf eine Scheibe trifft – im Bild,
    nicht zu schnell, nicht auf anderen Scheiben. Findet sich keine, geht die Suche einen Ton zurück und probiert dort eine andere.
    Gibt [{t, p, v_in, v_out, n}] und die Startposition zurück."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = BOX
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    start = (cx + rnd.uniform(-120, 120), y0 - 60.0)
    p0, v0 = _fly(start, (0.0, 0.0), hits[0][0])
    N = len(hits)
    stack = []                                           # je Ton: {p, v_in, cands, idx}
    steps = 0
    i = 0
    while i < N:
        steps += 1
        if i == len(stack):
            p, v_in = (p0, v0) if i == 0 else (stack[i - 1]["cands"][stack[i - 1]["idx"]][3], stack[i - 1]["cands"][stack[i - 1]["idx"]][4])
            dn = max(0.05, (hits[i + 1][0] - hits[i][0]) if i + 1 < N else 0.7)
            recent = [(hits[k][0], stack[k]["p"]) for k in range(max(0, i - 14), i)]
            stack.append({"p": p, "v_in": v_in, "dn": dn, "cands": _candidates(p, v_in, hits[i][0], dn, rnd, recent), "idx": 0})
        fr = stack[i]
        if fr["idx"] < len(fr["cands"]) or i == 0 or steps > 6000:
            if fr["idx"] >= len(fr["cands"]):            # Notfall (praktisch nie): Ziel in der Mitte, Abprall nur ungefähr
                p, v_in, dn = fr["p"], fr["v_in"], fr["dn"]
                q = (cx + rnd.uniform(-150, 150), cy + rnd.uniform(-150, 150))
                vo = ((q[0] - p[0]) / dn, (q[1] - p[1] - 0.5 * G * dn * dn) / dn)
                dv = (vo[0] - v_in[0], vo[1] - v_in[1])
                ln = math.hypot(*dv) or 1.0
                fr["cands"].append((0, (dv[0] / ln, dv[1] / ln), vo, q, (vo[0], vo[1] + G * dn)))
                fr["idx"] = len(fr["cands"]) - 1
            i += 1
            continue
        stack.pop()                                      # keine Möglichkeit mehr: einen Ton zurück, dort die nächste Neigung probieren
        i -= 1
        stack[i]["idx"] += 1
        del stack[i + 1:]
    out = []
    for k, fr in enumerate(stack):
        _sc, n, vo, _q, _vn = fr["cands"][fr["idx"]]
        out.append({"t": hits[k][0], "p": fr["p"], "v_in": fr["v_in"], "v_out": vo, "n": n})
    return out, start


def _can_continue(p, v_in, hits, j, rnd):
    dn = max(0.05, (hits[j + 1][0] - hits[j][0]) if j + 1 < len(hits) else 0.7)
    sp_in = math.hypot(*v_in)
    a_in = math.atan2(-v_in[1], -v_in[0])
    for k in range(80):
        ang = a_in + rnd.uniform(-1.35, 1.35)
        n = (math.cos(ang), math.sin(ang))
        if n[0] * v_in[0] + n[1] * v_in[1] > -0.15 * sp_in:
            continue
        vo = _reflect(v_in, n, rnd.uniform(*(RESTITUTION if k < 50 else SPRINGY)))
        q, _v = _fly(p, vo, dn)
        if _ok_target(q, vo, dn):
            return True
    return False


def appear_times(segs, start):
    """Wann darf jede Scheibe erscheinen? Spätestens SHOW_AHEAD vor ihrem Ton – aber erst, wenn die Kugel nicht mehr durch ihren
    Platz fliegt (sonst flöge sie sichtbar durch eine Scheibe hindurch)."""
    out = []
    reach = BALL_R + PANE_W / 2 + 6
    for j, s in enumerate(segs):
        nx, ny = s["n"]
        c = (s["p"][0] - nx * (BALL_R + PANE_W / 2), s["p"][1] - ny * (BALL_R + PANE_W / 2))
        ux, uy = -ny, nx                                  # Richtung entlang der Scheibe
        appear = s["t"] - SHOW_AHEAD
        tt = max(0.0, appear)
        while tt < s["t"] - 0.04:
            bx, by = ball_at(tt, segs, start)
            dx, dy = bx - c[0], by - c[1]
            along = max(-PANE_LEN / 2, min(PANE_LEN / 2, dx * ux + dy * uy))
            if math.hypot(dx - along * ux, dy - along * uy) < reach:
                appear = tt + 0.05
            tt += 1 / 120
        out.append(min(appear, s["t"] - 0.08))
    return out


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
        if m is None:                                    # stiller Zwischen-Aufprall: kein Ton
            continue
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
    """Text mittig – wird kleiner und notfalls zweizeilig, damit er nie über den Bildrand läuft."""
    max_w = W - 90
    lines = [text]
    f = _font(size)
    while d.textlength(text, font=f) > max_w and size > 44:
        size -= 4
        f = _font(size)
    if d.textlength(text, font=f) > max_w:              # immer noch zu breit: an einem Leerzeichen nahe der Mitte umbrechen
        words = text.split()
        best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))), default=1)
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    for k, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        yy = y + k * int(size * 1.15) - (int(size * 0.55) if len(lines) > 1 else 0)
        d.text(((W - w) / 2 + 3, yy + 3), ln, font=f, fill=(0, 0, 0))
        d.text(((W - w) / 2, yy), ln, font=f, fill=fill)
    return len(lines)


def render(song, out: Path, seed=0, title_top="Erkennst du das Lied?", reveal=True, work: Path = None):
    """Ganzes Video rendern (Bild + Ton). Gibt (Dauer, Pfad zum Vorschaubild) zurück. work = Ordner für Zwischendateien."""
    work = Path(work) if work else out.parent
    if isinstance(song, dict) and song.get("remix"):     # Remix einer gemeinfreien Melodie: {"remix": Melodie, "style": Stil}
        from . import remix
        base = SONGS[song["remix"]]
        name, who = f"{base[0]} – {remix.STYLES[song['style']]['name']} Remix", base[1]
        wav = work / "bounce.wav"
        hits, total = remix.build(base, remix.KEYS[song["remix"]], song["style"], wav, seed=seed)
    elif isinstance(song, dict):                         # eigenes Lied: {"file", "name", "who"}
        name, who = song.get("name") or "?", song.get("who") or ""
        hits, total, wav = file_song(song["file"], work)
    else:
        name, who, _bpm, _seq_ = SONGS[song]
        hits, total = notes(song)
        wav = work / "bounce.wav"
        audio(hits, total, wav, seed)
    hits = with_ghosts(hits)
    segs, start = path(hits, seed)
    rnd = random.Random(seed)
    hue0 = rnd.random()
    bg = _background(seed)
    panes = []
    appears = appear_times(segs, start)
    for i, s in enumerate(segs):
        nx, ny = s["n"]
        cx, cy = s["p"][0] - nx * (BALL_R + PANE_W / 2), s["p"][1] - ny * (BALL_R + PANE_W / 2)
        ang = math.atan2(ny, nx) + math.pi / 2           # Scheibe liegt quer zur Normale
        col = _hue_col(hue0 + 0.75 * i / max(1, len(segs)) + ((hits[i][1] or 0) % 12) * 0.004)
        shards = [(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-260, 260), rnd.uniform(-420, -60), rnd.uniform(-9, 9), rnd.uniform(10, 26))
                  for _ in range(7)]
        panes.append({"t": s["t"], "c": (cx, cy), "a": ang, "col": col, "shards": shards, "v": s["v_out"], "show": s["t"] - appears[i]})
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
                if 0 < dtp <= pn["show"]:                # Scheibe wartet (blendet ein – erst wenn die Kugel nicht mehr durchfliegt)
                    k = min(1.0, (pn["show"] - dtp) / 0.2)
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
                n_l = _text_center(d, 180, name, 64, (255, 230, 120))
                _text_center(d, 262 + (40 if n_l > 1 else 0), who, 40, (220, 220, 230))
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


def user_songs():
    """Eigene Lieder aus dem Release „songs“ (in der App hochgeladen): [{"asset", "name", "who"}]. Dateiname „Künstler - Titel.mp3“."""
    import json
    import re
    try:
        r = subprocess.run(["gh", "release", "view", "songs", "--json", "assets"], capture_output=True, text=True, timeout=60)
        assets = json.loads(r.stdout or "{}").get("assets") or [] if r.returncode == 0 else []
    except Exception:  # noqa: BLE001
        return []
    out = []
    for a in assets:
        nm = str(a.get("name") or "")
        if not re.search(r"\.(mp3|m4a|wav|ogg|aac|flac)$", nm, re.I):
            continue
        stem = re.sub(r"\.[^.]+$", "", nm).replace(".", " ").replace("_", " ").strip()
        who, _, title = stem.partition(" - ") if " - " in stem else ("", "", stem)
        out.append({"asset": nm, "name": (title or stem).strip(), "who": who.strip()})
    return out


def fetch_user_song(song, work):
    subprocess.run(["gh", "release", "download", "songs", "-p", song["asset"], "-D", str(work), "--clobber"], check=True, capture_output=True, timeout=300)
    return {**song, "file": str(Path(work) / song["asset"])}


CC_QUERIES = ["remix", "electronic remix", "edm", "trap beat", "phonk", "house", "dubstep", "future bass", "dance remix", "synthwave",
              "chill remix", "drum and bass"]


def cc_track(used, work):
    """Freier Remix/Track von ccMixter oder Jamendo (über Openverse): nur CC0 oder CC BY – „nicht kommerziell“ (NC) und
    „keine Bearbeitung“ (ND) sind ausgeschlossen. CC BY verlangt Namensnennung: sie steht in credit und kommt in die Beschreibung."""
    import requests
    ua = {"User-Agent": "AutoShorts/1.0 (open source shorts generator)"}
    qs = CC_QUERIES[:]
    random.shuffle(qs)
    for q in qs[:5]:
        try:
            r = requests.get("https://api.openverse.org/v1/audio/", headers=ua, timeout=30,
                             params={"q": q, "license": "cc0,by", "category": "music", "source": "jamendo,ccmixter", "page_size": 20})
            if r.status_code != 200:
                log(f"Openverse „{q}“: HTTP {r.status_code}")
                continue
            res = r.json().get("results", [])
        except Exception as e:  # noqa: BLE001
            log(f"Openverse „{q}“: {str(e)[:100]}")
            continue
        random.shuffle(res)
        for it in res:
            lic = str(it.get("license") or "").lower()
            dur = (it.get("duration") or 0) / 1000
            aid = "cc:" + str(it.get("id"))
            if lic not in ("cc0", "by") or aid in used or not it.get("url") or not (50 <= dur <= 480) or (it.get("filesize") or 0) > 25_000_000:
                continue
            dest = Path(work) / ("cc_" + str(it["id"])[:8] + "." + (str(it.get("filetype") or "mp3").lower()[:4] or "mp3"))
            try:
                with requests.get(it["url"], headers=ua, timeout=90, stream=True) as d:
                    d.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in d.iter_content(65536):
                            f.write(chunk)
            except Exception as e:  # noqa: BLE001
                log(f"Download {it.get('title')}: {str(e)[:100]}")
                continue
            title = str(it.get("title") or "Track").strip()[:80]
            creator = str(it.get("creator") or "unbekannt").strip()[:60]
            lic_txt = "CC0" if lic == "cc0" else f"CC BY {it.get('license_version') or ''}".strip()
            link = it.get("foreign_landing_url") or it.get("url")
            log(f"Freier Track: „{title}“ von {creator} ({lic_txt}, {it.get('source')})")
            return {"file": str(dest), "name": title, "who": creator, "asset": aid,
                    "credit": f"Musik: „{title}“ von {creator} – {lic_txt} – {link}", "license": lic_txt}
    raise RuntimeError("Kein passender freier Track gefunden")


def pick_song(used):
    """Melodie, die am längsten nicht dran war."""
    order = list(SONGS)
    random.shuffle(order)
    return sorted(order, key=lambda s: used.index(s) if s in used else -1)[0]


def meta(song):
    """Titel, Beschreibung, Hashtags fürs Hochladen (Name des Lieds erst in der Beschreibung – im Video wird geraten)."""
    if isinstance(song, dict) and song.get("remix"):
        from . import remix
        style = remix.STYLES[song["style"]]["name"]
        name, who = f"{SONGS[song['remix']][0]} ({style} Remix)", SONGS[song["remix"]][1]
        title = random.choice([f"Bekanntes Lied als {style}-Remix – erkennst du es? 🎵", f"Dieses Lied kennt jeder – aber als {style} 🔥",
                               f"Jede Scheibe ein Ton: {style}-Remix eines Klassikers"])
        desc = (f"Ein Lied, das jeder kennt – als {style}-Remix, jede Glasscheibe ist ein Ton. Erkennst du es? 🎵\n"
                f"Auflösung am Ende: {SONGS[song['remix']][0]} ({who}).\n"
                "Welches Lied soll als Nächstes einen Remix bekommen? Schreib es in die Kommentare!")
        return title, desc, ["#musik", "#remix", f"#{style.lower().replace(' ', '').replace('-', '')}", "#satisfying", "#erkennstdudaslied", "#shorts"], name
    if isinstance(song, dict) and song.get("credit"):    # freier Track (ccMixter/Jamendo): Namensnennung ist Pflicht
        title = random.choice(["Diese Kugel spielt den ganzen Beat 🎧", "Jede Scheibe ein Beat – wie lange schaust du zu? 🎧",
                               "Kugel trifft jeden Beat 🔥", "Satisfying: Jede Scheibe ein Ton 🎶"])
        desc = ("Jede Glasscheibe ist ein Ton – die Kugel spielt den ganzen Track mit. 🎧\n"
                f"{song['credit']}\n"
                "Welche Musik soll die Kugel als Nächstes spielen? Schreib es in die Kommentare!")
        return title, desc, ["#musik", "#remix", "#beat", "#satisfying", "#oddlysatisfying", "#shorts"], song["name"]
    name, who = (song.get("name"), song.get("who") or "") if isinstance(song, dict) else SONGS[song][:2]
    titles = ["Erkennst du dieses Lied? 🎵", "Diese Kugel spielt ein Lied, das jeder kennt", "Jede Scheibe ein Ton – welches Lied ist das?",
              "Nach drei Tönen weißt du es 🎶"]
    title = random.choice(titles)
    desc = (f"Jede Glasscheibe ist ein Ton – erkennst du das Lied, bevor die Kugel fertig ist? 🎵\n"
            f"Auflösung am Ende: {name}" + (f" ({who})" if who else "") + ".\n"
            "Wie viele Töne hast du gebraucht? Schreib es in die Kommentare!")
    tags = ["#musik", "#melodie", "#satisfying", "#erkennstdudaslied", "#klassik", "#shorts"]
    return title, desc, tags, name
