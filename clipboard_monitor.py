import threading
import time
import pyperclip
from database import add_clip, init_db


class ClipboardMonitor:
    def __init__(self, on_new_clip=None):
        self._running = False
        self._thread = None
        self._last_content = ""
        self._on_new_clip = on_new_clip
        init_db()

    def _poll(self):
        while self._running:
            try:
                content = pyperclip.paste()
                if content and content != self._last_content:
                    self._last_content = content
                    changed = add_clip(content)
                    if changed and self._on_new_clip:
                        self._on_new_clip(content)
            except Exception:
                pass
            time.sleep(0.3)

    def start(self):
        if self._running:
            return
        self._running = True
        self._last_content = pyperclip.paste() or ""
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
