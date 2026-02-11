#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
poe2-tools - 程序入口

启动综合应用界面。
"""

import sys
from pathlib import Path

import tkinter as tk


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

def main():
    """主函数"""
    try:
        import ttkbootstrap as ttk
    except ImportError:
        import tkinter as ttk
        print("Standard tkinter used (ttkbootstrap not found)")

    from poe2_tools.app import CombinedApp

    if hasattr(ttk, "Window"):
        root = ttk.Window(themename="cosmo")
    else:
        root = ttk.Tk()

    app = CombinedApp(root)
    app.run()


if __name__ == "__main__":
    main()
