#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
poe2-tools - 程序入口

启动综合应用界面。
"""

import tkinter as tk
from poe2_tools.app import CombinedApp


def main():
    """主函数"""
    root = tk.Tk()
    app = CombinedApp(root)
    app.run()


if __name__ == "__main__":
    main()
