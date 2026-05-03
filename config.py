import os
import json

APP_NAME = "ClipVault"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "clipboard.db")
CONFIG_PATH = os.path.join(APP_DIR, "settings.json")

FREE_MAX_ITEMS = 50
HOTKEY = "<Win>+<Shift>+V"
CHECK_INTERVAL_MS = 300

DEFAULT_SETTINGS = {
    "max_items": FREE_MAX_ITEMS,
    "auto_start": True,
    "theme": "dark",
    "language": "zh",
    "is_pro": False,
}


def load_settings():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    return dict(DEFAULT_SETTINGS)


def save_settings(s):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
