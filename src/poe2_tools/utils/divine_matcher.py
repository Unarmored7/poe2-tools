"""Divine orb matching for affix range values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValueCheck:
    current: int
    min_value: int
    max_value: int
    ratio: float
    passed: bool


@dataclass
class FracturedLineCheck:
    line: str
    checks: list[ValueCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)


@dataclass
class DivineMatchResult:
    matched: bool
    threshold_percent: float
    fractured_lines: list[FracturedLineCheck] = field(default_factory=list)
    total_current: int = 0
    total_max: int = 0
    total_ratio: float = 0.0
    matched_count: int = 0
    required_count: int = 0
    reason: str = ""


class DivineMatcher:
    """Evaluate affix values against max-range percentage."""

    VALUE_RANGE_PATTERN = re.compile(
        r"([+-]?\d+)\(\s*([+-]?\d+)\s*[-–—~～]\s*([+-]?\d+)\s*\)"
    )
    FRACTURED_KEYWORDS = ("fractured", "破裂", "碎裂")
    DESECRATED_KEYWORDS = ("desecrated", "褻瀆", "亵渎")

    def match_fractured_threshold(
        self,
        clipboard_text: str,
        threshold_percent: float,
        log_fn=None,
    ) -> DivineMatchResult:
        if not clipboard_text.strip():
            return DivineMatchResult(False, threshold_percent, reason="剪贴板文本为空")

        threshold_percent = max(0.0, min(float(threshold_percent), 100.0))
        threshold = threshold_percent / 100.0
        if log_fn:
            log_fn(f"判定模式：全部词条综合，阈值={threshold_percent:.1f}%", "info")
        fractured_lines = self._extract_all_stat_checks(clipboard_text, threshold, log_fn=log_fn)

        if not fractured_lines:
            return DivineMatchResult(
                matched=False,
                threshold_percent=threshold_percent,
                fractured_lines=[],
                matched_count=0,
                required_count=0,
                reason="未检测到可评估词条",
            )

        total_current, total_max, total_ratio = self._aggregate_totals(fractured_lines)
        all_passed = total_ratio >= threshold
        if log_fn:
            for item in fractured_lines:
                details = self._format_checks(item.checks)
                log_fn(f"词条明细：{item.line} | {details}", "debug")
            log_fn(
                f"综合比例：{total_current}/{total_max}={total_ratio * 100:.1f}%（目标 >= {threshold_percent:.1f}%）",
                "success" if all_passed else "warning",
            )

        reason = "综合达标" if all_passed else "综合未达标"
        return DivineMatchResult(
            matched=all_passed,
            threshold_percent=threshold_percent,
            fractured_lines=fractured_lines,
            total_current=total_current,
            total_max=total_max,
            total_ratio=total_ratio,
            matched_count=sum(1 for i in fractured_lines if i.passed),
            required_count=len(fractured_lines),
            reason=reason,
        )

    def match_selected_fractured_threshold(
        self,
        clipboard_text: str,
        selected_lines_text: str,
        threshold_percent: float,
        log_fn=None,
    ) -> DivineMatchResult:
        if not clipboard_text.strip():
            return DivineMatchResult(False, threshold_percent, reason="剪贴板文本为空")

        selected_lines = [ln.strip() for ln in selected_lines_text.splitlines() if ln.strip()]
        if not selected_lines:
            return DivineMatchResult(False, threshold_percent, reason="未输入目标词条")

        threshold_percent = max(0.0, min(float(threshold_percent), 100.0))
        threshold = threshold_percent / 100.0
        if log_fn:
            log_fn(
                f"判定模式：指定词条综合，阈值={threshold_percent:.1f}%，目标词条数={len(selected_lines)}",
                "info",
            )
            for idx, line in enumerate(selected_lines, start=1):
                log_fn(f"目标[{idx}]：{line}", "debug")
        fractured_stats = [
            item.line for item in self._extract_all_stat_checks(clipboard_text, threshold, log_fn=log_fn)
        ]
        required = len(selected_lines)

        matched_checks: list[FracturedLineCheck] = []
        matched_count = 0

        for req_line in selected_lines:
            pattern = self._build_identity_pattern(req_line)
            found_line = None
            for stat_line in fractured_stats:
                if re.search(pattern, stat_line, re.IGNORECASE):
                    found_line = stat_line
                    if log_fn:
                        log_fn(f"匹配到装备词条：{stat_line}", "debug")
                    break

            if not found_line:
                if log_fn:
                    log_fn(f"未找到目标词条：{req_line}", "debug")
                continue

            checks = self._evaluate_line(found_line, threshold)
            line_check = FracturedLineCheck(line=found_line, checks=checks)
            matched_checks.append(line_check)
            matched_count += 1
            details = self._format_checks(line_check.checks)
            if log_fn:
                log_fn(f"目标词条明细：{req_line} | {details}", "debug")

        total_current, total_max, total_ratio = self._aggregate_totals(matched_checks)
        ok = matched_count >= required and total_ratio >= threshold
        reason = (
            f"目标词条匹配 {matched_count}/{len(selected_lines)}，综合 {total_current}/{total_max}={total_ratio * 100:.1f}%"
            if ok
            else f"目标词条未达标：匹配 {matched_count}/{len(selected_lines)}，综合 {total_current}/{total_max}={total_ratio * 100:.1f}%"
        )
        if log_fn:
            log_fn(
                f"目标词条综合比例：{total_current}/{total_max}={total_ratio * 100:.1f}%（目标 >= {threshold_percent:.1f}%）",
                "success" if ok else "warning",
            )
        return DivineMatchResult(
            matched=ok,
            threshold_percent=threshold_percent,
            fractured_lines=matched_checks,
            total_current=total_current,
            total_max=total_max,
            total_ratio=total_ratio,
            matched_count=matched_count,
            required_count=required,
            reason=reason,
        )

    def match_selected_blocks_threshold(
        self,
        clipboard_text: str,
        selected_blocks: list[str],
        threshold_percent: float,
        log_fn=None,
    ) -> DivineMatchResult:
        if not clipboard_text.strip():
            return DivineMatchResult(False, threshold_percent, reason="剪贴板文本为空")

        blocks = [b.strip() for b in selected_blocks if b and b.strip()]
        if not blocks:
            return DivineMatchResult(False, threshold_percent, reason="未输入目标词条块")

        threshold_percent = max(0.0, min(float(threshold_percent), 100.0))
        threshold = threshold_percent / 100.0
        all_stat_lines = [
            item.line for item in self._extract_all_stat_checks(clipboard_text, threshold, log_fn=log_fn)
        ]

        if log_fn:
            log_fn(
                f"判定模式：指定词条块综合，阈值={threshold_percent:.1f}%，目标词条块数={len(blocks)}",
                "info",
            )

        matched_checks: list[FracturedLineCheck] = []
        matched_blocks = 0

        for idx, block in enumerate(blocks, start=1):
            req_lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if not req_lines:
                continue

            block_checks: list[FracturedLineCheck] = []
            block_ok = True

            for req_line in req_lines:
                pattern = self._build_identity_pattern(req_line)
                found_line = None
                for stat_line in all_stat_lines:
                    if re.search(pattern, stat_line, re.IGNORECASE):
                        found_line = stat_line
                        break

                if not found_line:
                    block_ok = False
                    if log_fn:
                        log_fn(f"词条块 #{idx} 缺少行：{req_line}", "debug")
                    break

                checks = self._evaluate_line(found_line, threshold)
                line_check = FracturedLineCheck(line=found_line, checks=checks)
                block_checks.append(line_check)

            if block_ok:
                matched_blocks += 1
                matched_checks.extend(block_checks)
                if log_fn:
                    log_fn(f"词条块 #{idx} 命中（{len(req_lines)} 行）", "success")
            elif log_fn:
                log_fn(f"词条块 #{idx} 未命中", "debug")

        required = len(blocks)
        total_current, total_max, total_ratio = self._aggregate_totals(matched_checks)
        ok = matched_blocks >= required and total_ratio >= threshold
        reason = (
            f"目标词条块匹配 {matched_blocks}/{required}，综合 {total_current}/{total_max}={total_ratio * 100:.1f}%"
            if ok
            else f"目标词条块未达标：匹配 {matched_blocks}/{required}，综合 {total_current}/{total_max}={total_ratio * 100:.1f}%"
        )
        if log_fn:
            log_fn(
                f"目标词条块综合比例：{total_current}/{total_max}={total_ratio * 100:.1f}%（目标 >= {threshold_percent:.1f}%）",
                "success" if ok else "warning",
            )

        return DivineMatchResult(
            matched=ok,
            threshold_percent=threshold_percent,
            fractured_lines=matched_checks,
            total_current=total_current,
            total_max=total_max,
            total_ratio=total_ratio,
            matched_count=matched_blocks,
            required_count=required,
            reason=reason,
        )

    def _extract_fractured_checks(self, clipboard_text: str, threshold: float, log_fn=None) -> list[FracturedLineCheck]:
        lines = [ln.strip() for ln in clipboard_text.splitlines()]
        fractured_lines: list[FracturedLineCheck] = []
        expect_stat_line = False

        for line in lines:
            if not line or line == "--------":
                continue

            if self._is_fractured_marker(line):
                if log_fn:
                    log_fn(f"检测到标记行：{line}", "debug")

                # 某些文本会把标记与词条写在同一行
                checks_same_line = self._evaluate_line(line, threshold)
                if checks_same_line:
                    fractured_lines.append(FracturedLineCheck(line=line, checks=checks_same_line))
                    expect_stat_line = False
                else:
                    expect_stat_line = True
                continue

            if not expect_stat_line:
                continue

            expect_stat_line = False
            checks = self._evaluate_line(line, threshold)
            if checks:
                fractured_lines.append(FracturedLineCheck(line=line, checks=checks))
            elif log_fn:
                    log_fn(f"词条无法解析数值范围，已跳过：{line}", "debug")

        if log_fn:
            log_fn(f"检测到可评估词条数：{len(fractured_lines)}", "info")
            if not fractured_lines:
                ranged = sum(1 for ln in lines if self.VALUE_RANGE_PATTERN.search(ln))
                log_fn(
                    f"未识别到标记词条，包含范围数字的行数={ranged}；如有需要请切换到“指定词条”模式",
                    "warning",
                )

        return fractured_lines

    def _extract_all_stat_checks(self, clipboard_text: str, threshold: float, log_fn=None) -> list[FracturedLineCheck]:
        lines = [ln.strip() for ln in clipboard_text.splitlines()]
        stat_lines: list[FracturedLineCheck] = []

        for line in lines:
            if not line or line == "--------":
                continue
            if line.startswith("{") and line.endswith("}"):
                continue

            checks = self._evaluate_line(line, threshold)
            if checks:
                stat_lines.append(FracturedLineCheck(line=line, checks=checks))

        if log_fn:
            log_fn(f"检测到可评估词条数：{len(stat_lines)}", "info")
            if not stat_lines:
                ranged = sum(1 for ln in lines if self.VALUE_RANGE_PATTERN.search(ln))
                log_fn(f"未识别到可评估词条，包含范围数字的行数={ranged}", "warning")

        return stat_lines

    def _is_fractured_marker(self, line: str) -> bool:
        low = line.lower()
        return any(k in low for k in self.FRACTURED_KEYWORDS)

    def _aggregate_totals(self, checks_by_line: list[FracturedLineCheck]) -> tuple[int, int, float]:
        total_current = 0
        total_max = 0
        for line_check in checks_by_line:
            for c in line_check.checks:
                total_current += c.current
                total_max += c.max_value
        ratio = (total_current / total_max) if total_max > 0 else 0.0
        return total_current, total_max, ratio

    def _build_identity_pattern(self, line: str) -> str:
        token_pattern = (
            r"([+-]?\d+\(\s*[+-]?\d+\s*[-–—~～]\s*[+-]?\d+\s*\)"
            r"|\(\s*[+-]?\d+\s*[-–—~～]\s*[+-]?\d+\s*\)"
            r"|[+-]?\d+)"
        )
        parts = re.split(token_pattern, line)
        pattern = ""
        for part in parts:
            if not part:
                continue
            if re.fullmatch(token_pattern, part):
                if "(" in part and ")" in part:
                    pattern += r"[+-]?\d+\(\s*[+-]?\d+\s*[-–—~～]\s*[+-]?\d+\s*\)"
                else:
                    pattern += r"[+-]?\d+"
            else:
                pattern += re.escape(part).replace(r"\ ", r"\s+")
        return pattern

    def _format_checks(self, checks: list[ValueCheck]) -> str:
        parts = []
        for c in checks:
            status = "OK" if c.passed else "LOW"
            parts.append(
                f"{c.current}({c.min_value}-{c.max_value}) -> {c.current}/{c.max_value}={c.ratio * 100:.1f}% [{status}]"
            )
        return ", ".join(parts)

    def _evaluate_line(self, line: str, threshold: float) -> list[ValueCheck]:
        checks: list[ValueCheck] = []
        for match in self.VALUE_RANGE_PATTERN.finditer(line):
            current = int(match.group(1))
            min_raw = int(match.group(2))
            max_raw = int(match.group(3))
            min_value = min(min_raw, max_raw)
            max_value = max(min_raw, max_raw)
            if max_value <= 0:
                continue
            ratio = current / max_value
            checks.append(
                ValueCheck(
                    current=current,
                    min_value=min_value,
                    max_value=max_value,
                    ratio=ratio,
                    passed=ratio >= threshold,
                )
            )
        return checks
