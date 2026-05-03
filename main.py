import tkinter as tk
import sys
import os

# 添加到 path 以便直接运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import ClipVaultGUI
from clipboard_monitor import ClipboardMonitor

def main():
    root = tk.Tk()
    app = ClipVaultGUI(root)

    monitor = ClipboardMonitor()
    monitor.start()

    # 初始隐藏到托盘（简化处理：直接显示主窗口）
    root.deiconify()

    try:
        root.mainloop()
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()
