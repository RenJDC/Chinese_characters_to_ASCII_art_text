#!/usr/bin/env python3
"""
汉字 → ASCII 艺术字 图形界面
基于 tkinter，全平台支持（macOS / Linux / Windows）
"""

import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
import platform
from char2ascii import convert, batch_convert, CHARSETS, find_font


# ─── 颜色主题 ─────────────────────────────────────────────────

COLORS = {
    "bg":       "#111827",
    "bg2":      "#1f2937",
    "bg3":      "#283548",
    "border":   "#374151",
    "text":     "#f9fafb",
    "text2":    "#d1d5db",
    "text3":    "#9ca3af",
    "accent":   "#818cf8",
    "accent2":  "#6366f1",
    "green":    "#34d399",
    "red":      "#f87171",
}


def _font_ok(path):
    """快速验证字体文件是否可被 PIL 加载"""
    try:
        from PIL import ImageFont
        ImageFont.truetype(path, 20)
        return True
    except Exception:
        return False


def scan_fonts():
    """扫描本地 fonts/ 目录和系统字体，返回 [(显示名, 路径), ...]"""
    fonts = []
    seen = set()

    # 项目 fonts/ 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_dir = os.path.join(script_dir, "fonts")
    if os.path.isdir(local_dir):
        # 优先字体列表（和 find_font 一致）
        preferred = [
            "NotoSansSC-Regular.otf",
            "NotoSansSC-Bold.otf",
            "NotoSansSC-Medium.otf",
            "SourceHanSansSC-Regular.otf",
            "WenQuanYiMicroHei.ttf",
        ]
        ordered = preferred + [f for f in sorted(os.listdir(local_dir))
                               if f.lower().endswith((".ttf", ".otf", ".ttc"))
                               and f not in preferred]
        for f in ordered:
            if not f.lower().endswith((".ttf", ".otf", ".ttc")):
                continue
            path = os.path.join(local_dir, f)
            if path in seen or not os.path.isfile(path):
                continue
            if not _font_ok(path):
                continue
            name = os.path.splitext(f)[0]
            fonts.append((f"[本地] {name}", path))
            seen.add(path)

    # 系统字体
    system = platform.system()
    if system == "Darwin":
        sys_fonts = [
            ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
            ("/System/Library/Fonts/STHeiti Medium.ttc", "STHeiti Medium"),
            ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti Light"),
            ("/System/Library/Fonts/Supplemental/Songti.ttc", "Songti"),
            ("/Library/Fonts/Arial Unicode.ttf", "Arial Unicode"),
        ]
    elif system == "Linux":
        sys_fonts = [
            ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYi Zen Hei"),
            ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", "WenQuanYi Micro Hei"),
            ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "Noto Sans CJK"),
            ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", "Noto Sans CJK"),
            ("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", "Noto Sans CJK"),
            ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "Droid Sans Fallback"),
        ]
    elif system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        sys_fonts = [
            (os.path.join(windir, "Fonts", "msyh.ttc"), "Microsoft YaHei"),
            (os.path.join(windir, "Fonts", "simhei.ttf"), "SimHei"),
            (os.path.join(windir, "Fonts", "simsun.ttc"), "SimSun"),
            (os.path.join(windir, "Fonts", "msyhbd.ttc"), "Microsoft YaHei Bold"),
        ]
    else:
        sys_fonts = []

    for path, name in sys_fonts:
        if os.path.isfile(path) and path not in seen and _font_ok(path):
            fonts.append((f"[系统] {name}", path))
            seen.add(path)

    return fonts


class Char2AsciiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("汉字 → ASCII 艺术字")
        self.root.geometry("1100x750")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLORS["bg"])

        # 状态
        self.charset_name = tk.StringVar(value="classic")
        self.font_var = tk.StringVar()
        self.width_var = tk.IntVar(value=40)
        self.gap_var = tk.IntVar(value=2)
        self.height_ratio_var = tk.DoubleVar(value=1.0)
        self.invert_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="就绪")

        # 扫描可用字体
        self.available_fonts = scan_fonts()
        if self.available_fonts:
            self.font_var.set(self.available_fonts[0][0])

        self._build_ui()
        self._apply_theme()

    # ─── 构建界面 ─────────────────────────────────────────────

    def _build_ui(self):
        # 顶部标题
        header = tk.Frame(self.root, bg=COLORS["bg2"], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(header, text="汉字 → ASCII 艺术字",
                         bg=COLORS["bg2"], fg=COLORS["accent"],
                         font=("Helvetica", 16, "bold"))
        title.pack(side="left", padx=20, pady=12)

        subtitle = tk.Label(header, text="Chinese Characters to ASCII Art",
                            bg=COLORS["bg2"], fg=COLORS["text3"],
                            font=("Helvetica", 10))
        subtitle.pack(side="left", padx=10, pady=12)

        # 主体区域：左侧控制面板 + 右侧预览
        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=16)

        # 左侧控制面板
        left = tk.Frame(body, bg=COLORS["bg"], width=320)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)

        self._build_input_section(left)
        self._build_charset_section(left)
        self._build_params_section(left)
        self._build_actions_section(left)

        # 右侧预览区
        right = tk.Frame(body, bg=COLORS["bg2"], relief="flat",
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        self._build_preview_section(right)

        # 底部状态栏
        footer = tk.Frame(self.root, bg=COLORS["bg2"], height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Label(footer, textvariable=self.status_var,
                 bg=COLORS["bg2"], fg=COLORS["text3"],
                 font=("Helvetica", 9)).pack(side="left", padx=12)

    def _build_input_section(self, parent):
        frame = tk.LabelFrame(parent, text=" 输入 ", bg=COLORS["bg"],
                              fg=COLORS["accent"], font=("Helvetica", 11, "bold"),
                              labelanchor="nw", relief="flat",
                              highlightbackground=COLORS["border"],
                              highlightthickness=1)
        frame.pack(fill="x", pady=(0, 12))

        self.input_entry = tk.Entry(frame, bg=COLORS["bg"], fg=COLORS["text"],
                                    insertbackground=COLORS["accent"],
                                    font=("Helvetica", 18), relief="flat",
                                    highlightbackground=COLORS["border"],
                                    highlightthickness=1)
        self.input_entry.pack(fill="x", padx=12, pady=(8, 4), ipady=8)

        hint = tk.Label(frame, text="输入汉字，支持多字并排",
                        bg=COLORS["bg"], fg=COLORS["text3"],
                        font=("Helvetica", 9))
        hint.pack(padx=12, pady=(0, 8), anchor="w")

    def _build_charset_section(self, parent):
        frame = tk.LabelFrame(parent, text=" 字符集风格 ", bg=COLORS["bg"],
                              fg=COLORS["accent"], font=("Helvetica", 11, "bold"),
                              labelanchor="nw", relief="flat",
                              highlightbackground=COLORS["border"],
                              highlightthickness=1)
        frame.pack(fill="x", pady=(0, 12))

        # 风格网格（3列）
        grid = tk.Frame(frame, bg=COLORS["bg"])
        grid.pack(fill="x", padx=12, pady=(8, 4))

        styles = list(CHARSETS.keys())
        cols = 3
        for i, name in enumerate(styles):
            row, col = divmod(i, cols)
            btn = tk.Radiobutton(
                grid, text=name, variable=self.charset_name, value=name,
                bg=COLORS["bg"], fg=COLORS["text2"],
                selectcolor=COLORS["bg2"],
                activebackground=COLORS["bg2"], activeforeground=COLORS["accent"],
                font=("Helvetica", 9), indicatoron=False,
                relief="flat", padx=6, pady=3,
                command=self._on_param_change
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="w")

        # 字符集预览
        self.charset_preview = tk.Label(frame, text="", bg=COLORS["bg"],
                                        fg=COLORS["text3"],
                                        font=("Helvetica", 9),
                                        wraplength=280, justify="left")
        self.charset_preview.pack(padx=12, pady=(4, 8), anchor="w")
        self._update_charset_preview()

    def _build_params_section(self, parent):
        frame = tk.LabelFrame(parent, text=" 参数 ", bg=COLORS["bg"],
                              fg=COLORS["accent"], font=("Helvetica", 11, "bold"),
                              labelanchor="nw", relief="flat",
                              highlightbackground=COLORS["border"],
                              highlightthickness=1)
        frame.pack(fill="x", pady=(0, 12))

        inner = tk.Frame(frame, bg=COLORS["bg"])
        inner.pack(fill="x", padx=12, pady=(8, 8))

        # 字体选择
        font_frame = tk.Frame(inner, bg=COLORS["bg"])
        font_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6))

        tk.Label(font_frame, text="字体", bg=COLORS["bg"], fg=COLORS["text2"],
                 font=("Helvetica", 10), width=5, anchor="w").pack(side="left")

        font_names = [f[0] for f in self.available_fonts] if self.available_fonts else ["无可用字体"]
        self.font_combo = ttk.Combobox(font_frame, textvariable=self.font_var,
                                       values=font_names, state="readonly",
                                       font=("Helvetica", 10))
        self.font_combo.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # 浏览按钮
        tk.Button(font_frame, text="...", bg=COLORS["bg2"], fg=COLORS["text2"],
                  font=("Helvetica", 10), relief="flat", padx=4, pady=0,
                  highlightbackground=COLORS["border"], highlightthickness=1,
                  command=self._browse_font).pack(side="right")

        # 宽度
        self._make_slider(inner, "宽度", self.width_var, 10, 100, 1)
        # 间距
        self._make_slider(inner, "间距", self.gap_var, -10, 10, 2)
        # 高度比
        self._make_slider(inner, "高度比", self.height_ratio_var, 0.3, 3.0, 3, resolution=0.1)

        # 反色
        invert_frame = tk.Frame(inner, bg=COLORS["bg"])
        invert_frame.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))

        tk.Checkbutton(invert_frame, text="反色（黑底白字）",
                       variable=self.invert_var,
                       bg=COLORS["bg"], fg=COLORS["text2"],
                       selectcolor=COLORS["bg2"],
                       activebackground=COLORS["bg"],
                       activeforeground=COLORS["accent"],
                       font=("Helvetica", 10),
                       command=self._on_param_change).pack(anchor="w")

    def _browse_font(self):
        path = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[("字体文件", "*.ttf *.otf *.ttc"), ("所有文件", "*.*")]
        )
        if path:
            name = f"[自定义] {os.path.splitext(os.path.basename(path))[0]}"
            if path not in [f[1] for f in self.available_fonts]:
                self.available_fonts.insert(0, (name, path))
                self.font_combo["values"] = [f[0] for f in self.available_fonts]
            self.font_var.set(name)

    def _make_slider(self, parent, label, var, from_, to_, row, resolution=None):
        tk.Label(parent, text=label, bg=COLORS["bg"], fg=COLORS["text2"],
                 font=("Helvetica", 10), width=5, anchor="w").grid(
            row=row, column=0, sticky="w", pady=3)

        scale_kw = dict(variable=var, from_=from_, to=to_,
                        orient="horizontal", bg=COLORS["bg"],
                        fg=COLORS["text"], troughcolor=COLORS["bg3"],
                        highlightthickness=0, sliderlength=16,
                        font=("Helvetica", 9), length=140,
                        command=lambda _: self._on_param_change())
        if resolution is not None:
            scale_kw["resolution"] = resolution
        scale = tk.Scale(parent, **scale_kw)
        scale.grid(row=row, column=1, columnspan=2, sticky="w", pady=3)

    def _build_actions_section(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill="x", pady=(0, 12))

        # 生成按钮
        gen_btn = tk.Button(frame, text="生成", bg=COLORS["accent"],
                            fg=COLORS["bg"], font=("Helvetica", 12, "bold"),
                            relief="flat", padx=20, pady=6,
                            activebackground=COLORS["accent2"],
                            activeforeground=COLORS["bg"],
                            cursor="hand2",
                            command=self._generate)
        gen_btn.pack(side="left", padx=(0, 8))

        # 复制按钮
        copy_btn = tk.Button(frame, text="复制", bg=COLORS["bg2"],
                             fg=COLORS["text"], font=("Helvetica", 12),
                             relief="flat", padx=20, pady=6,
                             highlightbackground=COLORS["border"],
                             highlightthickness=1,
                             activebackground=COLORS["bg3"],
                             cursor="hand2",
                             command=self._copy)
        copy_btn.pack(side="left", padx=(0, 8))

        # 清空按钮
        clear_btn = tk.Button(frame, text="清空", bg=COLORS["bg2"],
                              fg=COLORS["text2"], font=("Helvetica", 12),
                              relief="flat", padx=20, pady=6,
                              highlightbackground=COLORS["border"],
                              highlightthickness=1,
                              activebackground=COLORS["bg3"],
                              cursor="hand2",
                              command=self._clear)
        clear_btn.pack(side="left")

        # 保存引用，供 _set_buttons_state 使用
        self._action_buttons = [gen_btn, copy_btn, clear_btn]

    def _build_preview_section(self, parent):
        # 预览标题栏
        bar = tk.Frame(parent, bg=COLORS["bg3"])
        bar.pack(fill="x")

        tk.Label(bar, text="预览", bg=COLORS["bg3"], fg=COLORS["text2"],
                 font=("Helvetica", 10, "bold")).pack(side="left", padx=12, pady=6)

        # 预览文本区
        preview_frame = tk.Frame(parent, bg=COLORS["bg2"])
        preview_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.preview_text = tk.Text(
            preview_frame, bg=COLORS["bg"], fg=COLORS["green"],
            font=("Courier", 11), relief="flat", wrap="none",
            highlightbackground=COLORS["bg2"], highlightthickness=0,
            insertbackground=COLORS["green"], state="disabled"
        )

        # 滚动条
        scrollbar_y = ttk.Scrollbar(preview_frame, orient="vertical",
                                    command=self.preview_text.yview)
        scrollbar_x = ttk.Scrollbar(preview_frame, orient="horizontal",
                                    command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=scrollbar_y.set,
                                    xscrollcommand=scrollbar_x.set)

        self.preview_text.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

    # ─── 主题 ─────────────────────────────────────────────────

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TScrollbar",
                        background=COLORS["bg3"],
                        troughcolor=COLORS["bg"],
                        bordercolor=COLORS["bg"],
                        arrowcolor=COLORS["text3"])

    # ─── 事件处理 ─────────────────────────────────────────────

    def _on_param_change(self, value=None):
        self._update_charset_preview()

    def _update_charset_preview(self):
        name = self.charset_name.get()
        chars = CHARSETS.get(name, "")
        self.charset_preview.config(text=f"字符: {chars}")

    def _generate(self):
        text = self.input_entry.get().strip()
        if not text:
            self.status_var.set("请输入汉字")
            return

        self.status_var.set("生成中...")
        self._set_buttons_state("disabled")

        # 主线程读取所有参数，避免子线程访问 tkinter 变量
        font_path = None
        selected = self.font_var.get()
        for name, path in self.available_fonts:
            if name == selected:
                font_path = path
                break

        # 验证字体文件
        if font_path and not os.path.isfile(font_path):
            self._set_buttons_state("normal")
            self.status_var.set(f"字体文件不存在: {font_path}")
            return

        params = {
            "input_text": text,
            "width": self.width_var.get(),
            "charset_name": self.charset_name.get(),
            "font_path": font_path,
            "invert": self.invert_var.get(),
            "height_ratio": self.height_ratio_var.get(),
            "gap": self.gap_var.get(),
        }

        self.root.after(50, lambda: threading.Thread(
            target=self._do_generate, args=(text, params), daemon=True
        ).start())

    def _do_generate(self, text, params):
        try:
            font_path = params.get("font_path")
            if font_path and not os.path.isfile(font_path):
                self._safe_after(self._on_generate_done, None,
                                 f"字体文件不存在: {font_path}", params)
                return

            call_params = {k: v for k, v in params.items() if k != "input_text"}
            if len(text) == 1:
                single_params = {k: v for k, v in call_params.items() if k != "gap"}
                result = convert(text, **single_params)
            else:
                result = batch_convert(text, **call_params)

            self._safe_after(self._on_generate_done, result, None, params)
        except ValueError as e:
            self._safe_after(self._on_generate_done, None, str(e), params)
        except Exception as e:
            self._safe_after(self._on_generate_done, None,
                             f"生成失败: {type(e).__name__}: {e}", params)

    def _safe_after(self, callback, *args):
        try:
            self.root.after(0, callback, *args)
        except (RuntimeError, tk.TclError):
            pass

    def _on_generate_done(self, result, error, params):
        try:
            if error:
                self.status_var.set(f"错误: {error}")
                return

            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", result or "")
            self.preview_text.config(state="disabled")

            text = params.get("input_text", "")
            font_label = params.get("font_path", "") or "未找到"
            self.status_var.set(
                f"完成 | {len(text)}字 | {params['charset_name']} | "
                f"宽度{params['width']} | 字体: {os.path.basename(font_label)}"
            )
        finally:
            self._set_buttons_state("normal")

    def _set_buttons_state(self, state):
        for btn in getattr(self, "_action_buttons", []):
            try:
                btn.config(state=state)
            except tk.TclError:
                pass

    def _copy(self):
        content = self.preview_text.get("1.0", "end").rstrip()
        if not content:
            self.status_var.set("无内容可复制")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.status_var.set("已复制到剪贴板")
        except tk.TclError:
            self.status_var.set("复制失败，系统剪贴板不可用")

    def _clear(self):
        self.input_entry.delete(0, "end")
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.config(state="disabled")
        self.status_var.set("已清空")


def main():
    root = tk.Tk()
    Char2AsciiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
