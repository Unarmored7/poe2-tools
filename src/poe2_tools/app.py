"""POE2 tools main application."""

from __future__ import annotations

import ctypes
import webbrowser

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, X, Y

from poe2_tools.auto_potion import AutoPotionMonitor
from poe2_tools.reforge import DivineReforgeManager, ReforgeManager
from poe2_tools.theme import ThemeManager
from poe2_tools.utils.app_assets import apply_window_icon


class CombinedApp:
    """Application shell with sidebar navigation."""

    def __init__(self, root: ttk.Window):
        self.root = root
        self.root.title("poe2-tools")
        self.root.geometry("1100x800")
        self.root.minsize(980, 700)

        self._set_windows_app_id()
        self._set_window_icon()

        ThemeManager.setup_styles(self.root.style)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._init_layout()
        self._init_modules()
        self._show_module("potion")
        self._poll_toggle_state()

    def _set_windows_app_id(self):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("poe2_tools.app.v1.0")
        except Exception:
            pass

    def _set_window_icon(self):
        apply_window_icon(self.root)

    def _init_layout(self):
        self.sidebar_frame = ttk.Frame(self.root, style="Sidebar.TFrame", width=200)
        self.sidebar_frame.pack(side=LEFT, fill=Y)
        self.sidebar_frame.pack_propagate(False)

        title_lbl = ttk.Label(
            self.sidebar_frame,
            text="正版\n乌萨奇",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE + 10, ThemeManager.FONT_WEIGHT),
            background=ThemeManager.COLOR_BG_SIDEBAR,
            foreground=ThemeManager.COLOR_TEXT_SIDEBAR,
        )
        title_lbl.pack(pady=(30, 30), padx=20, anchor="w")

        self.nav_btns = {}
        self._create_nav_btn("自动喝药", "potion")
        self._create_nav_btn("混沌石洗炼", "reforge")
        self._create_nav_btn("神圣石洗炼", "divine_reforge")

        spacer = ttk.Frame(self.sidebar_frame, style="Sidebar.TFrame")
        spacer.pack(fill=Y, expand=True)

        self.mod_ref_btn = ttk.Button(
            self.sidebar_frame,
            text="词条参考",
            style="outline",
            width=18,
            command=lambda: webbrowser.open("https://poe2db.tw/tw/Modifiers"),
        )
        self.mod_ref_btn.pack(fill=X, padx=10, pady=(0, 8))

        self.module_toggle_btn = ttk.Button(
            self.sidebar_frame,
            text="启动（F12）",
            style="Action.TButton",
            width=18,
            command=self._toggle_active_module,
        )
        self.module_toggle_btn.pack(fill=X, padx=10, pady=(0, 36))

        self.content_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=True)

    def _create_nav_btn(self, text: str, key: str):
        btn = ttk.Button(
            self.sidebar_frame,
            text=text,
            style="Nav.TButton",
            command=lambda k=key: self._show_module(k),
        )
        btn.pack(fill=X, pady=2, padx=10)
        self.nav_btns[key] = btn

    def _init_modules(self):
        self.potion_monitor = AutoPotionMonitor(self.root)
        self.reforge_manager = ReforgeManager(self.root)
        self.divine_reforge_manager = DivineReforgeManager(self.root)
        self.module_frames = {}
        self.active_module_key = "potion"

    def _sync_module_hotkeys(self, active_key: str):
        self.potion_monitor.set_hotkey_enabled(active_key == "potion")
        self.reforge_manager.set_hotkey_enabled(active_key == "reforge")
        self.divine_reforge_manager.set_hotkey_enabled(active_key == "divine_reforge")

    def _show_module(self, key: str):
        self.active_module_key = key
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.state(["selected"])
                btn.configure(style="Nav.TButton")
            else:
                btn.state(["!selected"])

        for widget in self.content_frame.winfo_children():
            widget.forget()

        if key not in self.module_frames:
            frame = ttk.Frame(self.content_frame, style="Card.TFrame")
            if key == "potion":
                self.potion_monitor.create_ui(frame)
            elif key == "reforge":
                self.reforge_manager.create_ui(frame)
            elif key == "divine_reforge":
                self.divine_reforge_manager.create_ui(frame)
            self.module_frames[key] = frame

        self.module_frames[key].pack(fill=BOTH, expand=True, padx=30, pady=30)
        self._sync_module_hotkeys(key)
        self._refresh_sidebar_toggle()

    def _get_active_manager(self):
        if self.active_module_key == "potion":
            return self.potion_monitor
        if self.active_module_key == "reforge":
            return self.reforge_manager
        if self.active_module_key == "divine_reforge":
            return self.divine_reforge_manager
        return None

    def _toggle_active_module(self):
        manager = self._get_active_manager()
        if manager is None:
            return
        manager.toggle_running()
        self.root.after(80, self._refresh_sidebar_toggle)

    def _refresh_sidebar_toggle(self):
        manager = self._get_active_manager()
        if manager is None:
            self.module_toggle_btn.configure(text="启动（F12）", style="Action.TButton")
            return

        if manager.is_running():
            self.module_toggle_btn.configure(text="停止（F12）", style="Action.Active.TButton")
        else:
            self.module_toggle_btn.configure(text="启动（F12）", style="Action.TButton")

    def _poll_toggle_state(self):
        self._refresh_sidebar_toggle()
        self.root.after(200, self._poll_toggle_state)

    def _on_closing(self):
        try:
            self.potion_monitor.save_config()
            self.reforge_manager.save_config()
            self.divine_reforge_manager.save_config()
        except Exception as e:
            print(f"Config save failed: {e}")
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()
