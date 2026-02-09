"""
POE2 辅助工具 - 主应用

整合自动喝药、装备洗练、模板匹配等功能。
"""

import tkinter as tk
from tkinter import ttk

from poe2_tools.auto_potion import AutoPotionMonitor
from poe2_tools.reforge import ReforgeManager
from poe2_tools.template_matcher import TemplateMatcher


class CombinedApp:
    """综合应用主类"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化综合应用
        
        Args:
            root: Tkinter 根窗口
        """
        self.root = root
        self.root.title("poe2-tools")
        self.root.geometry("900x700")
        
        # 添加窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 初始化各模块
        self._init_modules()
        
        # 创建 UI
        self._create_tabs()
        
    def _init_modules(self):
        """初始化各功能模块"""
        self.potion_monitor = AutoPotionMonitor(self.root)
        self.reforge_manager = ReforgeManager(self.root)
        self.template_matcher = TemplateMatcher(self.root)
        
    def _create_tabs(self):
        """创建选项卡"""
        # 自动喝药 Tab
        potion_tab = ttk.Frame(self.notebook)
        self.notebook.add(potion_tab, text="自动喝药")
        self.potion_monitor.create_ui(potion_tab)
        
        # 装备洗练 Tab
        equip_tab = ttk.Frame(self.notebook)
        self.notebook.add(equip_tab, text="装备洗练")
        
        # 装备洗练二级选项卡
        equip_notebook = ttk.Notebook(equip_tab)
        equip_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 极速洗练
        reforge_tab = ttk.Frame(equip_notebook)
        equip_notebook.add(reforge_tab, text="极速洗练")
        self.reforge_manager.create_ui(reforge_tab)
        
        # 匹配测试
        matcher_tab = ttk.Frame(equip_notebook)
        equip_notebook.add(matcher_tab, text="匹配测试")
        self.template_matcher.create_ui(matcher_tab)
        
    def _on_closing(self):
        """窗口关闭时保存配置"""
        try:
            self.potion_monitor.save_config()
            self.reforge_manager.save_config()
        except Exception as e:
            print(f"⚠️ 保存配置失败: {e}")
        finally:
            self.root.destroy()
            
    def run(self):
        """运行应用"""
        self.root.mainloop()
