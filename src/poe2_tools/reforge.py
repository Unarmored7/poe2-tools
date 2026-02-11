"""
混沌石洗炼模块

通过 Alt+Ctrl+C 读取完整词条文本 + 正则范围匹配实现自动洗炼。
"""

import tkinter as tk
from tkinter import TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y, HORIZONTAL, VERTICAL, CENTER, END, W, E, N, S, NW, SW, NE, SE, WORD, CHAR, DISABLED, NORMAL
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import time
import threading
import pyautogui
import pyperclip

try:
    import keyboard
except ImportError:
    keyboard = None
    print("⚠️ keyboard 模块未安装，F12 中断功能不可用")

from poe2_tools.utils.region_selector import CoordinatePicker
from poe2_tools.utils.config_manager import config_manager
from poe2_tools.utils.ui_logger import UiLogger
from poe2_tools.utils.text_matcher import TextMatcher
from poe2_tools.utils.divine_matcher import DivineMatcher


SECTION_HEADER_HEIGHT = 28
CONFIG_COORD_ROW_HEIGHT = 36
CONFIG_CONTROLS_ROW_HEIGHT = 44
CONFIG_TOP_HEIGHT = (
    SECTION_HEADER_HEIGHT
    + 5
    + CONFIG_COORD_ROW_HEIGHT
    + 10
    + CONFIG_CONTROLS_ROW_HEIGHT
)


class AffixBlockInput:
    """Tag/chip-like editor for affix blocks.

    - Enter: commit current input as one block.
    - Shift+Enter: newline inside current block.
    - Select list item: load block into editor for quick editing.
    """

    def __init__(self, parent, *, theme_manager, section_style: str = "Content.TFrame"):
        self.blocks: list[str] = []
        self._selected_index: int | None = None

        self.frame = ttk.Frame(parent, style=section_style, height=SECTION_HEADER_HEIGHT)
        self.frame.pack(fill=X, pady=(0, 5))
        self.frame.pack_propagate(False)
        ttk.Label(self.frame, text="添加词条", style="Card.TLabel").pack(side=LEFT, padx=5)

        editor_wrap = ttk.Frame(parent, style=section_style)
        editor_wrap.pack(fill=X, padx=5, pady=(0, 6))
        self.editor = tk.Text(
            editor_wrap,
            height=3,
            wrap=WORD,
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat",
            bg=theme_manager.COLOR_BG_INPUT,
            fg=theme_manager.COLOR_TEXT_MAIN,
            insertbackground=theme_manager.COLOR_TEXT_MAIN,
            borderwidth=0,
            highlightthickness=0,
            highlightbackground=theme_manager.COLOR_BG_INPUT,
            highlightcolor=theme_manager.COLOR_PRIMARY,
        )
        self.editor.pack(fill=X)
        self.editor.bind("<Return>", self._on_return)
        self.editor.bind("<Button-1>", self._on_editor_click)

        self.final_frame = ttk.Frame(parent, style=section_style, height=SECTION_HEADER_HEIGHT)
        self.final_frame.pack(fill=X, pady=(0, 5))
        self.final_frame.pack_propagate(False)
        ttk.Label(self.final_frame, text="最终词条", style="Card.TLabel").pack(side=LEFT, padx=5)

        chips_wrap = ttk.Frame(parent, style=section_style)
        chips_wrap.pack(fill=BOTH, expand=False, padx=5)
        self.listbox = tk.Listbox(
            chips_wrap,
            height=5,
            activestyle="none",
            selectmode=tk.SINGLE,
            exportselection=False,
            font=("Microsoft YaHei", 10, "bold"),
            bg=theme_manager.COLOR_BG_INPUT,
            fg=theme_manager.COLOR_TEXT_MAIN,
            selectbackground=theme_manager.COLOR_PRIMARY,
            selectforeground=theme_manager.COLOR_TEXT_MAIN,
            borderwidth=0,
            highlightthickness=0,
        )
        self.listbox.pack(fill=X)
        self.listbox.bind("<Button-1>", self._on_listbox_click)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        actions = ttk.Frame(parent, style=section_style)
        actions.pack(fill=X, padx=5, pady=(6, 0))
        self.add_btn = ttk.Button(actions, text="添加词条", command=self.add_from_editor, style="outline", width=8)
        self.add_btn.pack(side=LEFT)
        self.delete_btn = ttk.Button(actions, text="删除选中", command=self.remove_selected, style="outline", width=8)
        self.delete_btn.pack(side=LEFT, padx=6)

        self.editor.bind_all("<Button-1>", self._on_any_click, add="+")

    def _on_return(self, event):
        if event.state & 0x0001:  # Shift pressed
            return
        self.add_from_editor()
        return "break"

    def _preview(self, text: str) -> str:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return "(空)"
        one_line = " | ".join(lines)
        return one_line if len(one_line) <= 90 else f"{one_line[:87]}..."

    def _render(self):
        self.listbox.delete(0, END)
        for i, block in enumerate(self.blocks, start=1):
            line_count = len([ln for ln in block.splitlines() if ln.strip()])
            prefix = f"#{i} [{line_count}行] "
            self.listbox.insert(END, prefix + self._preview(block))
            idx = i - 1
            self.listbox.itemconfig(idx, bg="#f2ead0" if i % 2 else "#e9e0c4")
        if self._selected_index is not None and 0 <= self._selected_index < len(self.blocks):
            self.listbox.selection_set(self._selected_index)

    def _current_editor_text(self) -> str:
        return self.editor.get("1.0", "end").strip()

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            self._selected_index = None
            return
        self._selected_index = int(sel[0])
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self.blocks[self._selected_index])

    def _clear_selection_and_editor(self):
        self._selected_index = None
        self.listbox.selection_clear(0, END)
        self.editor.delete("1.0", "end")

    def _on_editor_click(self, _event=None):
        if self._selected_index is not None:
            self._clear_selection_and_editor()

    def _on_listbox_click(self, event):
        if not self.blocks:
            self._clear_selection_and_editor()
            return "break"

        idx = self.listbox.nearest(event.y)
        if idx < 0 or idx >= len(self.blocks):
            self._clear_selection_and_editor()
            return "break"

        bbox = self.listbox.bbox(idx)
        if not bbox:
            self._clear_selection_and_editor()
            return "break"

        x, y, w, h = bbox
        if not (x <= event.x <= x + w and y <= event.y <= y + h):
            self._clear_selection_and_editor()
            return "break"

    def _is_click_on_list_item(self, event) -> bool:
        if event.widget is not self.listbox:
            return False
        if not self.blocks:
            return False
        idx = self.listbox.nearest(event.y)
        if idx < 0 or idx >= len(self.blocks):
            return False
        bbox = self.listbox.bbox(idx)
        if not bbox:
            return False
        x, y, w, h = bbox
        return x <= event.x <= x + w and y <= event.y <= y + h

    def _on_any_click(self, event):
        if event.widget in (self.add_btn, self.delete_btn):
            return
        if self._is_click_on_list_item(event):
            return
        if self._selected_index is not None or self._current_editor_text():
            self._clear_selection_and_editor()

    def add_from_editor(self):
        text = self._current_editor_text()
        if not text:
            return False
        self.blocks.append(text)
        self._selected_index = len(self.blocks) - 1
        self.editor.delete("1.0", "end")
        self._render()
        return True

    def update_selected(self):
        if self._selected_index is None:
            return
        text = self._current_editor_text()
        if not text:
            return
        self.blocks[self._selected_index] = text
        self._render()

    def remove_selected(self):
        if self._selected_index is None:
            return
        del self.blocks[self._selected_index]
        self._clear_selection_and_editor()
        self._render()

    def clear(self):
        self.blocks = []
        self._clear_selection_and_editor()
        self._render()

    def set_blocks(self, blocks: list[str]):
        self.blocks = [b.strip() for b in blocks if b and b.strip()]
        self._clear_selection_and_editor()
        self._render()

    def get_blocks(self) -> list[str]:
        return list(self.blocks)

    def get_legacy_text(self) -> str:
        return "\n".join(self.blocks)


class ReforgeManager:
    """混沌石洗炼管理器"""
    
    def __init__(self, root: tk.Tk | tk.Toplevel):
        """
        初始化混沌石洗炼管理器
        
        Args:
            root: 父窗口
        """
        self.root = root
        self._init_vars()
        
    def _init_vars(self):
        """初始化变量"""
        config = config_manager.load_reforge_config()
        
        # 文本匹配
        self._text_matcher = TextMatcher()
        self.mod_requirements_text = config.get("mod_requirements_text", "")
        self.mod_requirement_blocks = config.get("mod_requirement_blocks", [])
        if not isinstance(self.mod_requirement_blocks, list):
            self.mod_requirement_blocks = []
        if not self.mod_requirement_blocks and self.mod_requirements_text.strip():
            self.mod_requirement_blocks = [self.mod_requirements_text.strip()]
        legacy_logic = config.get("match_logic")
        default_k = 1
        if legacy_logic == "all":
            default_k = 99
        self.min_match_count = tk.IntVar(value=int(config.get("min_match_count", default_k)))
        
        # 坐标
        self.orb_pos = tk.StringVar(value=config.get("orb_pos", "(?, ?)"))
        self.equip_pos = tk.StringVar(value=config.get("equip_pos", "(?, ?)"))
        
        # 参数
        self.equip_click_delay_ms = tk.IntVar(value=int(config.get("equip_click_delay_ms", 100)))
        
        self._coord_picker = CoordinatePicker(self.root)
        
        # 洗炼状态
        self._stop_event = threading.Event()
        self._is_running = False
        self._global_listener_running = False
        self._hotkey_enabled = False

        # UI 引用占位
        self.mod_block_input = None
        self.log_text = None
        self.n_choose_k_label = None
        
    def _start_global_listener(self):
        """启动全局F12监听线程（开始/停止）"""
        if self._global_listener_running:
            return
            
        def listener():
            self._global_listener_running = True
            while self._global_listener_running:
                if not self._hotkey_enabled:
                    time.sleep(0.05)
                    continue
                if keyboard and keyboard.is_pressed('f12'):
                    if self._is_running:
                        self._stop_event.set()
                        self.root.after(80, self.root.deiconify)
                        self.root.after(120, self.root.lift)
                        self.root.after(0, lambda: self.log("F12 按下，正在停止", "warning"))
                    else:
                        self.root.after(0, self.root.iconify)
                        self.root.after(0, lambda: self.log("F12 按下，准备启动混沌石洗炼", "info"))
                        self.root.after(10, self._start_reforge)
                    time.sleep(0.5)
                time.sleep(0.05)
        
        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
        self.log("F12 热键已启用（开始/停止）", "success")
        
    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """创建 UI 界面 (Usagi Theme)"""
        from poe2_tools.theme import ThemeManager

        # parent is already the Card Frame (Pale Yellow)

        # 1. Configuration Area (Top) - unified top anchor
        config_top = ttk.Frame(parent, style="Content.TFrame", height=CONFIG_TOP_HEIGHT)
        config_top.pack(fill=X, pady=(0, 10))
        config_top.pack_propagate(False)

        header_global = ttk.Frame(config_top, style="Content.TFrame", height=SECTION_HEADER_HEIGHT)
        header_global.pack(fill=X, pady=(0, 5))
        header_global.pack_propagate(False)
        ttk.Label(header_global, text="全局设置", style="Card.TLabel").pack(side=LEFT, padx=5)

        config_frame = ttk.Frame(config_top, style="Content.TFrame", padding=(10, 0, 10, 0))
        config_frame.pack(fill=X)

        # Row 1: Coordinates
        row_coords = ttk.Frame(config_frame, style="Content.TFrame", height=CONFIG_COORD_ROW_HEIGHT)
        row_coords.pack(fill=X, pady=(0, 10))
        row_coords.pack_propagate(False)
        
        for label, var, key in [
            ("混沌石位置", self.orb_pos, "orb"), 
            ("装备位置", self.equip_pos, "equip"),
        ]:
            f = ttk.Frame(row_coords, style="Content.TFrame")
            f.pack(side=LEFT, padx=(0, 20))
            ttk.Label(f, text=label, style="Content.TLabel").pack(side=LEFT, padx=(0, 5))
            entry = ttk.Entry(
                f,
                textvariable=var,
                width=12,
                justify=CENTER,
                state='readonly',
                style="Numeric.TEntry",
                font=("Times New Roman", 10, "bold"),
            )
            entry.pack(side=LEFT, padx=(0, 5))
            entry.bind("<Button-1>", lambda _e, k=key: self._pick_coordinate(k))
            
        # Row 2: Parameters
        row_params = ttk.Frame(config_frame, style="Content.TFrame", height=CONFIG_CONTROLS_ROW_HEIGHT)
        row_params.pack(fill=X)
        row_params.pack_propagate(False)

        ttk.Label(row_params, text="点击延时（ms）：", style="Content.TLabel").pack(side=LEFT, pady=4)
        ttk.Entry(row_params, textvariable=self.equip_click_delay_ms, width=6, justify=CENTER, font=("Times New Roman", 10, "bold")).pack(side=LEFT, padx=5, pady=4)

        ttk.Label(row_params, text="命中条数：", style="Content.TLabel").pack(side=LEFT, padx=(20, 0), pady=4)
        ttk.Entry(row_params, textvariable=self.min_match_count, width=5, justify=CENTER, font=("Times New Roman", 10, "bold")).pack(side=LEFT, padx=5, pady=4)


        # 2. Main Content Area (Vertical Stack: Requirements -> Logs)
        
        # Section: Requirements Input (Fixed Height)
        frame_input = ttk.Frame(parent, style="Content.TFrame")
        frame_input.pack(fill=X, pady=(0, 10))

        self.mod_block_input = AffixBlockInput(
            frame_input,
            theme_manager=ThemeManager,
            section_style="Content.TFrame",
        )
        self.mod_block_input.set_blocks(self.mod_requirement_blocks)

        # Section: Logs (Expanded)
        frame_log = ttk.Frame(parent, style="Content.TFrame")
        frame_log.pack(fill=BOTH, expand=True, pady=(0, 10))

        lbl_log = ttk.Frame(frame_log, style="Content.TFrame", height=SECTION_HEADER_HEIGHT)
        lbl_log.pack(fill=X, pady=(0, 5))
        lbl_log.pack_propagate(False)
        ttk.Label(lbl_log, text="运行日志", style="Card.TLabel").pack(side=LEFT, padx=5)
        ttk.Button(lbl_log, text="清空", command=self._clear_logs, style="outline", width=6).pack(side=RIGHT, padx=5)

        log_body = ttk.Frame(frame_log, style="Content.TFrame")
        log_body.pack(fill=BOTH, expand=True)

        self.log_scroll = ttk.Scrollbar(log_body, orient=VERTICAL)
        self.log_scroll.pack(side=RIGHT, fill=Y)

        self.log_text = tk.Text(
            log_body, height=10, state=DISABLED, wrap=WORD,
            font=("Times New Roman", 10, "bold"), relief="flat",
            bg=ThemeManager.COLOR_BG_INPUT, fg=ThemeManager.COLOR_TEXT_MAIN,
            borderwidth=1,
            highlightthickness=0,
            yscrollcommand=self.log_scroll.set,
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.log_scroll.config(command=self.log_text.yview)
        self._logger = UiLogger(self.root, self.log_text, max_lines=800)


        # Global listener
        self._start_global_listener()

        return parent

    def log(self, msg: str, level: str = "info"):
        """添加日志"""
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

    def _pick_coordinate(self, target_type: str):
        """拾取坐标"""
        x, y = self._coord_picker.pick(f"将鼠标移到{target_type}上，单击左键。")
        var = self.orb_pos if target_type == "orb" else self.equip_pos
        var.set(f"({x}, {y})")

    def _parse_tuple(self, s: str) -> tuple:
        """解析坐标字符串"""
        parts = [int(x.strip()) for x in s.strip("() ").split(",") if x.strip()]
        return tuple(parts)

    def _effective_min_match_count(self, total_requirements: int) -> int:
        return max(1, min(self.min_match_count.get(), total_requirements))

    def _start_reforge(self):
        """开始混沌石洗炼"""
        if self._is_running:
            return

        try:
            orb_pos = self._parse_tuple(self.orb_pos.get())
            equip_pos = self._parse_tuple(self.equip_pos.get())
            if len(orb_pos) != 2 or len(equip_pos) != 2:
                raise ValueError("混沌石/装备坐标格式错误")

            requirement_blocks_text = self.mod_block_input.get_blocks() if self.mod_block_input else []
            if not requirement_blocks_text:
                self.log("请输入目标词条！", "warning")
                return

            requirement_blocks = []
            for idx, block_text in enumerate(requirement_blocks_text, start=1):
                reqs = self._text_matcher.parse_requirements(block_text)
                if not reqs:
                    self.log(f"第 {idx} 个词条块无法解析，请检查格式！", "warning")
                    return
                requirement_blocks.append(reqs)
            required_count = self._effective_min_match_count(len(requirement_blocks))

            config = {
                "REQUIREMENT_BLOCKS": requirement_blocks,
                "MIN_MATCH_COUNT": required_count,
                "REFORGE_ORB_POS": orb_pos,
                "TARGET_EQUIP_POS": equip_pos,
                "EQUIP_CLICK_DELAY_MS": self.equip_click_delay_ms.get(),
            }

            self.log(f"已解析 {len(requirement_blocks)} 个词条块", "info")
            for i, group in enumerate(requirement_blocks, start=1):
                self.log(f"  词条块 #{i}（{len(group)} 行）", "debug")
                for req in group:
                    self.log(
                        f"    → {req.original_text} ({req.mod_type}, 范围={list(zip(req.min_values, req.max_values)) if req.min_values else '文本'})",
                        "debug",
                    )

            self.save_config()

            thread = threading.Thread(target=self._run_reforge, args=(config,), daemon=True)
            thread.start()

        except Exception as e:
            self.log(f"启动失败：{e}", "error")

    def _run_reforge(self, config: dict):
        """执行混沌石洗炼流程"""
        self.log("混沌石洗炼流程启动", "success")
        self.log("按 F12 可随时中断", "info")
        time.sleep(0.5)
        started_at = time.time()

        requirement_blocks = config["REQUIREMENT_BLOCKS"]
        required_count = config.get("MIN_MATCH_COUNT", 1)
        orb_x, orb_y = config["REFORGE_ORB_POS"]
        equip_x, equip_y = config["TARGET_EQUIP_POS"]
        equip_click_delay_s = max(0.0, config.get("EQUIP_CLICK_DELAY_MS", 100) / 1000.0)

        # 拾取混沌石
        pyautogui.moveTo(orb_x, orb_y, duration=0.03)
        pyautogui.rightClick()
        time.sleep(0.3)
        pyautogui.keyDown('shift')

        success = False
        attempt = 0
        stop_reason = "未命中结束"
        last_result = None
        self._is_running = True
        self._stop_event.clear()
        self.log(f"开始混沌石洗炼（规则：{len(requirement_blocks)}组选{required_count}），按 F12 停止", "success")

        try:
            while True:
                if self._stop_event.is_set():
                    self.log("检测到 F12，混沌石洗炼已中断", "warning")
                    stop_reason = "F12 中断"
                    break

                attempt += 1

                # 点击装备
                pyautogui.moveTo(equip_x, equip_y, duration=0.03)
                pyautogui.click()
                time.sleep(equip_click_delay_s)

                # Alt+Ctrl+C 复制装备信息（统一使用完整词条信息）
                pyperclip.copy("")
                pyautogui.keyDown("alt")
                time.sleep(0.02)
                pyautogui.hotkey("ctrl", "c")
                time.sleep(0.01)
                pyautogui.keyUp("alt")

                # 等待剪贴板数据
                data = ""
                for _ in range(3):
                    if self._stop_event.is_set():
                        break
                    data = pyperclip.paste()
                    if data:
                        break
                    time.sleep(0.01)

                if not data:
                    if attempt % 20 == 0:
                        self.log(f"第 {attempt} 次：无法读取剪贴板", "warning")
                    time.sleep(0.05)
                    continue

                # 匹配检查 (N 选 K)
                result = self._text_matcher.check_grouped_match_at_least(
                    data,
                    requirement_blocks,
                    min_match_count=required_count,
                    log_fn=self.log,
                )
                last_result = result

                if result.matched:
                    self.log(
                        f"第 {attempt} 次混沌石洗炼命中（命中 {result.matched_count}/{len(requirement_blocks)} 组，目标 >= {result.required_count}）",
                        "success",
                    )
                    if result.matched_values:
                        self.log(f"匹配数值：{result.matched_values}", "success")
                    success = True
                    stop_reason = "命中目标"
                    break
                else:
                    if attempt % 10 == 0:
                        self.log(
                            f"第 {attempt} 次：未匹配（命中 {result.matched_count}/{len(requirement_blocks)} 组，目标 >= {result.required_count}）",
                            "debug",
                        )



        finally:
            pyautogui.keyUp("alt")
            pyautogui.keyUp('shift')
            self._is_running = False

        stopped = self._stop_event.is_set()
        result_text = "成功" if success else "已中断" if stopped else "结束"
        msg = f"{result_text}！共 {attempt} 次。"
        self.log(f"混沌石洗炼结束：{msg}", "success" if success else "warning")
        elapsed = max(0.0, time.time() - started_at)
        last_stat = "无"
        if last_result is not None:
            last_stat = f"{last_result.matched_count}/{len(requirement_blocks)}"
        self.log(
            f"结束汇总：原因={stop_reason}，耗时={elapsed:.1f}s，尝试={attempt} 次，最后命中组={last_stat}",
            "info",
        )

    def get_config(self) -> dict:
        """获取配置"""
        mod_text = ""
        try:
            blocks = self.mod_block_input.get_blocks() if self.mod_block_input else self.mod_requirement_blocks
            mod_text = "\n".join(blocks)
        except Exception:
            mod_text = self.mod_requirements_text
            blocks = self.mod_requirement_blocks

        return {
            "min_match_count": self.min_match_count.get(),
            "mod_requirements_text": mod_text,
            "mod_requirement_blocks": blocks,
            "orb_pos": self.orb_pos.get(),
            "equip_pos": self.equip_pos.get(),
            "equip_click_delay_ms": self.equip_click_delay_ms.get(),
        }

    def save_config(self):
        """保存配置"""
        config_manager.save_reforge_config(self.get_config())

    def set_hotkey_enabled(self, enabled: bool):
        self._hotkey_enabled = bool(enabled)

    def toggle_running(self):
        if self._is_running:
            self._stop_event.set()
        else:
            self._start_reforge()

    def is_running(self) -> bool:
        return self._is_running


class DivineReforgeManager:
    """神圣石洗炼管理器。"""

    def __init__(self, root: tk.Tk | tk.Toplevel):
        self.root = root
        self._init_vars()

    def _init_vars(self):
        config = config_manager.load_divine_reforge_config()
        self.orb_pos = tk.StringVar(value=config.get("orb_pos", "(?, ?)"))
        self.equip_pos = tk.StringVar(value=config.get("equip_pos", "(?, ?)"))
        self.fractured_threshold_percent = tk.IntVar(value=max(1, int(float(config.get("fractured_threshold_percent", 95)))))
        mode = config.get("target_mode", "all_stats")
        if mode == "all_fractured":
            mode = "all_stats"
        self.target_mode = tk.StringVar(value=mode)
        self.selected_requirements_text = config.get("selected_requirements_text", "")
        self.selected_requirement_blocks = config.get("selected_requirement_blocks", [])
        if not isinstance(self.selected_requirement_blocks, list):
            self.selected_requirement_blocks = []
        if not self.selected_requirement_blocks and self.selected_requirements_text.strip():
            self.selected_requirement_blocks = [self.selected_requirements_text.strip()]
        self.equip_click_delay_ms = tk.IntVar(value=int(config.get("equip_click_delay_ms", 100)))
        self._coord_picker = CoordinatePicker(self.root)
        self._matcher = DivineMatcher()
        self._stop_event = threading.Event()
        self._is_running = False
        self._global_listener_running = False
        self._hotkey_enabled = False

        # UI References
        self.selected_block_input = None
        self.log_text = None
        self.selected_section = None

    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """创建 UI 界面 (Minimalist Dark)"""
        from poe2_tools.theme import ThemeManager

        # Main Container
        main = ttk.Frame(parent, style="Card.TFrame")
        main.pack(fill=BOTH, expand=True)

        # 1. Configuration (Top) - unified top anchor
        config_top = ttk.Frame(main, style="Card.TFrame", height=CONFIG_TOP_HEIGHT)
        config_top.pack(fill=X, pady=(0, 10))
        config_top.pack_propagate(False)

        header_global = ttk.Frame(config_top, style="Card.TFrame", height=SECTION_HEADER_HEIGHT)
        header_global.pack(fill=X, pady=(0, 5))
        header_global.pack_propagate(False)
        ttk.Label(header_global, text="全局设置", style="Card.TLabel").pack(side=LEFT, padx=5)

        config_frame = ttk.Frame(config_top, style="Card.TFrame", padding=(10, 0, 10, 0))
        config_frame.pack(fill=X)

        # Row 1: Coordinates
        row_coords = ttk.Frame(config_frame, style="Card.TFrame", height=CONFIG_COORD_ROW_HEIGHT)
        row_coords.pack(fill=X, pady=(0, 10))
        row_coords.pack_propagate(False)

        for label, var, key in [("神圣石位置", self.orb_pos, "orb"), ("装备位置", self.equip_pos, "equip")]:
            f = ttk.Frame(row_coords, style="Card.TFrame")
            f.pack(side=LEFT, padx=(0, 20))
            ttk.Label(f, text=label, style="Content.TLabel").pack(side=LEFT, padx=(0, 5))
            entry = ttk.Entry(
                f,
                textvariable=var,
                width=12,
                justify=CENTER,
                state="readonly",
                style="Numeric.TEntry",
                font=("Times New Roman", 10, "bold"),
            )
            entry.pack(side=LEFT, padx=(0, 5))
            entry.bind("<Button-1>", lambda _e, k=key: self._pick_coordinate(k))

        # Row 2: Rules & Params
        row_rules = ttk.Frame(config_frame, style="Card.TFrame", height=CONFIG_CONTROLS_ROW_HEIGHT)
        row_rules.pack(fill=X)
        row_rules.pack_propagate(False)


        ttk.Label(row_rules, text="判定模式：", style="Content.TLabel").pack(side=LEFT, pady=4)
        self.mode_all_btn = ttk.Button(
            row_rules,
            text="全部词条",
            command=lambda: self._set_target_mode("all_stats"),
            style="Mode.TButton",
            width=10,
        )
        self.mode_all_btn.pack(side=LEFT, padx=5, pady=4)
        self.mode_selected_btn = ttk.Button(
            row_rules,
            text="指定词条",
            command=lambda: self._set_target_mode("selected"),
            style="Mode.TButton",
            width=10,
        )
        self.mode_selected_btn.pack(side=LEFT, padx=5, pady=4)

        ttk.Label(row_rules, text="阈值（%）：", style="Content.TLabel").pack(side=LEFT, padx=(20, 0), pady=4)
        ttk.Entry(row_rules, textvariable=self.fractured_threshold_percent, width=6, justify=CENTER, font=("Times New Roman", 10, "bold")).pack(side=LEFT, padx=5, pady=4)

        ttk.Label(row_rules, text="延时（ms）：", style="Content.TLabel").pack(side=LEFT, padx=(20, 0), pady=4)
        ttk.Entry(row_rules, textvariable=self.equip_click_delay_ms, width=6, justify=CENTER, font=("Times New Roman", 10, "bold")).pack(side=LEFT, padx=5, pady=4)


        # 2. Main Content (Vertical Stack)
        
        # Section: Requirements Input (Fixed Height)
        # We wrap it in a frame that always exists, but its inner content (textbox) is packed/hidden
        self.selected_section = ttk.Frame(main, style="Card.TFrame")
        self.selected_section.pack(fill=X, pady=(0, 10))

        self.selected_block_input = AffixBlockInput(
            self.selected_section,
            theme_manager=ThemeManager,
            section_style="Card.TFrame",
        )
        self.selected_block_input.set_blocks(self.selected_requirement_blocks)

        # Section: Logs (Expanded)
        self.frame_log = ttk.Frame(main, style="Card.TFrame")
        self.frame_log.pack(fill=BOTH, expand=True, pady=(0, 10))

        lbl_log = ttk.Frame(self.frame_log, style="Card.TFrame", height=SECTION_HEADER_HEIGHT)
        lbl_log.pack(fill=X, pady=(0, 5))
        lbl_log.pack_propagate(False)
        ttk.Label(lbl_log, text="运行日志", style="Card.TLabel").pack(side=LEFT, padx=5)
        ttk.Button(lbl_log, text="清空", command=self._clear_logs, style="outline", width=6).pack(side=RIGHT, padx=5)

        log_body = ttk.Frame(self.frame_log, style="Card.TFrame")
        log_body.pack(fill=BOTH, expand=True)

        self.log_scroll = ttk.Scrollbar(log_body, orient=VERTICAL)
        self.log_scroll.pack(side=RIGHT, fill=Y)

        self.log_text = tk.Text(
            log_body, height=10, state=DISABLED, wrap=WORD,
            font=("Times New Roman", 10, "bold"), relief="flat",
            bg=ThemeManager.COLOR_BG_INPUT, fg=ThemeManager.COLOR_TEXT_MAIN,
            borderwidth=1,
            highlightthickness=0,
            yscrollcommand=self.log_scroll.set,
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.log_scroll.config(command=self.log_text.yview)
        self._logger = UiLogger(self.root, self.log_text, max_lines=800)


        self._update_target_mode_ui()

        self._start_global_listener()
        return main

    def log(self, msg: str, level: str = "info"):
        if not hasattr(self, "_logger"):
            return
        mapper = {
            "debug": self._logger.debug,
            "info": self._logger.info,
            "success": self._logger.success,
            "warning": self._logger.warning,
            "error": self._logger.error,
        }
        mapper.get(level.lower(), self._logger.info)(msg)

    def _clear_logs(self):
        if hasattr(self, "_logger"):
            self._logger.clear()

    def _scroll_logs_bottom(self):
        if hasattr(self, "_logger"):
            self._logger.scroll_to_bottom()

    def _pick_coordinate(self, target_type: str):
        x, y = self._coord_picker.pick(f"将鼠标移到{target_type}上，单击左键。")
        (self.orb_pos if target_type == "orb" else self.equip_pos).set(f"({x}, {y})")

    def _parse_tuple(self, s: str) -> tuple:
        return tuple(int(x.strip()) for x in s.strip("() ").split(",") if x.strip())

    def _update_target_mode_ui(self):
        if not hasattr(self, "selected_section") or not hasattr(self, "frame_log"):
            return
        if self.selected_section is None or self.frame_log is None:
            return

        self._refresh_target_mode_buttons()

        if self.target_mode.get() == "selected":
            # Repack input section BEFORE logs
            self.selected_section.pack(fill=X, pady=(0, 10), before=self.frame_log)
        else:
            self.selected_section.pack_forget()

    def _set_target_mode(self, mode: str):
        self.target_mode.set(mode)
        self._update_target_mode_ui()

    def _refresh_target_mode_buttons(self):
        if hasattr(self, "mode_all_btn") and self.mode_all_btn is not None:
            self.mode_all_btn.configure(
                style="Mode.Active.TButton" if self.target_mode.get() == "all_stats" else "Mode.TButton"
            )
        if hasattr(self, "mode_selected_btn") and self.mode_selected_btn is not None:
            self.mode_selected_btn.configure(
                style="Mode.Active.TButton" if self.target_mode.get() == "selected" else "Mode.TButton"
            )

    def _start_global_listener(self):
        if self._global_listener_running:
            return

        def listener():
            self._global_listener_running = True
            while self._global_listener_running:
                if not self._hotkey_enabled:
                    time.sleep(0.05)
                    continue
                if keyboard and keyboard.is_pressed("f12"):
                    if self._is_running:
                        self._stop_event.set()
                        self.root.after(80, self.root.deiconify)
                        self.root.after(120, self.root.lift)
                        self.root.after(0, lambda: self.log("F12 按下，正在停止", "warning"))
                    else:
                        self.root.after(0, self.root.iconify)
                        self.root.after(0, lambda: self.log("F12 按下，准备启动神圣石洗炼", "info"))
                        self.root.after(10, self._start_reforge)
                    time.sleep(0.5)
                time.sleep(0.05)

        threading.Thread(target=listener, daemon=True).start()
        self.log("F12 热键已启用（开始/停止）", "success")

    def _start_reforge(self):
        if self._is_running:
            return
        try:
            orb_pos = self._parse_tuple(self.orb_pos.get())
            equip_pos = self._parse_tuple(self.equip_pos.get())
            if len(orb_pos) != 2 or len(equip_pos) != 2:
                raise ValueError("神圣石/装备坐标格式错误")
            selected_blocks = self.selected_block_input.get_blocks() if self.selected_block_input else []
            if self.target_mode.get() == "selected" and not selected_blocks:
                self.log("请先输入指定词条块", "warning")
                return
            cfg = {
                "REFORGE_ORB_POS": orb_pos,
                "TARGET_EQUIP_POS": equip_pos,
                "FRACTURED_THRESHOLD_PERCENT": float(self.fractured_threshold_percent.get()),
                "TARGET_MODE": self.target_mode.get(),
                "SELECTED_REQUIREMENT_BLOCKS": selected_blocks,
                "EQUIP_CLICK_DELAY_MS": int(self.equip_click_delay_ms.get()),
            }
            self.save_config()
            threading.Thread(target=self._run_reforge, args=(cfg,), daemon=True).start()
        except Exception as e:
            self.log(f"启动失败：{e}", "error")

    def _run_reforge(self, config: dict):
        self.log("神圣石洗炼流程启动", "success")
        self.log("按 F12 可随时中断", "info")
        time.sleep(0.5)
        started_at = time.time()

        orb_x, orb_y = config["REFORGE_ORB_POS"]
        equip_x, equip_y = config["TARGET_EQUIP_POS"]
        threshold_percent = float(config["FRACTURED_THRESHOLD_PERCENT"])
        target_mode = config.get("TARGET_MODE", "all_stats")
        selected_blocks = config.get("SELECTED_REQUIREMENT_BLOCKS", [])
        if not selected_blocks:
            selected_text = config.get("SELECTED_REQUIREMENTS_TEXT", "")
            if selected_text.strip():
                selected_blocks = [selected_text.strip()]
        equip_click_delay_s = max(0.0, int(config.get("EQUIP_CLICK_DELAY_MS", 100)) / 1000.0)

        pyautogui.moveTo(orb_x, orb_y, duration=0.03)
        pyautogui.rightClick()
        time.sleep(0.3)
        pyautogui.keyDown("shift")

        success = False
        attempt = 0
        stop_reason = "未命中结束"
        last_result = None
        self._is_running = True
        self._stop_event.clear()
        if target_mode == "selected":
            total = len(selected_blocks)
            self.log(
                f"开始神圣石洗炼（模式：指定词条块 {total} 组全达标，阈值：{threshold_percent:.0f}%），按 F12 停止",
                "success",
            )
        else:
            self.log(f"开始神圣石洗炼（模式：全部词条，阈值：{threshold_percent:.0f}%），按 F12 停止", "success")

        try:
            while True:
                if self._stop_event.is_set():
                    self.log("检测到 F12，神圣石洗炼已中断", "warning")
                    stop_reason = "F12 中断"
                    break

                attempt += 1
                pyautogui.moveTo(equip_x, equip_y, duration=0.03)
                pyautogui.click()
                time.sleep(equip_click_delay_s)

                pyperclip.copy("")
                pyautogui.keyDown("alt")
                time.sleep(0.02)
                pyautogui.hotkey("ctrl", "c")
                time.sleep(0.01)
                pyautogui.keyUp("alt")

                data = ""
                for _ in range(3):
                    if self._stop_event.is_set():
                        break
                    data = pyperclip.paste()
                    if data:
                        break
                    time.sleep(0.01)

                if not data:
                    if attempt % 20 == 0:
                        self.log(f"第 {attempt} 次：无法读取剪贴板", "warning")
                    continue

                if target_mode == "selected":
                    result = self._matcher.match_selected_blocks_threshold(
                        data,
                        selected_blocks,
                        threshold_percent,
                        log_fn=self.log,
                    )
                else:
                    result = self._matcher.match_fractured_threshold(data, threshold_percent, log_fn=self.log)
                last_result = result
                if result.matched:
                    self.log(
                        f"第 {attempt} 次神圣石洗炼命中！({result.reason})",
                        "success",
                    )
                    success = True
                    stop_reason = "命中目标"
                    break

                if attempt % 10 == 0:
                    self.log(f"第 {attempt} 次：未命中（{result.reason}；目标 {threshold_percent:.0f}%）", "debug")

        finally:
            pyautogui.keyUp("alt")
            pyautogui.keyUp("shift")
            self._is_running = False

        stopped = self._stop_event.is_set()
        status = "成功" if success else "已中断" if stopped else "结束"
        msg = f"{status}！共 {attempt} 次。"
        self.log(f"神圣石洗炼结束：{msg}", "success" if success else "warning")
        elapsed = max(0.0, time.time() - started_at)
        last_reason = last_result.reason if last_result is not None else "无"
        last_ratio = f"{last_result.total_ratio * 100:.1f}%" if last_result is not None else "无"
        self.log(
            f"结束汇总：原因={stop_reason}，耗时={elapsed:.1f}s，尝试={attempt} 次，最后判定={last_reason}，最后比例={last_ratio}",
            "info",
        )

    def get_config(self) -> dict:
        selected_text = ""
        selected_blocks = []
        try:
            selected_blocks = self.selected_block_input.get_blocks() if self.selected_block_input else self.selected_requirement_blocks
            selected_text = "\n".join(selected_blocks)
        except Exception:
            selected_text = self.selected_requirements_text
            selected_blocks = self.selected_requirement_blocks
        return {
            "orb_pos": self.orb_pos.get(),
            "equip_pos": self.equip_pos.get(),
            "fractured_threshold_percent": self.fractured_threshold_percent.get(),
            "target_mode": self.target_mode.get(),
            "selected_requirements_text": selected_text,
            "selected_requirement_blocks": selected_blocks,
            "equip_click_delay_ms": self.equip_click_delay_ms.get(),
        }

    def save_config(self):
        config_manager.save_divine_reforge_config(self.get_config())

    def set_hotkey_enabled(self, enabled: bool):
        self._hotkey_enabled = bool(enabled)

    def toggle_running(self):
        if self._is_running:
            self._stop_event.set()
        else:
            self._start_reforge()

    def is_running(self) -> bool:
        return self._is_running
