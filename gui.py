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
HIGHLIGHT = "#f9e2af"


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

        self._clip_widgets = {}       # clip_id -> {frame, labels}
        self._new_clip_ids = set()    # 本刷新周期新出现的 clip
        self._search_after = None     # 搜索 debounce 定时器
        self._highlight_after = None  # 高亮消退定时器

        self._build_ui()
        self.refresh_list()

        self.root.bind("<Escape>", lambda e: self.root.withdraw())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)

    def _build_ui(self):
        # 搜索栏
        top_frame = tk.Frame(self.root, bg=BG)
        top_frame.pack(fill=tk.X, padx=8, pady=(8, 0))

        tk.Label(
            top_frame, text="搜索", font=FONT_SMALL, bg=BG, fg="#6c7086"
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.search_entry = tk.Entry(
            top_frame, bg=SURFACE, fg=FG, font=FONT,
            insertbackground=FG, relief=tk.FLAT, bd=6,
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        tk.Button(
            top_frame, text="清空", command=self._clear_history,
            bg="#f38ba8", fg=BG, font=FONT_SMALL,
            relief=tk.FLAT, bd=4, padx=8, cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(6, 0))

        # 列表区域
        list_frame = tk.Frame(self.root, bg=BG)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.canvas.yview)

        self.clip_list = tk.Frame(self.canvas, bg=BG)
        self.clip_list.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.clip_list, anchor="nw", tags="clip_list")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

        # 绑定 canvas 宽度变化以更新内部 frame 宽度
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 底部状态栏
        status_frame = tk.Frame(self.root, bg=BG)
        status_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.status_label = tk.Label(
            status_frame, text="", font=FONT_SMALL, bg=BG, fg="#6c7086")
        self.status_label.pack(side=tk.LEFT)
        tk.Label(
            status_frame, text="Win+Shift+V", font=FONT_SMALL, bg=BG, fg="#45475a"
        ).pack(side=tk.RIGHT)

    def _on_canvas_configure(self, event):
        """canvas 宽度变化时，更新内部 frame 宽度"""
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_search_key(self, event):
        # 200ms debounce 避免每次按键都刷新
        if self._search_after:
            self.root.after_cancel(self._search_after)
        self._search_after = self.root.after(200, self.refresh_list)

    def refresh_list(self):
        search = self.search_entry.get().strip()
        clips = get_clips(limit=100, search=search)

        current_ids = set(self._clip_widgets.keys())
        new_ids = {c[0] for c in clips}

        # 搜索模式下全量重建（排序/过滤完全变化）
        if search:
            for w in self.clip_list.winfo_children():
                w.destroy()
            self._clip_widgets.clear()
            self._new_clip_ids.clear()
            for clip in clips:
                self._add_clip_row(clip)
        else:
            # 增量更新：移除已删除的，添加新增的
            removed = current_ids - new_ids
            for cid in removed:
                if cid in self._clip_widgets:
                    self._clip_widgets[cid]["frame"].destroy()
                    del self._clip_widgets[cid]
                self._new_clip_ids.discard(cid)

            added = new_ids - current_ids
            for clip in clips:
                cid = clip[0]
                if cid in added:
                    self._new_clip_ids.add(cid)
                    self._add_clip_row(clip)

            # 300ms 后消退新 item 高亮
            if added and self._highlight_after:
                self.root.after_cancel(self._highlight_after)
            if added:
                self._highlight_after = self.root.after(
                    400, self._fade_highlights)

        count = get_count()
        self.status_label.config(text=f"共 {count} 条记录")

    def _add_clip_row(self, clip):
        clip_id, content, content_type, source_app, is_pinned, created_at = clip
        is_new = clip_id in self._new_clip_ids

        row = tk.Frame(self.clip_list, bg=SURFACE)
        row.pack(fill=tk.X, pady=1, padx=1)

        text_frame = tk.Frame(row, bg=SURFACE)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=5)

        preview = content.replace("\n", " ").replace("\t", " ")[:120]
        if is_pinned:
            preview = "◆ " + preview

        fg_color = HIGHLIGHT if is_new else (ACCENT if is_pinned else FG)
        bg_color = "#3d3a2a" if is_new else SURFACE
        font = FONT_BOLD if (is_pinned or is_new) else FONT

        content_lbl = tk.Label(
            text_frame, text=preview, font=font,
            bg=bg_color, fg=fg_color,
            anchor=tk.W, justify=tk.LEFT, wraplength=280,
        )
        content_lbl.pack(fill=tk.X)

        time_str = time.strftime("%m/%d %H:%M", time.localtime(created_at))
        meta_lbl = tk.Label(
            text_frame, text=time_str, font=FONT_SMALL,
            bg=bg_color, fg="#6c7086", anchor=tk.W,
        )
        meta_lbl.pack(fill=tk.X)

        # 绑定点击
        for w in (row, text_frame, content_lbl, meta_lbl):
            w.bind("<Button-1>", lambda e, c=content: self._copy_clip(c))
            w.bind("<Button-3>", lambda e, cid=clip_id, p=is_pinned:
                   self._context_menu(e, cid, p))

        # 右侧按钮
        btn_frame = tk.Frame(row, bg=SURFACE)
        btn_frame.pack(side=tk.RIGHT, padx=(0, 4))

        tk.Button(
            btn_frame, text="◆" if is_pinned else "◇",
            font=FONT_SMALL, bg=SURFACE,
            fg="#f9e2af" if is_pinned else "#6c7086",
            relief=tk.FLAT, bd=2, cursor="hand2",
            command=lambda cid=clip_id: self._toggle_pin(cid),
        ).pack(side=tk.TOP)

        tk.Button(
            btn_frame, text="×", font=FONT_SMALL, bg=SURFACE,
            fg="#6c7086", relief=tk.FLAT, bd=2, cursor="hand2",
            command=lambda cid=clip_id: self._delete_clip(cid),
        ).pack(side=tk.BOTTOM)

        self._clip_widgets[clip_id] = {
            "frame": row, "content_lbl": content_lbl,
            "meta_lbl": meta_lbl, "text_frame": text_frame,
        }

    def _fade_highlights(self):
        """消退新 item 的金色高亮"""
        faded = set()
        for cid in self._new_clip_ids:
            if cid in self._clip_widgets:
                w = self._clip_widgets[cid]
                # 如果该 item 是 pinned，保留蓝色；否则回退到普通
                # 这里简单处理：全部回退到正常颜色
                try:
                    w["content_lbl"].configure(fg=FG, bg=SURFACE)
                    w["meta_lbl"].configure(bg=SURFACE)
                    w["frame"].configure(bg=SURFACE)
                    w["text_frame"].configure(bg=SURFACE)
                    faded.add(cid)
                except tk.TclError:
                    pass
        self._new_clip_ids -= faded
        self._highlight_after = None

    def _copy_clip(self, content):
        pyperclip.copy(content)
        self.status_label.config(text="已复制到剪贴板！")
        self.root.after(1500, lambda: self.status_label.config(
            text=f"共 {get_count()} 条记录"))

    def _context_menu(self, event, clip_id, is_pinned):
        menu = tk.Menu(self.root, tearoff=0, bg=SURFACE, fg=FG, font=FONT_SMALL)
        menu.add_command(
            label="取消固定" if is_pinned else "固定",
            command=lambda: self._toggle_pin(clip_id))
        menu.add_command(
            label="删除", command=lambda: self._delete_clip(clip_id))
        menu.post(event.x_root, event.y_root)

    def _toggle_pin(self, clip_id):
        toggle_pin(clip_id)
        # 快速切换：直接修改颜色，减少闪烁感
        if clip_id in self._clip_widgets:
            w = self._clip_widgets[clip_id]
            try:
                is_now_pinned = "◆" in w["content_lbl"].cget("text")
                # 无法快速判断，全量刷新
            except Exception:
                pass
        self.refresh_list()

    def _delete_clip(self, clip_id):
        delete_clip(clip_id)
        # 立即从 widgets dict 移除，避免残留
        if clip_id in self._clip_widgets:
            self._clip_widgets[clip_id]["frame"].destroy()
            del self._clip_widgets[clip_id]
        count = get_count()
        self.status_label.config(text=f"共 {count} 条记录")

    def _clear_history(self):
        if messagebox.askyesno("确认", "删除所有非固定的剪贴板记录？"):
            clear_all()
            self.refresh_list()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh_list()
