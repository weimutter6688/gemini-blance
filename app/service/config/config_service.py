"""
配置服务模块
"""
import os
from typing import Any, Dict
import json
from dotenv import load_dotenv, set_key

from app.config.config import settings, Settings


class ConfigService:
    """配置服务类，用于管理应用程序配置"""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        config_dict = {}
        
        # 获取Settings类的所有字段
        for field_name in settings.model_fields:
            value = getattr(settings, field_name)
            config_dict[field_name] = value
            
        return config_dict
    
    @staticmethod
    def update_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新配置
        
        Args:
            config_data (Dict[str, Any]): 新的配置数据
            
        Returns:
            Dict[str, Any]: 更新后的配置字典
        """
        # 更新settings对象
        for key, value in config_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        # 更新.env文件
        ConfigService._update_env_file(config_data)
        
        return ConfigService.get_config()
    
    @staticmethod
    def reset_config() -> Dict[str, Any]:
        """
        重置配置到默认值
        
        Returns:
            Dict[str, Any]: 重置后的配置字典
        """
        # 重新加载.env文件
        load_dotenv(override=True)
        
        # 重新创建settings对象
        global settings
        settings = Settings()
        
        return ConfigService.get_config()
    
    @staticmethod
    def _update_env_file(config_data: Dict[str, Any]) -> None:
        """
        更新.env文件
        
        Args:
            config_data (Dict[str, Any]): 配置数据
        """
        env_path = ".env"
        
        # 确保.env文件存在
        if not os.path.exists(env_path):
            # 如果不存在，复制.env.example
            if os.path.exists(".env.example"):
                with open(".env.example", "r", encoding="utf-8") as example_file:
                    with open(env_path, "w", encoding="utf-8") as env_file:
                        env_file.write(example_file.read())
            else:
                # 创建空文件
                open(env_path, "w", encoding="utf-8").close()
        
        # 更新.env文件中的配置
        for key, value in config_data.items():
            # 处理不同类型的值
            if isinstance(value, list):
                # 将列表转换为JSON字符串
                env_value = json.dumps(value)
            elif isinstance(value, bool):
                # 布尔值转换为小写字符串
                env_value = str(value).lower()
            else:
                env_value = str(value)
            
            # 更新.env文件
            set_key(env_path, key, env_value)
