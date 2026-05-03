import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from gui import ClipVaultGUI
from clipboard_monitor import ClipboardMonitor


def main():
    init_db()

    root = tk.Tk()
    app = ClipVaultGUI(root)

    # 监控到新剪贴板内容时，通过 root.after 调度 GUI 刷新（tkinter 不是线程安全的）
    def on_new_clip(_content):
        root.after(0, app.refresh_list)

    monitor = ClipboardMonitor(on_new_clip=on_new_clip)
    monitor.start()

    root.deiconify()

    try:
        root.mainloop()
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()
