"""统一弹窗工具。"""

from __future__ import annotations

import tkinter as tk

import ttkbootstrap as ttk

from poe2_tools.theme import ThemeManager
from poe2_tools.utils.app_assets import apply_window_icon


APP_NAME = "poe2-tools"


def _build_title(title: str | None) -> str:
    if not title:
        return APP_NAME
    if title.startswith(APP_NAME):
        return title
    return f"{APP_NAME} - {title}"


def _resolve_parent(parent: tk.Misc | None) -> tk.Misc | None:
    if parent is not None:
        return parent
    return getattr(tk, "_default_root", None)


def _show_modal(
    level: str,
    message: str,
    title: str,
    parent: tk.Misc | None,
) -> None:
    owner = _resolve_parent(parent)
    win = tk.Toplevel(owner) if owner is not None else tk.Toplevel()
    win.title(_build_title(title))
    win.resizable(False, False)
    win.configure(bg=ThemeManager.COLOR_BG_MAIN)
    apply_window_icon(win)

    if owner is not None:
        try:
            win.transient(owner)  # type: ignore[arg-type]
        except Exception:
            pass

    palette = {
        "info": ("INFO", "#9ec5fe"),
        "warning": ("WARNING", "#ffda6a"),
        "error": ("ERROR", "#f1aeb5"),
    }
    label_text, accent = palette.get(level, palette["info"])

    frame = ttk.Frame(win, style="Card.TFrame", padding=(18, 16, 18, 14))
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text=label_text,
        font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        fg=accent,
        bg=ThemeManager.COLOR_BG_CARD,
        anchor="w",
    ).pack(fill="x")

    tk.Label(
        frame,
        text=message,
        justify="left",
        wraplength=420,
        font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        fg=ThemeManager.COLOR_TEXT_MAIN,
        bg=ThemeManager.COLOR_BG_CARD,
        padx=0,
        pady=10,
    ).pack(fill="x")

    ttk.Button(frame, text="确定", style="Action.TButton", width=10, command=win.destroy).pack(anchor="e")

    win.update_idletasks()
    width = max(420, win.winfo_reqwidth())
    height = max(160, win.winfo_reqheight())

    if owner is not None and owner.winfo_exists():
        ox = owner.winfo_rootx()
        oy = owner.winfo_rooty()
        ow = owner.winfo_width()
        oh = owner.winfo_height()
        x = ox + max(0, (ow - width) // 2)
        y = oy + max(0, (oh - height) // 2)
    else:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2

    win.geometry(f"{width}x{height}+{x}+{y}")

    btn = frame.winfo_children()[-1]
    if isinstance(btn, ttk.Button):
        btn.focus_set()

    win.bind("<Escape>", lambda _e: win.destroy())
    win.bind("<Return>", lambda _e: win.destroy())

    try:
        win.grab_set()
    except Exception:
        pass
    win.wait_window()


class AppDialog:
    """统一风格的应用弹窗。"""

    @staticmethod
    def info(message: str, title: str = "提示", parent: tk.Misc | None = None) -> None:
        _show_modal("info", message, title, parent)

    @staticmethod
    def warning(message: str, title: str = "警告", parent: tk.Misc | None = None) -> None:
        _show_modal("warning", message, title, parent)

    @staticmethod
    def error(message: str, title: str = "错误", parent: tk.Misc | None = None) -> None:
        _show_modal("error", message, title, parent)
