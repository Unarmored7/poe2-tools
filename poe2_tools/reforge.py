"""
装备洗练模块

通过图像模板匹配自动洗练装备。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import time
import os
import cv2
import numpy as np
import pyautogui

try:
    import keyboard
except ImportError:
    keyboard = None
    print("⚠️ keyboard 模块未安装，F12 中断功能不可用")

from poe2_tools.utils.image_processing import preprocess_image, load_and_preprocess_template
from poe2_tools.utils.region_selector import RegionSelector, CoordinatePicker
from poe2_tools.utils.config_manager import config_manager


def match_main_template(screen_gray: np.ndarray, 
                        templates_with_path: list, 
                        threshold: float, 
                        attempt_num: int) -> tuple:
    """
    主词条模板匹配
    
    Args:
        screen_gray: 预处理后的屏幕截图
        templates_with_path: [(路径, 模板), ...]
        threshold: 匹配阈值
        attempt_num: 尝试次数
        
    Returns:
        (是否匹配, 模板, 路径, 位置, 得分)
    """
    print(f"\n🔄 第 {attempt_num} 次洗练 - 主词条匹配:")
    best_score = -1
    best_template = None
    best_path = None
    best_loc = None
    
    for path, template in templates_with_path:
        h_tpl, w_tpl = template.shape[:2]
        h_scr, w_scr = screen_gray.shape
        
        if h_tpl > h_scr or w_tpl > w_scr:
            print(f" ❌ 模板 {os.path.basename(path)}: 尺寸过大（跳过）")
            continue
            
        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        status = "✅" if max_val >= threshold else "❌"
        print(f" 🔍 {os.path.basename(path)}: 得分={max_val:.4f} → {status}")
        
        if max_val >= threshold and max_val > best_score:
            best_score = max_val
            best_template = template
            best_path = path
            best_loc = max_loc
            
    if best_template is not None:
        print(f" 🎯 主词条匹配成功！模板: {os.path.basename(best_path)} | "
              f"得分={best_score:.4f} | 位置={best_loc}")
        return True, best_template, best_path, best_loc, best_score
        
    return False, None, None, None, -1


class ReforgeManager:
    """装备洗练管理器"""
    
    def __init__(self, root: tk.Tk | tk.Toplevel):
        """
        初始化洗练管理器
        
        Args:
            root: 父窗口
        """
        self.root = root
        self._init_vars()
        
    def _init_vars(self):
        """初始化变量"""
        config = config_manager.load_reforge_config()
        
        self.main_template_paths = config.get("main_template_paths", [])
        self.tier_template_path = config.get("tier_template_path")

        self.orb_pos = tk.StringVar(value=config.get("orb_pos", "(?, ?)"))
        self.equip_pos = tk.StringVar(value=config.get("equip_pos", "(?, ?)"))
        self.mod_region = tk.StringVar(value=config.get("mod_region", "(?, ?, ?, ?)"))
        self.main_threshold = tk.DoubleVar(value=float(config.get("main_threshold", 0.85)))
        self.tier_threshold = tk.DoubleVar(value=float(config.get("tier_threshold", 0.90)))
        self.max_attempts = tk.IntVar(value=int(config.get("max_attempts", 200)))

        self.delay_vars = {
            "orb_delay": tk.DoubleVar(value=float(config.get("orb_delay", 0.25))),
            "equip_click_delay": tk.DoubleVar(value=float(config.get("equip_click_delay", 0.75))),
            "alt_screenshot_delay": tk.DoubleVar(value=float(config.get("alt_screenshot_delay", 0.0))),
            "loop_random_max": tk.DoubleVar(value=float(config.get("loop_random_max", 0.02))),
        }
        
        self._region_selector = RegionSelector(self.root)
        self._coord_picker = CoordinatePicker(self.root)
        
    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """创建 UI 界面"""
        frame = ttk.Frame(parent, padding="12")
        frame.pack(fill=tk.BOTH, expand=True)

        # 坐标配置
        coords = [
            ("洗练石:", self.orb_pos, "orb"), 
            ("装备:", self.equip_pos, "equip"), 
            ("属性区域:", self.mod_region, "mod")
        ]
        for i, (label, var, key) in enumerate(coords):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            ttk.Entry(frame, textvariable=var, width=25, state='readonly').grid(row=i, column=1, padx=5)
            btn_text = "拾取" if key != "mod" else "拖选"
            ttk.Button(
                frame, text=btn_text, 
                command=lambda k=key: self._pick_coordinate(k)
            ).grid(row=i, column=2)

        # 主词条模板
        ttk.Label(frame, text="主词条模板 (PNG):").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.listbox_main = tk.Listbox(frame, height=4, width=65)
        self.listbox_main.grid(row=4, column=0, columnspan=3, pady=5)
        
        for path in self.main_template_paths:
            self.listbox_main.insert(tk.END, path)
            
        btn_f1 = ttk.Frame(frame)
        btn_f1.grid(row=5, column=0, columnspan=3, pady=5, sticky=tk.W)
        ttk.Button(btn_f1, text="添加", command=self._add_main_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f1, text="移除", command=self._remove_main_template).pack(side=tk.LEFT, padx=5)

        # T阶模板
        ttk.Label(frame, text="T阶图标模板 (PNG):").grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        self.tier_entry = ttk.Entry(frame, width=50, state='readonly')
        self.tier_entry.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        
        if self.tier_template_path:
            self.tier_entry.config(state='normal')
            self.tier_entry.delete(0, tk.END)
            self.tier_entry.insert(0, self.tier_template_path)
            self.tier_entry.config(state='readonly')
            
        ttk.Button(frame, text="选择", command=self._select_tier_template).grid(row=7, column=2)

        # 阈值
        ttk.Label(frame, text="主词条阈值:").grid(row=8, column=0, sticky=tk.W, pady=5)
        ttk.Scale(
            frame, from_=0.70, to=0.95, 
            variable=self.main_threshold, orient=tk.HORIZONTAL
        ).grid(row=8, column=1, sticky=(tk.W, tk.E))
        ttk.Label(frame, textvariable=self.main_threshold, width=6).grid(row=8, column=2)

        ttk.Label(frame, text="T阶图标阈值:").grid(row=9, column=0, sticky=tk.W, pady=5)
        ttk.Scale(
            frame, from_=0.80, to=0.98, 
            variable=self.tier_threshold, orient=tk.HORIZONTAL
        ).grid(row=9, column=1, sticky=(tk.W, tk.E))
        ttk.Label(frame, textvariable=self.tier_threshold, width=6).grid(row=9, column=2)

        # 最大尝试
        ttk.Label(frame, text="最大尝试:").grid(row=10, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.max_attempts, width=10).grid(row=10, column=1, sticky=tk.W)

        # 延迟设置
        ttk.Label(frame, text="⏱️ 延迟 (秒):", foreground="blue").grid(row=11, column=0, sticky=tk.W, pady=(10, 5))
        delay_items = [
            ("洗练石后:", "orb_delay"),
            ("装备点击后:", "equip_click_delay"),
            ("Alt截图延迟:", "alt_screenshot_delay"),
            ("循环间隔上限:", "loop_random_max"),
        ]
        row = 12
        for label, key in delay_items:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Entry(frame, textvariable=self.delay_vars[key], width=8).grid(row=row, column=1, sticky=tk.W)
            row += 1

        # 开始按钮
        self.start_btn = ttk.Button(
            frame,
            text="🚀 开始极速洗练（主词条+T阶图标匹配）",
            command=self._start_reforge
        )
        self.start_btn.grid(row=row, column=0, columnspan=3, pady=10, ipadx=15, ipady=6)

        # 日志区域
        row += 1
        log_frame = ttk.LabelFrame(frame, text="📋 洗练日志", padding=5)
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        return frame

    def log(self, msg: str):
        """添加日志"""
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

    def _pick_coordinate(self, target_type: str):
        """拾取坐标"""
        if target_type == "mod":
            region = self._region_selector.select_by_drag()
            self.mod_region.set(f"({region[0]}, {region[1]}, {region[2]}, {region[3]})")
            return
            
        x, y = self._coord_picker.pick(f"将鼠标移到{target_type}上，单击左键。")
        var = self.orb_pos if target_type == "orb" else self.equip_pos
        var.set(f"({x}, {y})")

    def _add_main_template(self):
        """添加主词条模板"""
        files = filedialog.askopenfilenames(filetypes=[("PNG", "*.png")])
        for f in files:
            if f not in self.main_template_paths:
                self.main_template_paths.append(f)
                self.listbox_main.insert(tk.END, f)

    def _remove_main_template(self):
        """移除主词条模板"""
        sel = self.listbox_main.curselection()
        if sel:
            del self.main_template_paths[sel[0]]
            self.listbox_main.delete(sel[0])

    def _select_tier_template(self):
        """选择T阶模板"""
        file = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if file:
            self.tier_template_path = file
            self.tier_entry.config(state='normal')
            self.tier_entry.delete(0, tk.END)
            self.tier_entry.insert(0, file)
            self.tier_entry.config(state='readonly')

    def _parse_tuple(self, s: str) -> tuple:
        """解析坐标字符串"""
        parts = [int(x.strip()) for x in s.strip("() ").split(",") if x.strip()]
        return tuple(parts)

    def _start_reforge(self):
        """开始洗练"""
        if not self.main_template_paths:
            messagebox.showwarning("错误", "请添加主词条模板！", parent=self.root)
            return
        if not self.tier_template_path:
            messagebox.showwarning("错误", "请选择T阶图标模板！", parent=self.root)
            return

        try:
            orb_pos = self._parse_tuple(self.orb_pos.get())
            equip_pos = self._parse_tuple(self.equip_pos.get())
            mod_region = self._parse_tuple(self.mod_region.get())
            
            if len(orb_pos) != 2 or len(equip_pos) != 2 or len(mod_region) != 4:
                raise ValueError("坐标格式错误")

            config = {
                "REFORGE_ORB_POS": orb_pos,
                "TARGET_EQUIP_POS": equip_pos,
                "MOD_DISPLAY_REGION": mod_region,
                "MAIN_THRESHOLD": self.main_threshold.get(),
                "TIER_THRESHOLD": self.tier_threshold.get(),
                "MAX_ATTEMPTS": self.max_attempts.get(),
                "ORB_DELAY": self.delay_vars["orb_delay"].get(),
                "EQUIP_CLICK_DELAY": self.delay_vars["equip_click_delay"].get(),
                "ALT_SCREENSHOT_DELAY": self.delay_vars["alt_screenshot_delay"].get(),
                "LOOP_RANDOM_MAX": self.delay_vars["loop_random_max"].get(),
                "MAIN_TEMPLATE_PATHS": self.main_template_paths.copy(),
                "TIER_TEMPLATE_PATH": self.tier_template_path,
            }

            self.save_config()
            self.root.withdraw()
            self._run_reforge(config)
            self.root.deiconify()

        except Exception as e:
            messagebox.showerror("启动失败", str(e), parent=self.root)

    def _run_reforge(self, config: dict):
        """执行洗练"""
        print("\n" + "=" * 70)
        print("⚡ 极速洗练启动（主词条 + 右侧T阶图标匹配）")
        print("🛑 按 F12 可随时中断洗练（返回主界面）")
        print("=" * 70)
        time.sleep(0.5)

        # 加载模板
        main_templates = [
            (path, load_and_preprocess_template(path))
            for path in config["MAIN_TEMPLATE_PATHS"]
        ]
        tier_template = load_and_preprocess_template(config["TIER_TEMPLATE_PATH"])
        h_tier, w_tier = tier_template.shape

        orb_x, orb_y = config["REFORGE_ORB_POS"]
        equip_x, equip_y = config["TARGET_EQUIP_POS"]
        x, y, w, h = config["MOD_DISPLAY_REGION"]
        main_thresh = config["MAIN_THRESHOLD"]
        tier_thresh = config["TIER_THRESHOLD"]
        max_attempts = config["MAX_ATTEMPTS"]
        equip_click_delay = config["EQUIP_CLICK_DELAY"]
        orb_delay = config["ORB_DELAY"]

        pyautogui.moveTo(orb_x, orb_y, duration=0.03)
        pyautogui.rightClick()
        time.sleep(orb_delay)
        pyautogui.keyDown('shift')

        success = False
        attempt = 0

        try:
            while attempt < max_attempts:
                if keyboard and keyboard.is_pressed('f12'):
                    print("\n⏸️ 用户按下 F12，洗练已中断。")
                    break

                attempt += 1
                pyautogui.moveTo(equip_x, equip_y, duration=0.03)
                pyautogui.click()
                time.sleep(equip_click_delay)

                pyautogui.keyDown('alt')
                raw_screenshot = pyautogui.screenshot(region=(x, y, w, h))
                pyautogui.keyUp('alt')

                raw_img_bgr = cv2.cvtColor(np.array(raw_screenshot), cv2.COLOR_RGB2BGR)
                screen_gray = preprocess_image(raw_img_bgr)

                # 主词条匹配
                main_matched, matched_main_tpl, matched_main_path, match_loc, score = match_main_template(
                    screen_gray, main_templates, main_thresh, attempt
                )

                if not main_matched:
                    continue

                # T阶图标匹配
                h_scr, w_scr = screen_gray.shape
                h_main, w_main = matched_main_tpl.shape
                x_main, y_main = match_loc

                search_x_start = x_main + w_main
                search_x_end = w_scr
                search_y_start = y_main
                search_y_end = y_main + h_main

                tier_matched = False
                if search_x_start < search_x_end and search_y_end <= h_scr:
                    if h_tier <= (search_y_end - search_y_start) and w_tier <= (search_x_end - search_x_start):
                        search_region = screen_gray[search_y_start:search_y_end, search_x_start:search_x_end]
                        res_tier = cv2.matchTemplate(search_region, tier_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val_tier, _, _ = cv2.minMaxLoc(res_tier)
                        print(f" 🔍 T阶图标匹配得分: {max_val_tier:.4f} | 阈值: {tier_thresh:.2f}")
                        tier_matched = max_val_tier >= tier_thresh

                if tier_matched:
                    print(" ✅ 主词条 + T阶图标均匹配成功！洗练成功！")
                    success = True
                    break
                else:
                    print(" ⚠️ T阶图标未匹配，跳过本次结果")

                time.sleep(0.01)

        finally:
            pyautogui.keyUp('shift')

        result = "成功" if success else "已中断" if (keyboard and keyboard.is_pressed('f12')) else "已达上限"
        msg = f"{result}！共 {attempt} 次。"
        print(f"\n🏁 {msg}")
        messagebox.showinfo("洗练结束", msg)

    def get_config(self) -> dict:
        """获取配置"""
        return {
            "orb_pos": self.orb_pos.get(),
            "equip_pos": self.equip_pos.get(),
            "mod_region": self.mod_region.get(),
            "main_threshold": self.main_threshold.get(),
            "tier_threshold": self.tier_threshold.get(),
            "max_attempts": self.max_attempts.get(),
            **{k: v.get() for k, v in self.delay_vars.items()},
            "main_template_paths": self.main_template_paths,
            "tier_template_path": self.tier_template_path,
        }

    def save_config(self):
        """保存配置"""
        config_manager.save_reforge_config(self.get_config())
