"""Thread-safe UI logger for Tk/ttkbootstrap text widgets."""

from __future__ import annotations

import re
import time
from tkinter import font as tkfont
from queue import Empty, Queue


class UiLogger:
    """Append leveled log records to a text widget safely."""

    _PREFIX_TAB_1 = "72p"
    _PREFIX_TAB_2 = "124p"

    _LEVEL_STYLE = {
        "DEBUG": {"tag": "log_debug", "label": "DEBUG"},
        "INFO": {"tag": "log_info", "label": "INFO"},
        "SUCCESS": {"tag": "log_success", "label": "SUCCESS"},
        "WARNING": {"tag": "log_warning", "label": "WARNING"},
        "ERROR": {"tag": "log_error", "label": "ERROR"},
    }

    def __init__(self, root, text_widget, max_lines: int = 500):
        self.root = root
        self.text = text_widget.text if hasattr(text_widget, "text") else text_widget
        self.max_lines = max_lines
        self._queue: Queue[tuple[str, str]] = Queue()
        self._setup_tags()
        self._setup_scroll_bindings()
        self._schedule_drain()

    def _setup_tags(self) -> None:
        level_colors = {
            "debug": "#6c757d",
            "info": "#9ec5fe",
            "success": "#75b798",
            "warning": "#ffda6a",
            "error": "#f1aeb5",
        }
        self._level_label_width = max(len(v["label"]) for v in self._LEVEL_STYLE.values())
        sample_prefix = f"00:00:00 | {'X' * self._level_label_width} | "
        prefix_px = tkfont.Font(font=(self.FONT_EN, 10, "bold")).measure(sample_prefix)

        self.text.tag_configure(
            "log_prefix",
            font=(self.FONT_EN, 10, "bold"),
            foreground="#111111",
        )
        for level, color in level_colors.items():
            self.text.tag_configure(
                f"log_{level}_cn",
                foreground="#111111",
                font=(self.FONT_CN, 10, "bold"),
                lmargin2=prefix_px,
            )
            self.text.tag_configure(
                f"log_{level}_en",
                foreground="#111111",
                font=(self.FONT_EN, 10, "bold"),
                lmargin2=prefix_px,
            )
            self.text.tag_configure(
                f"log_level_{level}",
                foreground=color,
                font=(self.FONT_EN, 10, "bold"),
            )

    def _setup_scroll_bindings(self) -> None:
        self.text.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.text.bind("<Button-4>", lambda e: self._scroll_units(-3), add="+")
        self.text.bind("<Button-5>", lambda e: self._scroll_units(3), add="+")

    def _on_mousewheel(self, event):
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self._scroll_units(delta * 3)
        return "break"

    def _scroll_units(self, units: int):
        if not self.text.winfo_exists():
            return "break"
        self.text.yview_scroll(units, "units")
        return "break"

    def _schedule_drain(self) -> None:
        if self.text.winfo_exists():
            self.root.after(50, self._drain)

    def _drain(self) -> None:
        if not self.text.winfo_exists():
            return

        at_bottom_before = self.text.yview()[1] >= 0.999
        changed = False
        self.text.config(state="normal")
        try:
            while True:
                level, msg = self._queue.get_nowait()
                self._append_line(level, msg)
                changed = True
        except Empty:
            pass
        finally:
            if changed:
                self._trim_lines()
                if at_bottom_before:
                    self.text.see("end")
            self.text.config(state="disabled")
            self._schedule_drain()

    def _append_line(self, level: str, message: str) -> None:
        style = self._LEVEL_STYLE.get(level, self._LEVEL_STYLE["INFO"])
        ts = time.strftime("%H:%M:%S")
        level_padded = style["label"].ljust(self._level_label_width)
        self.text.insert("end", f"{ts} | ", "log_prefix")
        self.text.insert("end", level_padded, f"log_level_{style['tag'].replace('log_', '')}")
        self.text.insert("end", " | ", "log_prefix")

        level_key = style["tag"].replace("log_", "")
        for seg, is_cjk in self._split_segments(message):
            tag = f"log_{level_key}_{'cn' if is_cjk else 'en'}"
            self.text.insert("end", seg, tag)
        self.text.insert("end", "\n", f"log_{level_key}_en")

    def _split_segments(self, message: str) -> list[tuple[str, bool]]:
        if not message:
            return []
        segments: list[tuple[str, bool]] = []
        current = []
        current_is_cjk = self._is_cjk_char(message[0])

        for ch in message:
            is_cjk = self._is_cjk_char(ch)
            if is_cjk != current_is_cjk and current:
                segments.append(("".join(current), current_is_cjk))
                current = [ch]
                current_is_cjk = is_cjk
            else:
                current.append(ch)
        if current:
            segments.append(("".join(current), current_is_cjk))
        return segments

    def _is_cjk_char(self, ch: str) -> bool:
        return bool(self._CJK_RE.match(ch))

    def _trim_lines(self) -> None:
        line_count = int(self.text.index("end-1c").split(".")[0])
        overflow = line_count - self.max_lines
        if overflow > 0:
            self.text.delete("1.0", f"{overflow + 1}.0")

    def clear(self) -> None:
        if not self.text.winfo_exists():
            return
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def scroll_to_bottom(self) -> None:
        if not self.text.winfo_exists():
            return
        self.text.see("end")

    def debug(self, message: str) -> None:
        self._queue.put(("DEBUG", message))

    def info(self, message: str) -> None:
        self._queue.put(("INFO", message))

    def success(self, message: str) -> None:
        self._queue.put(("SUCCESS", message))

    def warning(self, message: str) -> None:
        self._queue.put(("WARNING", message))

    def error(self, message: str) -> None:
        self._queue.put(("ERROR", message))
    FONT_CN = "Consolas"
    FONT_EN = "Consolas"
    _CJK_RE = re.compile(r"[\u3400-\u9FFF]")
