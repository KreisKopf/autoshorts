"""Neu einrichten: eine Kopie (Fork) des Repositorys für einen anderen Kanal auf null setzen.

Löscht in DIESER Kopie die Video-Liste, Zahlen, Warteschlange, Pläne, Drehbücher, Vorschaubilder und Anmeldungen und leert die
Kanal-Angaben (Client-IDs, Kanal-Namen). Behält Motor, Video-Arten, Klang-Bibliothek und gelernte Gegenstände. Vergibt ein neues
Kanal-Merkmal, damit die Kopie andere Themen, Figuren und Melodien wählt als das Original.

Sicherheitssperren: läuft nur auf GitHub, nie im Original-Repository, und nur mit dem Namen der Kopie als Bestätigung."""
import json
import os
import secrets
import shutil

from .state import CONFIG, DATA, DEFAULT_STATE, ROOT, STATE, STATS, VIDEOS, log, save

ORIGINAL = "quatratkopf/autoshorts"
# Kanal-Angaben, die zum alten Kanal gehören und in der Kopie leer starten
CHANNEL_KEYS = ("youtube_client_id", "tiktok_client_key", "tiktok_handle", "youtube_handle", "channel_name", "channel_focus")


def new_seed():
    return secrets.token_hex(4)


def reset(confirm: str):
    repo = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    if not repo:
        raise RuntimeError("„Neu einrichten“ läuft nur auf GitHub")
    if repo.lower() == ORIGINAL:
        raise RuntimeError("Das Original-Repository wird nie zurückgesetzt – nur eine eigene Kopie (Fork)")
    if (confirm or "").strip().lower() != repo.lower():
        raise RuntimeError(f"Bestätigung fehlt: als Thema genau „{repo}“ angeben")
    VIDEOS.clear()                                        # im Speicher leeren: main speichert am Ende alles
    STATE.clear()
    STATE.update(json.loads(json.dumps(DEFAULT_STATE)))
    STATS.clear()
    STATS.update({"v": {}, "ch": {}, "updated": 0})
    for name, empty in (("insights.json", {}), ("wishes.json", []), ("plans.json", {})):
        if (DATA / name).exists():
            save(name, empty)
    for d in (DATA / "scripts", ROOT / "docs" / "thumbs"):
        if d.is_dir():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitkeep").write_text("", encoding="utf-8")
    tok = ROOT / "tokens"
    for f in tok.glob("*.enc") if tok.is_dir() else []:
        f.unlink()
    tok.mkdir(exist_ok=True)
    (tok / ".gitkeep").write_text("", encoding="utf-8")
    st = CONFIG.setdefault("settings", {})
    for k in CHANNEL_KEYS:
        st[k] = ""
    st["channel_seed"] = new_seed()
    CONFIG["queue"] = []
    save("config.json", CONFIG)
    log(f"{repo} neu eingerichtet: Videos, Zahlen, Warteschlange und Anmeldungen geleert, Kanal-Merkmal {st['channel_seed']}")
    return st["channel_seed"]


UPSTREAM = "https://github.com/QuatratKopf/autoshorts.git"
# Was „Motor aktualisieren“ aus dem Original holt – nie Daten, Einstellungen, Anmeldungen oder Videos dieser Kopie
ENGINE_PATHS = ("engine", "assets", "music", "docs/data/shapes.json", "README.md")


def update_engine():
    """Kopie auf den neuesten Motor des Originals bringen (ohne „Sync fork“, das auch die Video-Daten des Originals mitbrächte)."""
    import subprocess
    repo = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    if not repo:
        raise RuntimeError("„Motor aktualisieren“ läuft nur auf GitHub")
    if repo.lower() == ORIGINAL:
        log("Das ist das Original – der Motor ist schon aktuell")
        return 0
    shapes_f = DATA / "shapes.json"
    try:                                                  # was diese Kopie selbst gelernt hat (fehlende Gegenstände nachgezeichnet)
        own = json.loads(shapes_f.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        own = {}
    subprocess.run(["git", "fetch", "-q", "--depth", "1", UPSTREAM, "main"], cwd=ROOT, check=True, timeout=300)
    subprocess.run(["git", "checkout", "FETCH_HEAD", "--", *ENGINE_PATHS], cwd=ROOT, check=True, timeout=120)
    try:                                                  # zusammenführen statt überschreiben: Gelerntes der Kopie bleibt, Neues vom Original kommt dazu
        merged = json.loads(shapes_f.read_text(encoding="utf-8"))
        kept = {k: v for k, v in own.items() if k not in merged}
        if kept and isinstance(merged, dict):
            merged.update(kept)
            save("shapes.json", merged)
            log(f"Eigene gelernte Gegenstände behalten: {len(kept)}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"Gelernte Gegenstände nicht zusammengeführt ({e})")
    changed = subprocess.run(["git", "status", "--porcelain", "--", *ENGINE_PATHS], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    log(f"Motor aus dem Original geholt: {len(changed)} Dateien neu oder geändert (Daten, Einstellungen und Videos bleiben)")
    return len(changed)
