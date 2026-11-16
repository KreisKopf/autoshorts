"""Gelernte Gegenstände aus Kopien (Forks) sicher in die eigene Bibliothek übernehmen – nur auf ausdrücklichen Knopfdruck des Admins.

Daten aus einer Kopie sind fremde Eingaben. Deshalb:
- nur aus echten Forks dieses Repositorys (Prüfung über die GitHub-API), nur die Datei docs/data/shapes.json, höchstens 2 MB;
- nur Gegenstände, deren Name bei uns noch nicht vergeben ist (weder eingebaut noch gelernt) – nichts wird überschrieben;
- Zusatz-Wörter (Aliase) nur, wenn sie Mehrzahl/Beugung desselben Wortes sind, nie fremde Wörter (sonst könnte „Haus“ umgelenkt werden);
- jede Zeichnung wird durch die strenge Prüfung der Bibliothek geschickt, probeweise gezeichnet und von der Bild-KI angesehen:
  nur wenn sie eindeutig harmlos das Genannte zeigt, kommt sie in die Bibliothek (ohne KI-Prüfung: nichts)."""
import base64
import io
import json
import os
import re
import urllib.request

import requests

from .state import cfg, load, log, save, secret

ORIGINAL = "QuatratKopf/autoshorts"
MAX_ITEMS = 20
CHECK = ("Du prüfst eine einfache Cartoon-Zeichnung für ein Erklärvideo. Antworte nur mit JSON {\"ok\": true|false, \"why\": \"kurz\"}. "
         "ok ist nur true, wenn das Bild eindeutig einen harmlosen Gegenstand zeigt, der zum Namen passt, und nichts davon enthält: "
         "Schrift, Zahlen, Symbole von Parteien, Ideologien oder Gruppen, Gesten, Waffen in bedrohlicher Darstellung, Körperteile, "
         "Anzügliches, Gewalt, Logos oder Marken. Im Zweifel false.")


def _repo_ok(full):
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}", full or ""):
        return None
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    r = requests.get(f"https://api.github.com/repos/{full}", timeout=20,
                     headers={"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {tok}"} if tok else {})})
    if r.status_code != 200:
        return None
    js = r.json()
    parent = ((js.get("parent") or {}).get("full_name") or "").lower()
    if not js.get("fork") or parent != (os.environ.get("GITHUB_REPOSITORY") or ORIGINAL).lower():
        return None
    return js.get("default_branch") or "main"


def _fetch_shapes(full, branch):
    url = f"https://raw.githubusercontent.com/{full}/{branch}/docs/data/shapes.json"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "AutoShorts/1.0"}), timeout=30) as r:
        raw = r.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("shapes.json zu groß")
    data = json.loads(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


def _looks_ok(name, png):
    key = secret("GEMINI_API_KEY")
    if not key:
        return False, "keine Bild-KI verfügbar"
    parts = [{"text": f"Name des Gegenstands: {name}"}, {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(png).decode()}}]
    for model in (cfg("gemini_model") or "gemini-3.5-flash", "gemini-2.5-flash"):
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              headers={"x-goog-api-key": key}, timeout=60,
                              json={"systemInstruction": {"parts": [{"text": CHECK}]}, "contents": [{"role": "user", "parts": parts}],
                                    "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}})
            if r.status_code != 200:
                continue
            txt = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"] if not p.get("thought"))
            js = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
            return js.get("ok") is True, str(js.get("why") or "")[:120]
        except Exception as e:  # noqa: BLE001
            log(f"Bild-Prüfung {model}: {str(e)[:100]}")
    return False, "Bild-KI nicht erreichbar"


def _plural_of(alias, name):
    """Nur Beugungen desselben Wortes (kompass → kompasse, kompassen), nie ein anderes Wort."""
    return alias.startswith(name) and 0 < len(alias) - len(name) <= 3 and re.fullmatch(r"(e|n|en|s|es|er|ern)", alias[len(name):]) is not None


def adopt(forks):
    from PIL import Image
    from .toon import extras, library, places
    mine = load("shapes.json", {})
    library.load_all(mine)
    taken_words = set(extras.PROPS) | set(extras.PROP_ALIASES) | set(extras.HELD) | set(library.LIB) | set(mine) \
        | set(places.PLACES) | set(places.ALIASES)
    added = 0
    for full in [f.strip() for f in str(forks or "").split(",") if f.strip()][:20]:
        branch = _repo_ok(full)
        if not branch:
            log(f"Übernehmen: {full} ist keine Kopie dieses Repositorys – übersprungen")
            continue
        try:
            theirs = _fetch_shapes(full, branch)
        except Exception as e:  # noqa: BLE001
            log(f"Übernehmen: {full} nicht lesbar ({str(e)[:100]})")
            continue
        for raw in list(theirs.values())[:200]:
            if added >= MAX_ITEMS:
                break
            item = library.clean(raw)
            if not item or item["name"] in taken_words:
                continue
            item["aliases"] = [a for a in item["aliases"] if a not in taken_words and _plural_of(a, item["name"])]
            lay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
            try:                                              # probeweise zeichnen: kaputte Zeichnungen fliegen raus
                from PIL import ImageDraw
                library._drawer(item)(ImageDraw.Draw(lay, "RGBA"), 540, 1.0)
                box = lay.getbbox()
                if not box:
                    continue
                buf = io.BytesIO()
                bg = Image.new("RGB", lay.size, (240, 240, 244))
                bg.paste(lay, (0, 0), lay)
                bg.crop(box).resize((min(512, box[2] - box[0]), min(512, box[3] - box[1]))).save(buf, "PNG")
            except Exception as e:  # noqa: BLE001
                log(f"Übernehmen: „{item['name']}“ lässt sich nicht zeichnen ({e})")
                continue
            ok, why = _looks_ok(item["name"], buf.getvalue())
            if not ok:
                log(f"Übernehmen: „{item['name']}“ aus {full} abgelehnt ({why})")
                continue
            mine[item["name"]] = {k: item[k] for k in ("name", "aliases", "height_m", "sky", "anim", "shapes")}
            taken_words |= {item["name"], *item["aliases"]}
            added += 1
            log(f"Übernehmen: „{item['name']}“ aus {full} geprüft und übernommen")
    if added:
        save("shapes.json", mine)
    log(f"Übernehmen: {added} Gegenstände neu in der Bibliothek")
    return added
