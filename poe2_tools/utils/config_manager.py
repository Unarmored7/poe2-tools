"""
配置管理工具模块

提供统一的配置加载、保存、导入、导出功能。
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# 默认配置目录
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


class ConfigManager:
    """配置管理器"""
    
    # 预定义配置文件名
    POTION_CONFIG = "potion_config.json"
    REFORGE_CONFIG = "reforge_config.json"
    
    def __init__(self, config_dir: Optional[Path | str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为 config/
        """
        self.config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_config_path(self, filename: str) -> Path:
        """获取配置文件完整路径"""
        return self.config_dir / filename
    
    def load(self, filename: str, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            filename: 配置文件名
            default: 默认配置值
            
        Returns:
            配置字典
        """
        config_path = self._get_config_path(filename)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 配置加载失败 ({filename}): {e}")
                
        return default or {}
    
    def save(self, filename: str, config: Dict[str, Any]) -> bool:
        """
        保存配置文件
        
        Args:
            filename: 配置文件名
            config: 配置字典
            
        Returns:
            是否保存成功
        """
        config_path = self._get_config_path(filename)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ 配置保存失败 ({filename}): {e}")
            return False
    
    def export_to(self, filename: str, export_path: Path | str) -> bool:
        """
        导出配置到指定路径
        
        Args:
            filename: 配置文件名
            export_path: 导出路径
            
        Returns:
            是否导出成功
        """
        config = self.load(filename)
        export_path = Path(export_path)
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ 配置导出失败: {e}")
            return False
    
    def import_from(self, filename: str, import_path: Path | str) -> Dict[str, Any]:
        """
        从指定路径导入配置
        
        Args:
            filename: 配置文件名（用于保存导入的配置）
            import_path: 导入路径
            
        Returns:
            导入的配置字典
        """
        import_path = Path(import_path)
        
        if not import_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {import_path}")
            
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 保存到默认位置
            self.save(filename, config)
            return config
        except Exception as e:
            raise ValueError(f"配置导入失败: {e}")
    
    def load_potion_config(self) -> Dict[str, Any]:
        """加载喝药配置"""
        return self.load(self.POTION_CONFIG, {
            "hp_key": "1",
            "hp_threshold": 35.0,
            "disable_hp": False,
            "enable_hp_timer": False,
            "hp_timer_interval": 5.0,
            "mp_key": "2",
            "mp_threshold": 35.0,
            "disable_mp": False,
            "enable_mp_timer": False,
            "mp_timer_interval": 8.0,
            "check_interval": 0.3,
            "hp_region": None,
            "mp_region": None,
        })
    
    def save_potion_config(self, config: Dict[str, Any]) -> bool:
        """保存喝药配置"""
        return self.save(self.POTION_CONFIG, config)
    
    def load_reforge_config(self) -> Dict[str, Any]:
        """加载洗练配置"""
        return self.load(self.REFORGE_CONFIG, {
            "orb_pos": "(?, ?)",
            "equip_pos": "(?, ?)",
            "mod_region": "(?, ?, ?, ?)",
            "main_threshold": 0.85,
            "tier_threshold": 0.90,
            "max_attempts": 200,
            "orb_delay": 0.25,
            "equip_click_delay": 0.75,
            "alt_screenshot_delay": 0.0,
            "loop_random_max": 0.02,
            "main_template_paths": [],
            "tier_template_path": None,
        })
    
    def save_reforge_config(self, config: Dict[str, Any]) -> bool:
        """保存洗练配置"""
        return self.save(self.REFORGE_CONFIG, config)


# 全局配置管理器实例
config_manager = ConfigManager()
