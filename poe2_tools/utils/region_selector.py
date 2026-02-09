"""
区域选择工具模块

提供屏幕区域选择和坐标拾取功能。
"""

import tkinter as tk
from tkinter import messagebox
import time
from typing import Tuple, Optional

try:
    from pynput import mouse
except ImportError:
    mouse = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


class RegionSelector:
    """屏幕区域选择器"""
    
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        """
        初始化区域选择器
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.selected_region: Optional[Tuple[int, int, int, int]] = None
    
    def select(self, title: str = "选择区域") -> Optional[Tuple[int, int, int, int]]:
        """
        选择屏幕区域
        
        Args:
            title: 选择窗口标题
            
        Returns:
            选中区域 (x, y, width, height)，取消时返回 None
        """
        if ImageGrab is None:
            raise ImportError("需要安装 pillow: pip install pillow")
            
        try:
            screen_img = ImageGrab.grab()
            w, h = screen_img.size

            selector = tk.Toplevel(self.parent)
            selector.title(title)
            selector.geometry(f"{w}x{h}+0+0")
            selector.overrideredirect(True)
            selector.attributes("-alpha", 0.3)
            selector.attributes("-topmost", True)

            canvas = tk.Canvas(selector, width=w, height=h, cursor="cross")
            canvas.pack()

            start_x = start_y = end_x = end_y = 0
            rect_id = None

            def on_press(event):
                nonlocal start_x, start_y
                start_x, start_y = event.x, event.y

            def on_drag(event):
                nonlocal rect_id, end_x, end_y
                end_x, end_y = event.x, event.y
                if rect_id:
                    canvas.delete(rect_id)
                rect_id = canvas.create_rectangle(
                    start_x, start_y, end_x, end_y, 
                    outline="red", width=2
                )

            def on_release(event):
                x1, y1 = min(start_x, end_x), min(start_y, end_y)
                x2, y2 = max(start_x, end_x), max(start_y, end_y)
                selector.destroy()
                if x2 - x1 > 5 and y2 - y1 > 10:
                    self.selected_region = (x1, y1, x2 - x1, y2 - y1)
                else:
                    self.selected_region = None

            canvas.bind("<ButtonPress-1>", on_press)
            canvas.bind("<B1-Motion>", on_drag)
            canvas.bind("<ButtonRelease-1>", on_release)
            selector.wait_window()

            return self.selected_region
            
        except Exception as e:
            print(f"选区失败: {e}")
            return None
    
    def select_by_drag(self, min_size: int = 10) -> Tuple[int, int, int, int]:
        """
        通过拖拽选择区域（全屏半透明遮罩）
        
        Args:
            min_size: 最小选区尺寸
            
        Returns:
            选中区域 (x, y, width, height)
            
        Raises:
            RuntimeError: 用户取消选择
        """
        selector = tk.Toplevel(self.parent)
        selector.attributes('-fullscreen', True, '-topmost', True, '-alpha', 0.3)
        selector.overrideredirect(True)
        
        canvas = tk.Canvas(selector, bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        start_x = start_y = rect_id = None
        selected_region = None
        done = False

        def on_mouse_down(e):
            nonlocal start_x, start_y
            start_x, start_y = e.x, e.y

        def on_mouse_move(e):
            nonlocal rect_id
            if start_x is None:
                return
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(
                start_x, start_y, e.x, e.y,
                outline='cyan', width=2, dash=(5, 5)
            )

        def on_mouse_up(e):
            nonlocal selected_region, done
            if start_x is None:
                selector.destroy()
                return
            x = min(start_x, e.x)
            y = min(start_y, e.y)
            w, h = abs(e.x - start_x), abs(e.y - start_y)
            if w < min_size or h < min_size:
                messagebox.showwarning(
                    "区域太小", 
                    f"请选择至少 {min_size}×{min_size} 像素！",
                    parent=selector
                )
                return
            selected_region = (x, y, w, h)
            done = True
            selector.destroy()

        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        
        messagebox.showinfo("区域选择", "拖动选择区域（青色虚线框）", parent=self.parent)
        
        while not done and selector.winfo_exists():
            self.parent.update()
            time.sleep(0.02)
            
        if selected_region is None:
            raise RuntimeError("用户取消选择")
            
        return selected_region


class CoordinatePicker:
    """坐标拾取器"""
    
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        """
        初始化坐标拾取器
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
    
    def pick(self, prompt: str = "将鼠标移到目标位置，单击左键") -> Tuple[int, int]:
        """
        拾取屏幕坐标
        
        Args:
            prompt: 提示信息
            
        Returns:
            坐标 (x, y)
        """
        if pyautogui is None:
            raise ImportError("需要安装 pyautogui: pip install pyautogui")
            
        messagebox.showinfo("拾取坐标", prompt, parent=self.parent)
        
        if mouse is not None:
            clicked = False
            
            def on_click(x, y, button, pressed):
                nonlocal clicked
                if pressed and button.name == 'left':
                    clicked = True
                    return False
                    
            try:
                with mouse.Listener(on_click=on_click):
                    while not clicked:
                        time.sleep(0.01)
            except Exception:
                time.sleep(1.5)
        else:
            # 无 pynput 时的后备方案
            time.sleep(1.5)
            
        return pyautogui.position()
