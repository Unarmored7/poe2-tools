"""
AI 装备检查模块

使用 DashScope OCR + LLM 判断装备属性是否符合预期。
"""

import os
import base64
from io import BytesIO
from typing import Optional

import pyautogui
from PIL import Image

# DashScope API
try:
    from dashscope import MultiModalConversation, Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("⚠️ dashscope 模块未安装，AI 装备检查功能不可用")


# API Key 配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")


def set_api_key(api_key: str):
    """
    设置 DashScope API Key
    
    Args:
        api_key: API Key
    """
    global DASHSCOPE_API_KEY
    DASHSCOPE_API_KEY = api_key


def image_to_base64(image: Image.Image) -> str:
    """
    将 PIL Image 转换为 Base64 编码字符串
    
    Args:
        image: PIL Image 对象
        
    Returns:
        Base64 编码字符串
    """
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text_from_region(region: tuple) -> Optional[str]:
    """
    使用 DashScope 对指定屏幕区域进行 OCR
    
    Args:
        region: (left, top, width, height) 定义要截取的屏幕区域
        
    Returns:
        提取出的文字，如果失败则返回 None
    """
    if not DASHSCOPE_AVAILABLE:
        print("❌ DashScope 不可用")
        return None
        
    if not DASHSCOPE_API_KEY:
        print("❌ 请设置 DASHSCOPE_API_KEY 环境变量")
        return None

    try:
        left, top, width, height = region
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        img_base64 = image_to_base64(screenshot)

        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/png;base64,{img_base64}"},
                    {"text": "请识别这张图片中的所有文字内容，按原有格式输出，不要添加任何解释。"}
                ]
            }
        ]

        response = MultiModalConversation.call(
            model="qwen-vl-plus",
            messages=messages,
            api_key=DASHSCOPE_API_KEY
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            print(f"❌ OCR 失败: {response.code} - {response.message}")
            return None

    except Exception as e:
        print(f"❌ OCR 异常: {e}")
        return None


def check_stats_with_llm(stats_text: str, 
                         expected_description: str,
                         model: str = "qwen-turbo") -> bool:
    """
    使用 LLM 判断装备属性是否符合预期
    
    Args:
        stats_text: OCR 识别出的装备属性文本
        expected_description: 用户描述的预期属性
        model: 使用的 LLM 模型
        
    Returns:
        是否符合预期
    """
    if not DASHSCOPE_AVAILABLE:
        print("❌ DashScope 不可用")
        return False
        
    if not DASHSCOPE_API_KEY:
        print("❌ 请设置 DASHSCOPE_API_KEY 环境变量")
        return False

    prompt = f"""你是一个 Path of Exile 游戏装备属性判断助手。

用户期望的装备属性描述：
{expected_description}

实际识别出的装备属性：
{stats_text}

请判断实际属性是否满足用户的期望。只回答 "是" 或 "否"，不要有任何其他解释。"""

    try:
        response = Generation.call(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=DASHSCOPE_API_KEY
        )

        if response.status_code == 200:
            answer = response.output.text.strip().lower()
            return answer in ["是", "yes", "true", "满足", "符合"]
        else:
            print(f"❌ LLM 判断失败: {response.code} - {response.message}")
            return False

    except Exception as e:
        print(f"❌ LLM 异常: {e}")
        return False


def click_at_coordinates(x: int, y: int, 
                         button: str = "left",
                         clicks: int = 1,
                         interval: float = 0.0,
                         duration: float = 0.0) -> bool:
    """
    在指定坐标执行点击操作
    
    Args:
        x: 屏幕 X 坐标
        y: 屏幕 Y 坐标
        button: 鼠标按键
        clicks: 点击次数
        interval: 点击间隔
        duration: 移动时长
        
    Returns:
        是否成功
    """
    try:
        pyautogui.click(x, y, clicks=clicks, interval=interval, 
                       duration=duration, button=button)
        return True
    except Exception as e:
        print(f"❌ 点击失败: {e}")
        return False


def process_item_and_check(item_coords: tuple,
                           equipment_coords: tuple,
                           stats_region: tuple,
                           expected_description: str,
                           delay: float = 0.5) -> bool:
    """
    处理物品并检查属性
    
    Args:
        item_coords: 物品坐标 (x, y)
        equipment_coords: 装备槽坐标 (x, y)
        stats_region: 属性面板区域 (left, top, width, height)
        expected_description: 期望属性描述
        delay: 操作间隔
        
    Returns:
        是否满足预期属性
    """
    import time
    
    # 右键点击物品
    click_at_coordinates(item_coords[0], item_coords[1], button="right")
    time.sleep(delay)
    
    # 左键点击装备槽
    click_at_coordinates(equipment_coords[0], equipment_coords[1], button="left")
    time.sleep(delay)
    
    # OCR 识别属性
    stats_text = extract_text_from_region(stats_region)
    if not stats_text:
        print("⚠️ 无法识别装备属性")
        return False
    
    print(f"📋 识别到的属性:\n{stats_text}")
    
    # LLM 判断
    result = check_stats_with_llm(stats_text, expected_description)
    
    if result:
        print("✅ 装备属性符合预期！")
    else:
        print("❌ 装备属性不符合预期")
        
    return result
