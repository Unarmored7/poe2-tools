"""
自动喝药模块

监控血条/蓝条，低于阈值时自动按键喝药。
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
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


class AutoPotionMonitor:
    """自动喝药监控器"""
    
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
        self.hp_key = tk.StringVar(value=config.get("hp_key", "1"))
        self.hp_threshold = tk.DoubleVar(value=float(config.get("hp_threshold", 35.0)))
        self.disable_hp = tk.BooleanVar(value=config.get("disable_hp", False))
        self.enable_hp_timer = tk.BooleanVar(value=config.get("enable_hp_timer", False))
        self.hp_timer_interval = tk.DoubleVar(value=float(config.get("hp_timer_interval", 5.0)))
        self._last_hp_timer = 0

        # MP 设置
        self.mp_key = tk.StringVar(value=config.get("mp_key", "2"))
        self.mp_threshold = tk.DoubleVar(value=float(config.get("mp_threshold", 35.0)))
        self.disable_mp = tk.BooleanVar(value=config.get("disable_mp", False))
        self.enable_mp_timer = tk.BooleanVar(value=config.get("enable_mp_timer", False))
        self.mp_timer_interval = tk.DoubleVar(value=float(config.get("mp_timer_interval", 8.0)))
        self._last_mp_timer = 0

        # 全局设置
        self.check_interval = tk.DoubleVar(value=float(config.get("check_interval", 0.3)))
        self._is_monitoring = False
        self._monitor_thread = None

        self.current_hp = tk.StringVar(value="--%")
        self.current_mp = tk.StringVar(value="--%")

        # 区域设置
        hp_region = config.get("hp_region")
        self.hp_region = tuple(hp_region) if hp_region and len(hp_region) == 4 else None
        
        mp_region = config.get("mp_region")
        self.mp_region = tuple(mp_region) if mp_region and len(mp_region) == 4 else None
        
        # 区域选择器
        self._region_selector = RegionSelector(self.root)
    
    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """
        创建 UI 界面
        
        Args:
            parent: 父容器
            
        Returns:
            创建的框架
        """
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 手动选区按钮
        btn_frame1 = ttk.Frame(frame)
        btn_frame1.pack(fill=tk.X, pady=5)
        ttk.Button(
            btn_frame1, 
            text="🩸 手动选血条（请框选一个竖条区域）", 
            command=self._select_hp_region
        ).pack(side=tk.LEFT)
        self.hp_region_label = ttk.Label(btn_frame1, text="未设置", foreground="red")
        self.hp_region_label.pack(side=tk.LEFT, padx=10)
        
        if self.hp_region:
            self.hp_region_label.config(
                text=f"({self.hp_region[0]},{self.hp_region[1]}) "
                     f"{self.hp_region[2]}x{self.hp_region[3]}"
            )

        btn_frame2 = ttk.Frame(frame)
        btn_frame2.pack(fill=tk.X, pady=5)
        ttk.Button(
            btn_frame2, 
            text="💧 手动选蓝条（请框选一个竖条区域）", 
            command=self._select_mp_region
        ).pack(side=tk.LEFT)
        self.mp_region_label = ttk.Label(btn_frame2, text="未设置", foreground="blue")
        self.mp_region_label.pack(side=tk.LEFT, padx=10)
        
        if self.mp_region:
            self.mp_region_label.config(
                text=f"({self.mp_region[0]},{self.mp_region[1]}) "
                     f"{self.mp_region[2]}x{self.mp_region[3]}"
            )

        # 实时百分比显示
        pct_frame = ttk.Frame(frame)
        pct_frame.pack(fill=tk.X, pady=10)
        ttk.Label(pct_frame, text="血量:").pack(side=tk.LEFT)
        ttk.Label(
            pct_frame, 
            textvariable=self.current_hp, 
            font=("Arial", 10, "bold"), 
            foreground="red"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(pct_frame, text="蓝量:").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(
            pct_frame, 
            textvariable=self.current_mp, 
            font=("Arial", 10, "bold"), 
            foreground="blue"
        ).pack(side=tk.LEFT, padx=5)

        # HP 配置
        hp_frame = ttk.LabelFrame(frame, text="🩸 生命药水", padding=8)
        hp_frame.pack(fill=tk.X, pady=5)
        self._create_potion_ui(
            hp_frame, self.hp_key, self.hp_threshold,
            self.disable_hp, self.enable_hp_timer, self.hp_timer_interval
        )

        # MP 配置
        mp_frame = ttk.LabelFrame(frame, text="💧 魔法药水", padding=8)
        mp_frame.pack(fill=tk.X, pady=5)
        self._create_potion_ui(
            mp_frame, self.mp_key, self.mp_threshold,
            self.disable_mp, self.enable_mp_timer, self.mp_timer_interval
        )

        # 全局选项
        opt_frame = ttk.Frame(frame)
        opt_frame.pack(fill=tk.X, pady=10)
        ttk.Label(opt_frame, text="检测间隔(秒):").pack(side=tk.LEFT)
        ttk.Spinbox(
            opt_frame, 
            from_=0.1, to=1.0, increment=0.1, 
            textvariable=self.check_interval, 
            width=6
        ).pack(side=tk.LEFT, padx=5)

        # 导入导出按钮
        io_frame = ttk.Frame(frame)
        io_frame.pack(fill=tk.X, pady=5)
        ttk.Button(io_frame, text="💾 导出配置", command=self._export_config).pack(side=tk.LEFT)
        ttk.Button(io_frame, text="📂 导入配置", command=self._import_config).pack(side=tk.LEFT, padx=10)

        # 控制按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        self.start_btn = ttk.Button(
            btn_frame, text="▶ 开始", 
            command=self.start_monitoring, width=12
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(
            btn_frame, text="⏹ 停止", 
            command=self.stop_monitoring, 
            state=tk.DISABLED, width=12
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 日志
        log_frame = ttk.LabelFrame(frame, text="📋 日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log("✅ 自动喝药模块启动（支持红/绿血条）")
        
        return frame
    
    def _create_potion_ui(self, parent, key_var, thresh_var, disable_var, 
                          timer_var, timer_interval_var):
        """创建药水配置 UI"""
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="按键:").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=key_var, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="阈值(%):").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(row1, from_=1, to=100, textvariable=thresh_var, width=6).pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(row2, text="🚫 禁止喝此药", variable=disable_var).pack(side=tk.LEFT)
        ttk.Checkbutton(row2, text="⏱️ 定时喝药", variable=timer_var).pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(row2, text="每").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(
            row2, from_=1, to=60, increment=0.5, 
            textvariable=timer_interval_var, width=6
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="秒").pack(side=tk.LEFT)

    def log(self, msg: str):
        """添加日志消息"""
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

    def _select_hp_region(self):
        """选择血条区域"""
        r = self._region_selector.select("请选择血条的竖条区域（窄而高）")
        if r:
            self.hp_region = r
            self.hp_region_label.config(text=f"({r[0]},{r[1]}) {r[2]}x{r[3]}")
            self.log("✅ 血条区域已设")

    def _select_mp_region(self):
        """选择蓝条区域"""
        r = self._region_selector.select("请选择蓝条的竖条区域（窄而高）")
        if r:
            self.mp_region = r
            self.mp_region_label.config(text=f"({r[0]},{r[1]}) {r[2]}x{r[3]}")
            self.log("✅ 蓝条区域已设")

    def _monitor_loop(self):
        """监控循环"""
        while self._is_monitoring:
            try:
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
                    pyautogui.press(self.hp_key.get())
                    self.log(f"🩸 HP {current_hp_val:.1f}% → 按 '{self.hp_key.get()}'")

                if (current_mp_val is not None and 
                    not self.disable_mp.get() and 
                    current_mp_val < self.mp_threshold.get()):
                    pyautogui.press(self.mp_key.get())
                    self.log(f"💧 MP {current_mp_val:.1f}% → 按 '{self.mp_key.get()}'")

                # 定时喝药
                if (current_hp_val is not None and 
                    not self.disable_hp.get() and 
                    self.enable_hp_timer.get()):
                    if now - self._last_hp_timer >= self.hp_timer_interval.get():
                        pyautogui.press(self.hp_key.get())
                        self.log(f"⏱️ 定时喝 HP（每 {self.hp_timer_interval.get()}s）")
                        self._last_hp_timer = now

                if (current_mp_val is not None and 
                    not self.disable_mp.get() and 
                    self.enable_mp_timer.get()):
                    if now - self._last_mp_timer >= self.mp_timer_interval.get():
                        pyautogui.press(self.mp_key.get())
                        self.log(f"⏱️ 定时喝 MP（每 {self.mp_timer_interval.get()}s）")
                        self._last_mp_timer = now

                time.sleep(self.check_interval.get())

            except Exception as e:
                self.log(f"⚠️ 异常: {e}")
                time.sleep(1)

    def start_monitoring(self):
        """开始监控"""
        if not self.hp_region and not self.mp_region:
            messagebox.showwarning("警告", "请先设置血条或蓝条区域！")
            return
        self._is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("▶ 开始监控")
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self._is_monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.current_hp.set("--%")
        self.current_mp.set("--%")
        self.log("⏹ 已停止")

    def get_config(self) -> dict:
        """获取配置"""
        return {
            "hp_region": list(self.hp_region) if self.hp_region else None,
            "mp_region": list(self.mp_region) if self.mp_region else None,
            "hp_key": self.hp_key.get(),
            "hp_threshold": self.hp_threshold.get(),
            "disable_hp": self.disable_hp.get(),
            "enable_hp_timer": self.enable_hp_timer.get(),
            "hp_timer_interval": self.hp_timer_interval.get(),
            "mp_key": self.mp_key.get(),
            "mp_threshold": self.mp_threshold.get(),
            "disable_mp": self.disable_mp.get(),
            "enable_mp_timer": self.enable_mp_timer.get(),
            "mp_timer_interval": self.mp_timer_interval.get(),
            "check_interval": self.check_interval.get(),
        }

    def set_config(self, cfg: dict):
        """设置配置"""
        hp_region = cfg.get("hp_region")
        self.hp_region = tuple(hp_region) if hp_region else None
        
        mp_region = cfg.get("mp_region")
        self.mp_region = tuple(mp_region) if mp_region else None
        
        self.hp_key.set(cfg.get("hp_key", "1"))
        self.hp_threshold.set(cfg.get("hp_threshold", 35.0))
        self.disable_hp.set(cfg.get("disable_hp", False))
        self.enable_hp_timer.set(cfg.get("enable_hp_timer", False))
        self.hp_timer_interval.set(cfg.get("hp_timer_interval", 5.0))

        self.mp_key.set(cfg.get("mp_key", "2"))
        self.mp_threshold.set(cfg.get("mp_threshold", 35.0))
        self.disable_mp.set(cfg.get("disable_mp", False))
        self.enable_mp_timer.set(cfg.get("enable_mp_timer", False))
        self.mp_timer_interval.set(cfg.get("mp_timer_interval", 8.0))

        self.check_interval.set(cfg.get("check_interval", 0.3))

        # 更新 UI
        if self.hp_region and hasattr(self, 'hp_region_label'):
            x, y, w, h = self.hp_region
            self.hp_region_label.config(text=f"({x},{y}) {w}x{h}")
        if self.mp_region and hasattr(self, 'mp_region_label'):
            x, y, w, h = self.mp_region
            self.mp_region_label.config(text=f"({x},{y}) {w}x{h}")

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
            self.log(f"💾 配置已导出: {file_path}")

    def _import_config(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.set_config(cfg)
                self.log(f"📂 配置已导入: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")
