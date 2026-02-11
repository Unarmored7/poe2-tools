"""
文本匹配模块

解析用户输入的词条范围描述，通过正则匹配 POE2 剪贴板文本判断装备词条是否满足需求。

用法：
    matcher = TextMatcher()
    # 解析用户输入（含范围）
    reqs = matcher.parse_requirements("增加 (45-50)%最大能量護盾")
    # 匹配 POE2 Alt+Ctrl+C 的装备文本
    result = matcher.check_match(clipboard_text, reqs)
"""

import re
from dataclasses import dataclass, field


@dataclass
class ModRequirement:
    """一条词条需求"""
    original_text: str          # 用户输入的原始文本
    pattern: str                # 生成的正则表达式
    min_values: list[int] = field(default_factory=list)  # 范围下限列表
    max_values: list[int] = field(default_factory=list)  # 范围上限列表
    mod_type: str = "number"    # "number" | "text"


@dataclass
class MatchResult:
    """匹配结果"""
    matched: bool
    matched_line: str = ""       # 匹配到的行
    matched_values: list[int] = field(default_factory=list)  # 实际数值
    matched_count: int = 0
    required_count: int = 0
    requirement: ModRequirement | None = None


class TextMatcher:
    """POE2 装备文本匹配器"""

    # 各种破折号/连字符统一处理
    DASH_CHARS = r'[-–—~～]'

    def parse_requirements(self, user_text: str) -> list[ModRequirement]:
        """
        解析用户输入的词条需求文本
        
        支持格式：
            增加 (45-50)%最大能量護盾
            增加 (45—50)%最大能量護盾
            +1 最大旋风导管数量
            附加 (20-30) 到 (40-50) 物理傷害
            升級範圍至大範圍             （纯文本匹配）
        """
        requirements = []
        # 统一破折号
        clean = user_text.replace('–', '-').replace('—', '-').replace('～', '-').replace('~', '-')
        
        for line in clean.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            req = self._parse_line(line)
            if req:
                requirements.append(req)
        
        return requirements

    def _parse_line(self, line: str) -> ModRequirement | None:
        """解析单行需求"""
        # 没有数字 → 纯文本匹配
        if not re.search(r'\d', line):
            # 把空格变成 \s+, 让匹配更宽松
            regex = re.escape(line).replace(r'\ ', r'\s+')
            return ModRequirement(
                original_text=line,
                pattern=regex,
                mod_type="text"
            )

        # 有数字 → 解析范围
        try:
            # 找所有 (min-max) 或单独数值
            # 匹配: (45-50), (20-30), 45-50, 单独的 45
            range_pattern = r'\(?(\d+)(?:-(\d+))?\)?'
            ranges = re.findall(range_pattern, line)
            
            min_values = []
            max_values = []
            for min_val, max_val in ranges:
                min_v = int(min_val)
                max_v = int(max_val) if max_val else min_v
                min_values.append(min_v)
                max_values.append(max_v)
            
            # 构造正则：把数字范围替换为 (\d+) 捕获组
            parts = re.split(r'\(?\d+(?:-\d+)?\)?', line)
            regex = ""
            for i, part in enumerate(parts):
                regex += re.escape(part).replace(r'\ ', r'\s+')
                if i < len(parts) - 1:
                    regex += r'(\d+)'
            
            return ModRequirement(
                original_text=line,
                pattern=regex,
                min_values=min_values,
                max_values=max_values,
                mod_type="number"
            )
        except Exception:
            return None

    def check_match(
        self,  
        clipboard_text: str, 
        requirements: list[ModRequirement],
        log_fn=None
    ) -> MatchResult:
        """
        检查剪贴板装备文本是否满足所有需求
        
        Args:
            clipboard_text: POE2 Alt+Ctrl+C 复制的装备文本
            requirements: 解析后的需求列表
            log_fn: 日志回调
            
        Returns:
            MatchResult: 是否匹配 + 详情
        """
        return self.check_match_at_least(
            clipboard_text=clipboard_text,
            requirements=requirements,
            min_match_count=len(requirements),
            log_fn=log_fn,
        )

    def check_match_any(
        self,
        clipboard_text: str,
        requirements: list[ModRequirement],
        log_fn=None
    ) -> MatchResult:
        """
        检查剪贴板装备文本是否满足任意一条需求（OR 逻辑）
        """
        return self.check_match_at_least(
            clipboard_text=clipboard_text,
            requirements=requirements,
            min_match_count=1,
            log_fn=log_fn,
        )

    def check_match_at_least(
        self,
        clipboard_text: str,
        requirements: list[ModRequirement],
        min_match_count: int,
        log_fn=None,
    ) -> MatchResult:
        """检查是否至少命中 K 条需求（N 选 K）。"""
        if not clipboard_text or not requirements:
            return MatchResult(matched=False, matched_count=0, required_count=max(1, min_match_count))

        total = len(requirements)
        required = max(1, min(min_match_count, total))
        clean_data = self._normalize_clipboard_text(clipboard_text)

        matched_count = 0
        first_unmatched = None
        first_matched = None

        for req in requirements:
            single = self._check_single(clean_data, req, log_fn)
            if single.matched:
                matched_count += 1
                if first_matched is None:
                    first_matched = single
            elif first_unmatched is None:
                first_unmatched = req

        is_ok = matched_count >= required
        if log_fn:
            log_fn(f"命中统计: {matched_count}/{total} (目标 >= {required})", "info")

        if not is_ok:
            return MatchResult(
                matched=False,
                matched_count=matched_count,
                required_count=required,
                requirement=first_unmatched,
            )

        return MatchResult(
            matched=True,
            matched_line=first_matched.matched_line if first_matched else "",
            matched_values=first_matched.matched_values if first_matched else [],
            matched_count=matched_count,
            required_count=required,
            requirement=first_matched.requirement if first_matched else None,
        )

    def check_grouped_match_at_least(
        self,
        clipboard_text: str,
        requirement_groups: list[list[ModRequirement]],
        min_match_count: int,
        log_fn=None,
    ) -> MatchResult:
        """检查是否至少命中 K 个词条组（组内全部命中才算一组）。"""
        if not clipboard_text or not requirement_groups:
            return MatchResult(matched=False, matched_count=0, required_count=max(1, min_match_count))

        total = len(requirement_groups)
        required = max(1, min(min_match_count, total))
        clean_data = self._normalize_clipboard_text(clipboard_text)

        matched_groups = 0
        first_unmatched_req = None

        for idx, group in enumerate(requirement_groups, start=1):
            group_ok = True
            for req in group:
                single = self._check_single(clean_data, req, log_fn)
                if not single.matched:
                    group_ok = False
                    if first_unmatched_req is None:
                        first_unmatched_req = req
                    break
            if group_ok:
                matched_groups += 1
                if log_fn:
                    log_fn(f"词条组 #{idx} 命中（{len(group)} 行）", "success")
            elif log_fn:
                log_fn(f"词条组 #{idx} 未命中", "debug")

        is_ok = matched_groups >= required
        if log_fn:
            log_fn(f"词条组命中统计: {matched_groups}/{total} (目标 >= {required})", "info")

        return MatchResult(
            matched=is_ok,
            matched_count=matched_groups,
            required_count=required,
            requirement=first_unmatched_req,
        )

    def _normalize_clipboard_text(self, clipboard_text: str) -> str:
        clean_data = clipboard_text.lower()
        clean_data = re.sub(r'.*\(fractured\).*', '', clean_data)
        clean_data = re.sub(r'.*\(implicit\).*', '', clean_data)
        # Alt+Ctrl+C 文本会包含当前值后的范围标注，如 107(101-110)
        # 混沌石匹配按“当前值”比较区间，因此这里移除括号内范围，统一成非 Alt 形态。
        clean_data = re.sub(
            rf"\(\s*[+-]?\d+\s*{self.DASH_CHARS}\s*[+-]?\d+\s*\)",
            "",
            clean_data,
        )
        clean_data = clean_data.replace(',', '')
        return clean_data

    def _check_single(
        self, 
        clean_data: str, 
        req: ModRequirement,
        log_fn=None
    ) -> MatchResult:
        """检查单条需求是否匹配"""
        matches = re.finditer(req.pattern, clean_data, re.IGNORECASE)
        
        for match in matches:
            # 纯文本匹配
            if req.mod_type == "text":
                if log_fn:
                    log_fn(f"✓ 文本匹配: {req.original_text}", "success")
                return MatchResult(
                    matched=True,
                    matched_line=match.group(0),
                    requirement=req
                )
            
            # 数值范围匹配
            game_values = []
            try:
                game_values = [int(v) for v in match.groups() if v is not None]
            except (ValueError, TypeError):
                continue
            
            if len(game_values) != len(req.min_values):
                continue
            
            # 检查所有数值是否在范围内
            all_in_range = all(
                mn <= val <= mx 
                for val, mn, mx in zip(game_values, req.min_values, req.max_values)
            )
            
            if all_in_range:
                if log_fn:
                    log_fn(f"✓ 范围匹配: {req.original_text} → {game_values}", "success")
                return MatchResult(
                    matched=True,
                    matched_line=match.group(0),
                    matched_values=game_values,
                    requirement=req
                )
            else:
                if log_fn:
                    log_fn(
                        f"✗ 值超范围: {req.original_text} → {game_values} "
                        f"(需要 {list(zip(req.min_values, req.max_values))})",
                        "debug"
                    )
        
        return MatchResult(matched=False, requirement=req)
