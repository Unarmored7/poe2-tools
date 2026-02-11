"""
公共工具模块

提供血条/蓝条检测、区域选择、配置管理、文本匹配等公共功能。
"""

from poe2_tools.utils.image_processing import (
    calculate_hp_percentage,
    calculate_mp_percentage,
    is_valid_hp_bar,
    is_valid_mp_bar,
)
from poe2_tools.utils.region_selector import RegionSelector, CoordinatePicker
from poe2_tools.utils.config_manager import ConfigManager
from poe2_tools.utils.ui_logger import UiLogger
from poe2_tools.utils.text_matcher import TextMatcher
from poe2_tools.utils.divine_matcher import DivineMatcher
from poe2_tools.utils.dialogs import AppDialog
from poe2_tools.utils.app_assets import apply_window_icon, resolve_app_icon_path

__all__ = [
    "calculate_hp_percentage",
    "calculate_mp_percentage",
    "is_valid_hp_bar",
    "is_valid_mp_bar",
    "RegionSelector",
    "CoordinatePicker",
    "ConfigManager",
    "UiLogger",
    "TextMatcher",
    "DivineMatcher",
    "AppDialog",
    "apply_window_icon",
    "resolve_app_icon_path",
]
