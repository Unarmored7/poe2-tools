"""
自动喝药模块

监控血条/蓝条，低于阈值时自动按键喝药。
"""

import tkinter as tk
from tkinter import TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y, HORIZONTAL, VERTICAL, CENTER, END, W, E, N, S, NW, SW, NE, SE, WORD, CHAR, DISABLED, NORMAL
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
import threading
import time
import numpy as np
import pyautogui
from PIL import ImageGrab

from poe2_tools.utils.image_processing import (
    calculate_hp_percentage,
    calculate_mp_percentage,
    is_valid_hp_bar,
    is_valid_mp_bar,
)
from poe2_tools.utils.region_selector import RegionSelector
from poe2_tools.utils.config_manager import config_manager
from poe2_tools.utils.ui_logger import UiLogger


class AutoPotionMonitor:
    """自动喝药监控器"""
    HP_KEY = "1"
    MP_KEY = "2"
    
    def __init__(self, root: tk.Tk | tk.Toplevel):
        """
        初始化自动喝药监控器
        
        Args:
            root: 父窗口
        """
        self.root = root
        self._init_vars()
        
    def _init_vars(self):
        """初始化变量"""
        # 加载配置
        config = config_manager.load_potion_config()
        
        # HP 设置
        self.hp_threshold = tk.IntVar(value=max(1, int(float(config.get("hp_threshold", 35)))))
        self.disable_hp = tk.BooleanVar(value=config.get("disable_hp", False))

        # MP 设置
        self.mp_threshold = tk.IntVar(value=max(1, int(float(config.get("mp_threshold", 35)))))
        self.disable_mp = tk.BooleanVar(value=config.get("disable_mp", False))

        # 定时喝药（全局）
        timed_interval = config.get("timed_potion_interval", "")
        self.timed_potion_interval = tk.StringVar(value=str(timed_interval) if timed_interval not in (None, 0) else "")
        self._last_timed_potion = 0

        # 全局设置
        self.check_interval = tk.IntVar(value=max(1, int(float(config.get("check_interval", 1)))))
        self._is_monitoring = False
        self._monitor_thread = None
        self._global_listener_running = False
        self._hotkey_enabled = False
        self._session_started_at = None
        self._loop_count = 0
        self._hp_press_count = 0
        self._mp_press_count = 0
        self._timed_trigger_count = 0
        self._error_count = 0

        self.current_hp = tk.StringVar(value="--%")
        self.current_mp = tk.StringVar(value="--%")

        # 区域设置
        hp_region = config.get("hp_region")
        self.hp_region = tuple(hp_region) if hp_region and len(hp_region) == 4 else None
        self.hp_region_display = tk.StringVar(value="--,--")
        
        mp_region = config.get("mp_region")
        self.mp_region = tuple(mp_region) if mp_region and len(mp_region) == 4 else None
        self.mp_region_display = tk.StringVar(value="--,--")
        
        # 区域选择器
        self._region_selector = RegionSelector(self.root)
        self._threshold_widgets = []
        self._input_anchor_width = 260
    
    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """
        创建 UI 界面 - Dashboard 布局
        """
        from poe2_tools.theme import ThemeManager

        # Main Container
        main = ttk.Frame(parent, style="Card.TFrame")
        main.pack(fill=BOTH, expand=True)



        # --- Content Area (2 Columns) ---
        content = ttk.Frame(main, style="Card.TFrame")
        content.pack(fill=BOTH, expand=True)

        # === Left Column: Status + Configuration ===
        left_col = ttk.Frame(content, style="Card.TFrame", width=350)
        left_col.pack(side=LEFT, fill=Y, expand=False, padx=(0, 0))
        left_col.pack_propagate(False)

        # 1. Status Panel（置顶）
        status_wrap = ttk.Frame(left_col, style="Card.TFrame")
        status_wrap.pack(fill=X, pady=(0, 15))

        header_height = 28

        status_header = ttk.Frame(status_wrap, style="Card.TFrame", height=header_height)
        status_header.pack(fill=X, pady=(0, 6))
        status_header.pack_propagate(False)
        ttk.Label(status_header, text="实时状态", style="Card.TLabel").pack(side=LEFT, padx=5)

        status_frame = ttk.Frame(status_wrap, style="Card.TFrame", padding=15)
        status_frame.pack(fill=X)
        
        # HP Display
        s_hp = ttk.Frame(status_frame, style="Card.TFrame")
        s_hp.pack(fill=X, pady=5)
        ttk.Label(
            s_hp,
            text="HP",
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            width=4,
            style="Content.TLabel",
            foreground=ThemeManager.COLOR_HP,
        ).pack(side=LEFT)
        ttk.Progressbar(s_hp, value=0, bootstyle="danger", length=200).pack(side=LEFT, padx=10)
        ttk.Label(
            s_hp,
            textvariable=self.current_hp,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            style="Content.TLabel",
            foreground=ThemeManager.COLOR_HP,
        ).pack(side=LEFT, padx=10)

        # MP Display
        s_mp = ttk.Frame(status_frame, style="Card.TFrame")
        s_mp.pack(fill=X, pady=5)
        ttk.Label(
            s_mp,
            text="MP",
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            width=4,
            style="Content.TLabel",
            foreground=ThemeManager.COLOR_MP,
        ).pack(side=LEFT)
        ttk.Progressbar(s_mp, value=0, bootstyle="info", length=200).pack(side=LEFT, padx=10)
        ttk.Label(
            s_mp,
            textvariable=self.current_mp,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            style="Content.TLabel",
            foreground=ThemeManager.COLOR_MP,
        ).pack(side=LEFT, padx=10)

        # 2. HP Settings
        self._create_section_frame(left_col, "生命设置", ThemeManager.COLOR_HP, self._build_hp_settings)

        # 3. MP Settings
        self._create_section_frame(left_col, "魔力设置", ThemeManager.COLOR_MP, self._build_mp_settings)
        
        # 4. Config Management
        self._create_section_frame(left_col, "配置管理", ThemeManager.COLOR_PRIMARY, self._build_config_settings)

        # 5. Global Settings（放底部，包含监控控制）
        self._create_section_frame(left_col, "全局设置", ThemeManager.COLOR_PRIMARY, self._build_global_settings)

        # === Right Column: Logs Only ===
        right_col = ttk.Frame(content, style="Card.TFrame")
        right_col.pack(side=LEFT, fill=BOTH, expand=True)

        # Logs（独占右侧）
        log_header = ttk.Frame(right_col, style="Card.TFrame", height=header_height)
        log_header.pack(fill=X, pady=(0, 6))
        log_header.pack_propagate(False)
        ttk.Label(log_header, text="运行日志", style="Card.TLabel").pack(side=LEFT, padx=5)
        ttk.Button(log_header, text="清空", command=self._clear_logs, style="link", width=6).pack(side=RIGHT)

        log_frame = ttk.Frame(right_col, style="Card.TFrame")
        log_frame.pack(fill=BOTH, expand=True)
        
        # Log Text
        self.log_scroll = ttk.Scrollbar(log_frame, orient=VERTICAL)
        self.log_scroll.pack(side=RIGHT, fill=Y)
        self.log_text = tk.Text(
            log_frame,
            height=10,
            state=DISABLED,
            wrap=WORD,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT), relief="flat",
            bg=ThemeManager.COLOR_BG_INPUT, fg=ThemeManager.COLOR_TEXT_MUTED,
            borderwidth=5,
            highlightthickness=0,
            yscrollcommand=self.log_scroll.set,
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.log_scroll.config(command=self.log_text.yview)
        self._logger = UiLogger(self.root, self.log_text, max_lines=600)

        self.timed_potion_interval.trace_add("write", lambda *_: self._refresh_threshold_controls_state())
        self._refresh_threshold_controls_state()

        self._start_global_listener()

        self.log("准备就绪。", "success")
        return main

    def _create_section_frame(self, parent, title, color, build_func):
        """Helper to create a unified section card"""
        from poe2_tools.theme import ThemeManager

        style = getattr(self.root, "style", ttk.Style())
        self._font_cn = (ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT)
        self._font_en = (ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT)

        style_name = f"Section{abs(hash(title))}.TLabelframe"
        style = getattr(self.root, "style", ttk.Style())
        style.configure(
            style_name,
            background=ThemeManager.COLOR_BG_CARD,
            bordercolor=ThemeManager.COLOR_BG_CARD,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            f"{style_name}.Label",
            background=ThemeManager.COLOR_BG_CARD,
            foreground=color,
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )

        frame = ttk.Labelframe(parent, text=title, style=style_name, padding=15)
        frame.pack(fill=X, pady=(0, 15))
        build_func(frame)

    def _build_hp_settings(self, parent):
        """HP Settings Grid"""
        grid_parent = ttk.Frame(parent, style="Content.TFrame", width=self._input_anchor_width)
        grid_parent.pack(anchor=W)

        # Grid Config: col 0=Label, col 1=Input
        grid_parent.columnconfigure(0, minsize=130)
        grid_parent.columnconfigure(1, weight=1)
        threshold_width = 8
        
        # Row 0: Region
        ttk.Label(grid_parent, text="监控区域：", style="Cn.Content.TLabel").grid(row=0, column=0, sticky=W, pady=(4, 8))
        self.hp_region_entry = ttk.Entry(
            grid_parent,
            textvariable=self.hp_region_display,
            width=threshold_width,
            justify=CENTER,
            style="Numeric.TEntry",
            font=self._font_en,
            state="readonly",
        )
        self.hp_region_entry.grid(row=0, column=1, sticky=E, padx=10, pady=(4, 8))
        self.hp_region_entry.bind("<Button-1>", lambda _e: self._select_hp_region())
        self._refresh_region_display_text("hp")
        
        # Row 1: Threshold
        ttk.Label(grid_parent, text="触发阈值（%）：", style="Cn.Content.TLabel").grid(row=1, column=0, sticky=W, pady=(0, 8))
        hp_threshold_entry = ttk.Entry(
            grid_parent,
            textvariable=self.hp_threshold,
            width=threshold_width,
            justify=CENTER,
            style="Numeric.TEntry",
            font=self._font_en,
        )
        hp_threshold_entry.grid(
            row=1, column=1, sticky=E, padx=10, pady=(0, 8)
        )
        self._threshold_widgets = getattr(self, "_threshold_widgets", [])
        self._threshold_widgets.append(hp_threshold_entry)

        # 定时配置已迁移到全局设置

    def _build_mp_settings(self, parent):
        """MP Settings Grid"""
        grid_parent = ttk.Frame(parent, style="Content.TFrame", width=self._input_anchor_width)
        grid_parent.pack(anchor=W)

        grid_parent.columnconfigure(0, minsize=130)
        grid_parent.columnconfigure(1, weight=1)
        threshold_width = 8
        
        # Row 0: Region
        ttk.Label(grid_parent, text="监控区域：", style="Cn.Content.TLabel").grid(row=0, column=0, sticky=W, pady=(4, 8))
        self.mp_region_entry = ttk.Entry(
            grid_parent,
            textvariable=self.mp_region_display,
            width=threshold_width,
            justify=CENTER,
            style="Numeric.TEntry",
            font=self._font_en,
            state="readonly",
        )
        self.mp_region_entry.grid(row=0, column=1, sticky=E, padx=10, pady=(4, 8))
        self.mp_region_entry.bind("<Button-1>", lambda _e: self._select_mp_region())
        self._refresh_region_display_text("mp")
        
        # Row 1: Threshold
        ttk.Label(grid_parent, text="触发阈值（%）：", style="Cn.Content.TLabel").grid(row=1, column=0, sticky=W, pady=(0, 8))
        mp_threshold_entry = ttk.Entry(
            grid_parent,
            textvariable=self.mp_threshold,
            width=threshold_width,
            justify=CENTER,
            style="Numeric.TEntry",
            font=self._font_en,
        )
        mp_threshold_entry.grid(
            row=1, column=1, sticky=E, padx=10, pady=(0, 8)
        )
        self._threshold_widgets = getattr(self, "_threshold_widgets", [])
        self._threshold_widgets.append(mp_threshold_entry)

        # 定时配置已迁移到全局设置

    def _build_global_settings(self, parent):
        """Global Settings"""
        layout = ttk.Frame(parent, style="Content.TFrame", width=self._input_anchor_width)
        layout.pack(anchor=W)

        row = ttk.Frame(layout, style="Content.TFrame")
        row.pack(fill=X)
        row.columnconfigure(0, minsize=130)
        row.columnconfigure(1, weight=1)
        ttk.Label(row, text="检测频率（秒）：", style="Cn.Content.TLabel").grid(row=0, column=0, sticky=W)
        check_entry = ttk.Entry(
            row,
            textvariable=self.check_interval,
            width=8,
            justify=CENTER,
            style="Numeric.TEntry",
            font=self._font_en,
        )
        check_entry.grid(row=0, column=1, sticky=E, padx=10)
        self._threshold_widgets = getattr(self, "_threshold_widgets", [])
        self._threshold_widgets.append(check_entry)

        timer_row = ttk.Frame(layout, style="Content.TFrame")
        timer_row.pack(fill=X, pady=(10, 0))
        timer_row.columnconfigure(0, minsize=130)
        timer_row.columnconfigure(1, weight=1)
        ttk.Label(timer_row, text="定时喝药间隔（秒）：", style="Cn.Content.TLabel").grid(row=0, column=0, sticky=W)
        ttk.Entry(
            timer_row,
            textvariable=self.timed_potion_interval,
            width=8,
            justify=CENTER,
            style="Numeric.TEntry",
            font=self._font_en,
        ).grid(row=0, column=1, sticky=E, padx=10)

        # 启停按钮统一放在导航栏底部

    def _build_config_settings(self, parent):
        """Config Management Section"""
        row = ttk.Frame(parent, style="Content.TFrame")
        row.pack(fill=X)
        ttk.Button(row, text="导入配置", command=self._import_config, style="outline", width=12).pack(side=LEFT, padx=(0, 10))
        ttk.Button(row, text="导出配置", command=self._export_config, style="outline", width=12).pack(side=LEFT)

    def _create_potion_ui(self, parent, key_var, thresh_var, disable_var, 
                          timer_var, timer_interval_var):
        """创建药水配置 UI"""
        f1 = ttk.Frame(parent, style="Card.TFrame")
        f1.pack(fill=X, pady=5)
        
        ttk.Label(f1, text="按键:", style="Content.TLabel").pack(side=LEFT)
        ttk.Entry(f1, textvariable=key_var, width=5).pack(side=LEFT, padx=5)
        
        ttk.Label(f1, text="阈值(%):", style="Content.TLabel").pack(side=LEFT, padx=(10, 0))
        ttk.Entry(f1, textvariable=thresh_var, width=5, justify=CENTER).pack(side=LEFT, padx=5)
        
        f2 = ttk.Frame(parent, style="Card.TFrame")
        f2.pack(fill=X, pady=5)
        ttk.Checkbutton(f2, text="禁用此药水", variable=disable_var, bootstyle="secondary").pack(side=LEFT)
        
        f3 = ttk.Frame(parent, style="Card.TFrame")
        f3.pack(fill=X, pady=5)
        ttk.Checkbutton(f3, text="定时(s):", variable=timer_var, bootstyle="secondary").pack(side=LEFT, padx=(0, 5))
        ttk.Entry(f3, textvariable=timer_interval_var, width=5, justify=CENTER).pack(side=LEFT)

    def log(self, msg: str, level: str = "info"):
        """添加日志消息"""
        if not hasattr(self, "_logger"):
            return
        level_map = {
            "debug": self._logger.debug,
            "info": self._logger.info,
            "success": self._logger.success,
            "warning": self._logger.warning,
            "error": self._logger.error,
        }
        level_map.get(level.lower(), self._logger.info)(msg)

    def _clear_logs(self):
        if hasattr(self, "_logger"):
            self._logger.clear()

    def _scroll_logs_bottom(self):
        if hasattr(self, "_logger"):
            self._logger.scroll_to_bottom()

    def _select_hp_region(self):
        """选择血条区域"""
        r = self._region_selector.select("请选择血条的竖条区域（窄而高）")
        if r:
            self.hp_region = r
            self._refresh_region_display_text("hp")
            self.log("血条区域已设", "success")

    def _select_mp_region(self):
        """选择蓝条区域"""
        r = self._region_selector.select("请选择蓝条的竖条区域（窄而高）")
        if r:
            self.mp_region = r
            self._refresh_region_display_text("mp")
            self.log("蓝条区域已设", "success")

    def _refresh_region_display_text(self, target: str):
        """在区域输入框中显示当前坐标。"""
        if target == "hp":
            region = self.hp_region
            display_var = self.hp_region_display
        else:
            region = self.mp_region
            display_var = self.mp_region_display

        if region:
            x, y, w, h = region
            display_var.set(f"{x},{y}")
        else:
            display_var.set("--,--")

    def _get_timed_interval_seconds(self, strict: bool = False):
        raw = self.timed_potion_interval.get().strip()
        if not raw:
            return None
        try:
            val = int(raw)
            if val <= 0:
                raise ValueError
            return val
        except Exception:
            if strict:
                raise ValueError("定时喝药间隔必须是大于 0 的整数秒")
            return None

    def _refresh_threshold_controls_state(self):
        timed_mode = self._get_timed_interval_seconds() is not None
        state = "disabled" if timed_mode else "normal"
        if hasattr(self, "hp_region_entry"):
            self.hp_region_entry.configure(state="readonly" if not timed_mode else "disabled")
        if hasattr(self, "mp_region_entry"):
            self.mp_region_entry.configure(state="readonly" if not timed_mode else "disabled")
        for widget in getattr(self, "_threshold_widgets", []):
            widget.configure(state=state)

    def _monitor_loop(self):
        """监控循环"""
        while self._is_monitoring:
            try:
                self._loop_count += 1
                timed_interval = self._get_timed_interval_seconds()
                if timed_interval is not None:
                    now = time.time()
                    if now - self._last_timed_potion >= timed_interval:
                        if not self.disable_hp.get():
                            pyautogui.press(self.HP_KEY)
                            self._hp_press_count += 1
                        if not self.disable_mp.get():
                            pyautogui.press(self.MP_KEY)
                            self._mp_press_count += 1
                        self.log(f"定时喝药触发（间隔 {timed_interval} 秒）", "info")
                        self._timed_trigger_count += 1
                        self._last_timed_potion = now
                    self.current_hp.set("--%")
                    self.current_mp.set("--%")
                    time.sleep(0.1)
                    continue

                current_hp_val = None
                current_mp_val = None
                now = time.time()

                screen = np.array(ImageGrab.grab())

                # HP 检测
                if self.hp_region:
                    x, y, w, h = self.hp_region
                    if x + w <= screen.shape[1] and y + h <= screen.shape[0]:
                        hp_img = screen[y:y + h, x:x + w]
                        if is_valid_hp_bar(hp_img):
                            current_hp_val = calculate_hp_percentage(hp_img)
                            self.current_hp.set(f"{current_hp_val:.1f}%")
                        else:
                            self.current_hp.set("--%")
                    else:
                        self.current_hp.set("--%")
                else:
                    self.current_hp.set("--%")

                # MP 检测
                if self.mp_region:
                    x, y, w, h = self.mp_region
                    if x + w <= screen.shape[1] and y + h <= screen.shape[0]:
                        mp_img = screen[y:y + h, x:x + w]
                        if is_valid_mp_bar(mp_img):
                            current_mp_val = calculate_mp_percentage(mp_img)
                            self.current_mp.set(f"{current_mp_val:.1f}%")
                        else:
                            self.current_mp.set("--%")
                    else:
                        self.current_mp.set("--%")
                else:
                    self.current_mp.set("--%")

                # 喝药逻辑
                if (current_hp_val is not None and 
                    not self.disable_hp.get() and 
                    current_hp_val < self.hp_threshold.get()):
                    pyautogui.press(self.HP_KEY)
                    self._hp_press_count += 1
                    self.log(f"HP {current_hp_val:.1f}% -> 按键 {self.HP_KEY}", "warning")

                if (current_mp_val is not None and 
                    not self.disable_mp.get() and 
                    current_mp_val < self.mp_threshold.get()):
                    pyautogui.press(self.MP_KEY)
                    self._mp_press_count += 1
                    self.log(f"MP {current_mp_val:.1f}% -> 按键 {self.MP_KEY}", "warning")

                time.sleep(max(1, int(self.check_interval.get())))

            except Exception as e:
                self._error_count += 1
                self.log(f"监控异常: {e}", "error")
                time.sleep(1)

    def _start_global_listener(self):
        """启动全局 F12 监听线程（开始/停止）。"""
        if self._global_listener_running:
            return

        try:
            import keyboard
        except Exception:
            self.log("keyboard 模块不可用，F12 热键不可用", "warning")
            return

        def listener():
            self._global_listener_running = True
            while self._global_listener_running:
                if not self._hotkey_enabled:
                    time.sleep(0.05)
                    continue
                if keyboard.is_pressed("f12"):
                    if self._is_monitoring:
                        self.root.after(0, self._toggle_monitoring)
                        self.root.after(80, self.root.deiconify)
                        self.root.after(120, self.root.lift)
                    else:
                        self.root.after(0, self.root.iconify)
                        self.root.after(0, self._toggle_monitoring)
                    time.sleep(0.5)
                time.sleep(0.05)

        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
        self.log("F12 热键已启用（开始/停止）", "success")

    def _toggle_monitoring(self):
        if self._is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def toggle_running(self):
        self._toggle_monitoring()

    def is_running(self) -> bool:
        return self._is_monitoring

    def set_hotkey_enabled(self, enabled: bool):
        self._hotkey_enabled = bool(enabled)

    def start_monitoring(self):
        """开始监控"""
        try:
            timed_interval = self._get_timed_interval_seconds(strict=True)
        except ValueError as e:
            self.log(str(e), "error")
            return

        if timed_interval is None and not self.hp_region and not self.mp_region:
            self.log("请先设置血条或蓝条区域！", "warning")
            return
        self._is_monitoring = True
        self._session_started_at = time.time()
        self._loop_count = 0
        self._hp_press_count = 0
        self._mp_press_count = 0
        self._timed_trigger_count = 0
        self._error_count = 0
        self._last_timed_potion = 0
        self.log("开始监控", "success")
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self._is_monitoring = False
        self.current_hp.set("--%")
        self.current_mp.set("--%")
        elapsed = 0.0
        if self._session_started_at is not None:
            elapsed = max(0.0, time.time() - self._session_started_at)
        self.log(
            (
                f"监控结束汇总：耗时 {elapsed:.1f}s，循环 {self._loop_count} 次，"
                f"HP触发 {self._hp_press_count} 次，MP触发 {self._mp_press_count} 次，"
                f"定时触发 {self._timed_trigger_count} 次，异常 {self._error_count} 次"
            ),
            "info",
        )
        self.log("监控已停止", "info")

    def get_config(self) -> dict:
        """获取配置"""
        return {
            "hp_region": list(self.hp_region) if self.hp_region else None,
            "mp_region": list(self.mp_region) if self.mp_region else None,
            "hp_key": self.HP_KEY,
            "hp_threshold": self.hp_threshold.get(),
            "disable_hp": self.disable_hp.get(),
            "mp_key": self.MP_KEY,
            "mp_threshold": self.mp_threshold.get(),
            "disable_mp": self.disable_mp.get(),
            "timed_potion_interval": self.timed_potion_interval.get().strip(),
            "check_interval": self.check_interval.get(),
        }

    def set_config(self, cfg: dict):
        """设置配置"""
        hp_region = cfg.get("hp_region")
        self.hp_region = tuple(hp_region) if hp_region else None
        
        mp_region = cfg.get("mp_region")
        self.mp_region = tuple(mp_region) if mp_region else None
        
        self.hp_threshold.set(max(1, int(float(cfg.get("hp_threshold", 35)))))
        self.disable_hp.set(cfg.get("disable_hp", False))

        self.mp_threshold.set(max(1, int(float(cfg.get("mp_threshold", 35)))))
        self.disable_mp.set(cfg.get("disable_mp", False))

        timed_value = cfg.get("timed_potion_interval", "")
        self.timed_potion_interval.set(str(timed_value) if timed_value not in (None, 0) else "")

        self.check_interval.set(max(1, int(float(cfg.get("check_interval", 1)))))

        # 更新 UI
        self._refresh_region_display_text("hp")
        self._refresh_region_display_text("mp")
        self._refresh_threshold_controls_state()

    def save_config(self):
        """保存配置"""
        config_manager.save_potion_config(self.get_config())

    def _export_config(self):
        """导出配置"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="potion_config.json"
        )
        if file_path:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.get_config(), f, indent=4, ensure_ascii=False)
            self.log(f"配置已导出: {file_path}", "success")

    def _import_config(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.set_config(cfg)
                self.log(f"配置已导入: {file_path}", "success")
            except Exception as e:
                self.log(f"导入失败: {e}", "error")
