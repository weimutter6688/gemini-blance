"""
配置服务模块
"""
import datetime
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from sqlalchemy import insert, update

from app.config.config import settings, reload_settings 
from app.database.connection import database
from app.database.models import Settings
from app.database.services import get_all_settings
from app.service.key.key_manager import get_key_manager_instance, reset_key_manager_instance
from app.log.logger import get_config_routes_logger

logger = get_config_routes_logger()


class ConfigService:
    """配置服务类，用于管理应用程序配置"""
    
    @staticmethod
    async def get_config() -> Dict[str, Any]:
        return settings.model_dump()
    
    @staticmethod
    async def update_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in config_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                logger.info(f"Updated setting in memory: {key}") 
        
        # 获取现有设置
        existing_settings_raw: List[Dict[str, Any]] = await get_all_settings()
        existing_settings_map: Dict[str, Dict[str, Any]] = {s['key']: s for s in existing_settings_raw}
        existing_keys = set(existing_settings_map.keys())

        settings_to_update: List[Dict[str, Any]] = []
        settings_to_insert: List[Dict[str, Any]] = []
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

        # 准备要更新或插入的数据
        for key, value in config_data.items():
            # 处理不同类型的值
            if isinstance(value, list):
                db_value = json.dumps(value)
            elif isinstance(value, bool):
                db_value = str(value).lower()
            else:
                db_value = str(value)

            # 仅当值发生变化时才更新
            if key in existing_keys and existing_settings_map[key]['value'] == db_value:
                continue 

            description = f"{key}配置项" 

            data = {
                'key': key,
                'value': db_value,
                'description': description,
                'updated_at': now
            }

            if key in existing_keys:
                # Preserve original description if not explicitly provided
                data['description'] = existing_settings_map[key].get('description', description)
                settings_to_update.append(data)
            else:
                data['created_at'] = now
                settings_to_insert.append(data)

        # 在事务中执行批量插入和更新
        if settings_to_insert or settings_to_update:
            try:
                async with database.transaction():
                    if settings_to_insert:
                        query_insert = insert(Settings).values(settings_to_insert)
                        await database.execute(query=query_insert)
                        logger.info(f"Bulk inserted {len(settings_to_insert)} settings.")

                    if settings_to_update:
                        for setting_data in settings_to_update:
                            query_update = (
                                update(Settings)
                                .where(Settings.key == setting_data['key'])
                                .values(
                                    value=setting_data['value'],
                                    description=setting_data['description'],
                                    updated_at=setting_data['updated_at']
                                )
                            )
                            await database.execute(query=query_update)
                        logger.info(f"Updated {len(settings_to_update)} settings.")
            except Exception as e:
                logger.error(f"Failed to bulk update/insert settings: {str(e)}")
                raise  # Re-raise the exception after logging

        # 重置并重新初始化 KeyManager
        try:
            await reset_key_manager_instance()
            await get_key_manager_instance(settings.API_KEYS)
            logger.info("KeyManager instance re-initialized with updated settings.")
        except Exception as e:
            logger.error(f"Failed to re-initialize KeyManager: {str(e)}")
            # Decide if this error should prevent returning the updated config
            # For now, we log the error and continue

        return await ConfigService.get_config()
    
    @staticmethod
    async def reset_config() -> Dict[str, Any]:
        """
        重置配置到默认值
        
        Returns:
            Dict[str, Any]: 重置后的配置字典
        """
        # 重新加载.env文件
        load_dotenv(override=True)
        # 重新加载配置对象以反映最新的环境变量
        reload_settings()
        logger.info("Settings object reloaded from environment variables.")
        # 同步数据库中的配置到settings对象
        await ConfigService._sync_db_config()
        return await ConfigService.get_config()
    
    @staticmethod
    async def _sync_db_config() -> None:
        """
        将.env文件中的配置项同步到数据库
        """
        try:
            # 获取.env文件中的所有配置项
            env_values = dotenv_values(".env")
            await ConfigService.update_config(env_values)
            
            logger.info("Synced configuration to database")
        except Exception as e:
            logger.error(f"Failed to sync configuration to database: {str(e)}")


# 添加dotenv_values函数
def dotenv_values(dotenv_path: str) -> Dict[str, str]:
    """
    从.env文件中读取配置项
    
    Args:
        dotenv_path: .env文件路径
    
    Returns:
        Dict[str, str]: 配置项字典
    """
    if not os.path.exists(dotenv_path):
        return {}
    
    result = {}
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # 去除引号
            if value and value[0] == value[-1] and value[0] in ["'", '"']:
                value = value[1:-1]
            
            result[key] = value
    
    return result
