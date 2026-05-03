import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from gui import ClipVaultGUI
from clipboard_monitor import ClipboardMonitor


def main():
    # 先建表，再启动任何依赖数据库的组件
    init_db()

    root = tk.Tk()
    app = ClipVaultGUI(root)

    monitor = ClipboardMonitor()
    monitor.start()

    root.deiconify()

    try:
        root.mainloop()
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()
