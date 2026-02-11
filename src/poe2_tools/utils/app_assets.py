"""应用资源路径与窗口图标工具。"""

from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk


def resolve_app_icon_path() -> Path | None:
    """解析应用图标路径。"""
    base_dir = Path(__file__).resolve().parents[3]
    candidates: list[Path] = []

    # PyInstaller onefile: extracted runtime files live under sys._MEIPASS
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            base = Path(meipass)
            candidates.extend(
                [
                    base / "assets" / "favicon.ico",
                    base / "assets" / "icon.ico",
                    base / "favicon.ico",
                    base / "icon.ico",
                ]
            )

    candidates.extend(
        [
            base_dir / "assets" / "favicon.ico",
            base_dir / "assets" / "icon.ico",
            Path.cwd() / "assets" / "favicon.ico",
            Path.cwd() / "assets" / "icon.ico",
        ]
    )

    for icon_path in candidates:
        if icon_path.exists():
            return icon_path
    return None


def apply_window_icon(window: tk.Misc) -> bool:
    """为窗口设置应用图标。"""
    icon_path = resolve_app_icon_path()
    if icon_path is None:
        return False
    try:
        window.iconbitmap(str(icon_path))
        return True
    except Exception:
        return False
