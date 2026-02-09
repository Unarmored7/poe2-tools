"""
图像处理工具模块

提供血条/蓝条检测、图像预处理等公共功能。
"""

import cv2
import numpy as np


def preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    图像预处理：转灰度 + OTSU 二值化
    
    Args:
        img: BGR 或灰度图像
        
    Returns:
        二值化后的灰度图像
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def calculate_hp_percentage(img: np.ndarray) -> float | None:
    """
    计算血条百分比（支持红色和绿色血条）
    
    Args:
        img: RGB 格式的 numpy 数组 (H, W, 3)
        
    Returns:
        血条百分比 (0.0-100.0)，无效时返回 None
    """
    if img.size == 0 or img.shape[0] < 10 or img.shape[1] < 3:
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # 红色掩码（H 在 0-20 或 160-180 范围）
    lower_red1 = np.array([0, 70, 60])
    upper_red1 = np.array([20, 255, 255])
    lower_red2 = np.array([160, 70, 60])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.bitwise_or(
        cv2.inRange(hsv, lower_red1, upper_red1),
        cv2.inRange(hsv, lower_red2, upper_red2)
    )

    # 绿色掩码
    lower_green = np.array([40, 70, 60])
    upper_green = np.array([80, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # 合并掩码
    combined_mask = cv2.bitwise_or(mask_red, mask_green)

    # 形态学去噪
    kernel = np.ones((2, 2), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

    h, w = combined_mask.shape
    colored_rows = np.where(np.any(combined_mask > 0, axis=1))[0]

    if len(colored_rows) == 0:
        return 0.0

    top_most_colored_row = np.min(colored_rows)
    filled_height = h - top_most_colored_row
    percentage = (filled_height / h) * 100
    return max(0.0, min(100.0, percentage))


def calculate_mp_percentage(img: np.ndarray) -> float | None:
    """
    计算蓝条百分比
    
    Args:
        img: RGB 格式的 numpy 数组 (H, W, 3)
        
    Returns:
        蓝条百分比 (0.0-100.0)，无效时返回 None
    """
    if img.size == 0 or img.shape[0] < 10 or img.shape[1] < 3:
        return None
        
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    
    # 蓝色掩码
    lower = np.array([90, 70, 60])
    upper = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    
    # 形态学去噪
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    h, w = mask.shape
    colored_rows = np.where(np.any(mask > 0, axis=1))[0]
    
    if len(colored_rows) == 0:
        return 0.0
        
    top_most = np.min(colored_rows)
    filled = h - top_most
    return max(0.0, min(100.0, (filled / h) * 100))


def is_valid_hp_bar(img: np.ndarray, min_ratio: float = 0.1) -> bool:
    """
    判断图像是否包含有效的红色或绿色血条
    
    Args:
        img: RGB 格式的 numpy 数组
        min_ratio: 有效像素最小占比
        
    Returns:
        是否为有效血条
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # 红色掩码
    mask_red1 = cv2.inRange(hsv, np.array([0, 50, 40]), np.array([25, 255, 255]))
    mask_red2 = cv2.inRange(hsv, np.array([150, 50, 40]), np.array([180, 255, 255]))
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # 绿色掩码
    mask_green = cv2.inRange(hsv, np.array([40, 50, 40]), np.array([80, 255, 255]))

    combined = cv2.bitwise_or(mask_red, mask_green)
    total = combined.size
    colored = cv2.countNonZero(combined)
    return (colored / total) > min_ratio


def is_valid_mp_bar(img: np.ndarray, min_ratio: float = 0.1) -> bool:
    """
    判断图像是否包含有效的蓝条
    
    Args:
        img: RGB 格式的 numpy 数组
        min_ratio: 有效像素最小占比
        
    Returns:
        是否为有效蓝条
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array([80, 50, 40]), np.array([150, 255, 255]))
    total = mask.size
    colored = cv2.countNonZero(mask)
    return (colored / total) > min_ratio


def load_and_preprocess_template(path: str) -> np.ndarray:
    """
    加载并预处理模板图像
    
    Args:
        path: 模板图像路径
        
    Returns:
        预处理后的模板图像
        
    Raises:
        ValueError: 无法加载模板
    """
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None:
        raise ValueError(f"无法加载模板: {path}")
    return preprocess_image(template)
