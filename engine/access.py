"""Zugänge: Eine Kopie (Fork) macht nur Videos, solange ihr Zugang in der Liste des Admins gültig ist.

Die Liste liegt im Original-Repository (docs/admin/access.json, öffentlich lesbar, nur Prüfsummen der Codes). Die Kanal-App
trägt beim Freischalten die Zugangs-ID in die Einstellungen der Kopie ein (settings.access_id). Das Original selbst braucht keinen Zugang."""
import json
import os
import time
import urllib.request

from .state import cfg, log

ORIGINAL = "quatratkopf/autoshorts"
URL = "https://raw.githubusercontent.com/QuatratKopf/autoshorts/main/docs/admin/access.json"


def _fetch():
    req = urllib.request.Request(f"{URL}?t={int(time.time())}", headers={"User-Agent": "AutoShorts/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read(2_000_000).decode("utf-8"))


def blocked():
    """None, wenn Videos erlaubt sind – sonst der Grund (für das Protokoll)."""
    repo = (os.environ.get("GITHUB_REPOSITORY") or "").strip().lower()
    if not repo or repo == ORIGINAL:
        return None
    aid = str(cfg("access_id") or "").strip()
    if not aid:
        return "Diese Kopie ist noch nicht freigeschaltet (Zugangscode in der Kanal-App eingeben)"
    try:
        data = _fetch()
    except Exception as e:  # noqa: BLE001 – Liste gerade nicht erreichbar: nicht blockieren (GitHub-Störung)
        log(f"Zugangsliste nicht erreichbar ({str(e)[:80]}) – fahre fort")
        return None
    e = next((x for x in data.get("access", []) if isinstance(x, dict) and str(x.get("id")) == aid), None)
    if not e:
        return "Der Zugang dieser Kopie wurde gelöscht"
    if e.get("expires") and time.time() > float(e["expires"]):
        return "Der Zugang dieser Kopie ist abgelaufen"
    return None
