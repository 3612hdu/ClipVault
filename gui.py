import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import time
from database import get_clips, toggle_pin, delete_clip, clear_all, get_count

FONT = ("Microsoft YaHei UI", 10)
FONT_BOLD = ("Microsoft YaHei UI", 10, "bold")
FONT_SMALL = ("Microsoft YaHei UI", 8)
BG = "#1e1e2e"
FG = "#cdd6f4"
ACCENT = "#89b4fa"
SURFACE = "#313244"


class ClipVaultGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipVault")
        self.root.geometry("420x560")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(320, 300)

        try:
            self.root.iconbitmap("clipvault.ico")
        except Exception:
            pass

        self._setup_styles()
        self._build_ui()
        self.refresh_list()

        # 快捷键
        self.root.bind("<Escape>", lambda e: self.root.withdraw())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=FONT)
        style.configure("TButton", background=SURFACE, foreground=FG, font=FONT)
        style.configure("TEntry", fieldbackground=SURFACE, foreground=FG, font=FONT)

    def _build_ui(self):
        # 搜索栏
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=8, pady=(8, 0))

        ttk.Label(top_frame, text="搜索", font=FONT_SMALL).pack(side=tk.LEFT, padx=(0, 4))
        self.search_entry = tk.Entry(
            top_frame,
            bg=SURFACE,
            fg=FG,
            font=FONT,
            insertbackground=FG,
            relief=tk.FLAT,
            bd=6,
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        clear_btn = tk.Button(
            top_frame,
            text="清空",
            command=self._clear_history,
            bg="#f38ba8",
            fg=BG,
            font=FONT_SMALL,
            relief=tk.FLAT,
            bd=4,
            padx=8,
        )
        clear_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # 列表区域
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.clip_list = ttk.Frame(self.canvas)

        self.clip_list.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.clip_list, anchor="nw", tags="clip_list")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

        # 底部状态栏
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.status_label = ttk.Label(self.status_bar, text="", font=FONT_SMALL)
        self.status_label.pack(side=tk.LEFT)
        ttk.Label(self.status_bar, text="Win+Shift+V", font=FONT_SMALL).pack(side=tk.RIGHT)

    def refresh_list(self):
        for w in self.clip_list.winfo_children():
            w.destroy()

        search = self.search_entry.get().strip()
        clips = get_clips(limit=100, search=search)

        for clip in clips:
            clip_id, content, content_type, source_app, is_pinned, created_at = clip
            self._add_clip_row(clip_id, content, content_type, source_app, is_pinned, created_at)

        count = get_count()
        self.status_label.config(text=f"共 {count} 条记录")

    def _add_clip_row(self, clip_id, content, content_type, source_app, is_pinned, created_at):
        row = tk.Frame(self.clip_list, bg=SURFACE, bd=0, relief=tk.FLAT)
        row.pack(fill=tk.X, pady=2, padx=2)

        # 左侧内容区
        text_frame = tk.Frame(row, bg=SURFACE)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=4)

        # 截断显示
        preview = content.replace("\n", " ").replace("\t", " ")[:120]
        if is_pinned:
            preview = "  " + preview

        content_lbl = tk.Label(
            text_frame,
            text=preview,
            font=FONT_BOLD if is_pinned else FONT,
            bg=SURFACE,
            fg=ACCENT if is_pinned else FG,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=280,
        )
        content_lbl.pack(fill=tk.X)

        # 时间
        time_str = time.strftime("%m/%d %H:%M", time.localtime(created_at))
        meta_lbl = tk.Label(
            text_frame, text=time_str, font=FONT_SMALL, bg=SURFACE, fg="#6c7086", anchor=tk.W
        )
        meta_lbl.pack(fill=tk.X)

        # 绑定点击事件
        for w in (row, text_frame, content_lbl, meta_lbl):
            w.bind("<Button-1>", lambda e, c=content: self._copy_clip(c))
            w.bind("<Button-3>", lambda e, cid=clip_id, p=is_pinned: self._context_menu(e, cid, p))

        # 右侧按钮
        btn_frame = tk.Frame(row, bg=SURFACE)
        btn_frame.pack(side=tk.RIGHT, padx=(0, 4))

        pin_btn = tk.Button(
            btn_frame,
            text=" " if is_pinned else " ",
            font=FONT_SMALL,
            bg=SURFACE,
            fg="#f9e2af" if is_pinned else "#6c7086",
            relief=tk.FLAT,
            bd=2,
            command=lambda cid=clip_id: self._toggle_pin(cid),
        )
        pin_btn.pack(side=tk.TOP)

        del_btn = tk.Button(
            btn_frame,
            text="x",
            font=FONT_SMALL,
            bg=SURFACE,
            fg="#6c7086",
            relief=tk.FLAT,
            bd=2,
            command=lambda cid=clip_id: self._delete_clip(cid),
        )
        del_btn.pack(side=tk.BOTTOM)

    def _copy_clip(self, content):
        pyperclip.copy(content)
        self.status_label.config(text="已复制到剪贴板！")

    def _context_menu(self, event, clip_id, is_pinned):
        menu = tk.Menu(self.root, tearoff=0, bg=SURFACE, fg=FG, font=FONT_SMALL)
        menu.add_command(label="取消固定" if is_pinned else "固定", command=lambda: self._toggle_pin(clip_id))
        menu.add_command(label="删除", command=lambda: self._delete_clip(clip_id))
        menu.post(event.x_root, event.y_root)

    def _toggle_pin(self, clip_id):
        toggle_pin(clip_id)
        self.refresh_list()

    def _delete_clip(self, clip_id):
        delete_clip(clip_id)
        self.refresh_list()

    def _clear_history(self):
        if messagebox.askyesno("确认", "删除所有非固定的剪贴板记录？"):
            clear_all()
            self.refresh_list()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh_list()
