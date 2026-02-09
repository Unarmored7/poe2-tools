"""
模板匹配测试工具

用于测试主词条和T阶图标的匹配效果。
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import cv2
import numpy as np
from PIL import Image, ImageTk
import os

from poe2_tools.utils.image_processing import preprocess_image


class TemplateMatcher:
    """模板匹配测试工具"""
    
    def __init__(self, root: tk.Tk | tk.Toplevel):
        """
        初始化模板匹配器
        
        Args:
            root: 父窗口
        """
        self.root = root
        self._init_vars()
        
    def _init_vars(self):
        """初始化变量"""
        self.screenshot_path = None
        self.template_main_path = None
        self.template_tier_path = None
        self.screenshot_img = None
        self.template_main_img = None
        self.template_tier_img = None
        
        self.main_thresh = tk.DoubleVar(value=0.85)
        self.tier_thresh = tk.DoubleVar(value=0.90)
        
    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """创建 UI 界面"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 控制区
        control_frame = ttk.Frame(frame, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # 按钮行
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(button_frame, text="选择截图", command=self._load_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="选择主词条模板", command=self._load_template_main).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="选择T阶图标模板", command=self._load_template_tier).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔍 开始匹配", command=self._run_matching).pack(side=tk.RIGHT, padx=5)

        # 阈值设置
        thresh_frame = ttk.Frame(control_frame)
        thresh_frame.pack(fill=tk.X)

        main_thresh_frame = ttk.Frame(thresh_frame)
        main_thresh_frame.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(main_thresh_frame, text="主词条阈值:").pack(side=tk.LEFT)
        ttk.Scale(
            main_thresh_frame, from_=0.7, to=0.98, 
            variable=self.main_thresh, orient=tk.HORIZONTAL, length=120
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(main_thresh_frame, textvariable=self.main_thresh, width=5).pack(side=tk.LEFT)

        tier_thresh_frame = ttk.Frame(thresh_frame)
        tier_thresh_frame.pack(side=tk.LEFT)
        ttk.Label(tier_thresh_frame, text="T阶图标阈值:").pack(side=tk.LEFT)
        ttk.Scale(
            tier_thresh_frame, from_=0.8, to=0.99, 
            variable=self.tier_thresh, orient=tk.HORIZONTAL, length=120
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(tier_thresh_frame, textvariable=self.tier_thresh, width=5).pack(side=tk.LEFT)

        # 三视图区
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 日志区
        log_frame = ttk.LabelFrame(frame, text="📋 匹配日志", padding=5)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        self.result_text = scrolledtext.ScrolledText(
            log_frame, height=6, state='disabled', bg='#f0f0f0', wrap=tk.WORD
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 原始图像区
        frame1 = ttk.LabelFrame(paned, text="1. 原始图像")
        paned.add(frame1, weight=1)
        self.canvas_orig_screen = tk.Canvas(frame1, bg='white')
        self.canvas_orig_screen.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas_orig_main = tk.Canvas(frame1, bg='lightgray', height=60)
        self.canvas_orig_main.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))
        self.canvas_orig_tier = tk.Canvas(frame1, bg='lightblue', height=40)
        self.canvas_orig_tier.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))

        # 预处理图像区
        frame2 = ttk.LabelFrame(paned, text="2. 预处理图像（二值化）")
        paned.add(frame2, weight=1)
        self.canvas_proc_screen = tk.Canvas(frame2, bg='white')
        self.canvas_proc_screen.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas_proc_main = tk.Canvas(frame2, bg='lightgray', height=60)
        self.canvas_proc_main.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))
        self.canvas_proc_tier = tk.Canvas(frame2, bg='lightblue', height=40)
        self.canvas_proc_tier.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))

        # 匹配结果区
        frame3 = ttk.LabelFrame(paned, text="3. 匹配结果（绿框=主词条，蓝框=T阶图标）")
        paned.add(frame3, weight=1)
        self.canvas_result = tk.Canvas(frame3, bg='white')
        self.canvas_result.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        return frame

    def log(self, msg: str):
        """添加日志"""
        self.result_text.config(state='normal')
        self.result_text.insert(tk.END, msg + "\n")
        self.result_text.see(tk.END)
        self.result_text.config(state='disabled')

    def _load_screenshot(self):
        """加载截图"""
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.bmp")])
        if path:
            self.screenshot_path = path
            self.screenshot_img = cv2.imread(path, cv2.IMREAD_COLOR)
            self._update_original_views()
            self.log(f"✅ 已加载截图: {os.path.basename(path)}")

    def _load_template_main(self):
        """加载主词条模板"""
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if path:
            self.template_main_path = path
            self.template_main_img = cv2.imread(path, cv2.IMREAD_COLOR)
            self._update_original_views()
            self.log(f"✅ 已加载主词条模板: {os.path.basename(path)}")

    def _load_template_tier(self):
        """加载T阶模板"""
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if path:
            self.template_tier_path = path
            self.template_tier_img = cv2.imread(path, cv2.IMREAD_COLOR)
            self._update_original_views()
            self.log(f"✅ 已加载T阶模板: {os.path.basename(path)}")

    def _update_original_views(self):
        """更新原始图像显示"""
        if self.screenshot_img is not None:
            self._show_image(self.screenshot_img, self.canvas_orig_screen)
            proc = preprocess_image(self.screenshot_img)
            self._show_image(proc, self.canvas_proc_screen, is_gray=True)
            
        if self.template_main_img is not None:
            self._show_image(self.template_main_img, self.canvas_orig_main, max_h=50)
            proc = preprocess_image(self.template_main_img)
            self._show_image(proc, self.canvas_proc_main, max_h=50, is_gray=True)
            
        if self.template_tier_img is not None:
            self._show_image(self.template_tier_img, self.canvas_orig_tier, max_h=35)
            proc = preprocess_image(self.template_tier_img)
            self._show_image(proc, self.canvas_proc_tier, max_h=35, is_gray=True)

    def _show_image(self, img: np.ndarray, canvas: tk.Canvas, 
                    max_h: int | None = None, is_gray: bool = False):
        """在 Canvas 上显示图像"""
        if is_gray:
            pil_img = Image.fromarray(img)
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            
        w, h = pil_img.size
        canvas.update_idletasks()
        cw = canvas.winfo_width()
        ch = canvas.winfo_height() if max_h is None else max_h
        
        if cw > 1 and ch > 1:
            scale = min(cw / w, ch / h, 1.0)
            new_w, new_h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
        tk_img = ImageTk.PhotoImage(pil_img)
        canvas.delete("all")
        canvas.create_image(cw // 2, ch // 2, anchor=tk.CENTER, image=tk_img)
        canvas._photo = tk_img

    def _run_matching(self):
        """运行匹配"""
        if self.screenshot_img is None:
            self.log("❌ 请先加载截图")
            return
        if self.template_main_img is None:
            self.log("❌ 请先加载主词条模板")
            return

        screen_gray = preprocess_image(self.screenshot_img)
        main_gray = preprocess_image(self.template_main_img)
        
        main_thresh = self.main_thresh.get()
        tier_thresh = self.tier_thresh.get()

        self.log(f"\n🔍 开始匹配... 主词条阈值={main_thresh:.2f}, T阶阈值={tier_thresh:.2f}")

        # 主词条匹配
        h_main, w_main = main_gray.shape
        h_scr, w_scr = screen_gray.shape

        if h_main > h_scr or w_main > w_scr:
            self.log("❌ 主词条模板尺寸大于截图")
            return

        res_main = cv2.matchTemplate(screen_gray, main_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val_main, _, max_loc_main = cv2.minMaxLoc(res_main)

        self.log(f"📊 主词条匹配得分: {max_val_main:.4f}")

        result_img = self.screenshot_img.copy()
        main_matched = max_val_main >= main_thresh

        if main_matched:
            x, y = max_loc_main
            cv2.rectangle(result_img, (x, y), (x + w_main, y + h_main), (0, 255, 0), 2)
            self.log(f"✅ 主词条匹配成功！位置=({x}, {y})")

            # T阶匹配
            if self.template_tier_img is not None:
                tier_gray = preprocess_image(self.template_tier_img)
                h_tier, w_tier = tier_gray.shape

                search_x_start = x + w_main
                search_x_end = w_scr
                search_y_start = y
                search_y_end = y + h_main

                if search_x_start < search_x_end and search_y_end <= h_scr:
                    if h_tier <= (search_y_end - search_y_start) and w_tier <= (search_x_end - search_x_start):
                        search_region = screen_gray[search_y_start:search_y_end, search_x_start:search_x_end]
                        res_tier = cv2.matchTemplate(search_region, tier_gray, cv2.TM_CCOEFF_NORMED)
                        _, max_val_tier, _, max_loc_tier = cv2.minMaxLoc(res_tier)

                        self.log(f"📊 T阶匹配得分: {max_val_tier:.4f}")

                        if max_val_tier >= tier_thresh:
                            tx = search_x_start + max_loc_tier[0]
                            ty = search_y_start + max_loc_tier[1]
                            cv2.rectangle(result_img, (tx, ty), (tx + w_tier, ty + h_tier), (255, 0, 0), 2)
                            self.log(f"✅ T阶匹配成功！位置=({tx}, {ty})")
                        else:
                            self.log("❌ T阶匹配失败")
                    else:
                        self.log("⚠️ T阶模板大于搜索区域")
                else:
                    self.log("⚠️ 无有效右侧搜索区域")
        else:
            self.log("❌ 主词条匹配失败")

        self._show_image(result_img, self.canvas_result)
