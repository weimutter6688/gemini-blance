"""
应用程序配置模块
"""
import datetime
import json
from typing import List, Any, Dict, Type

from pydantic import ValidationError
from pydantic_settings import BaseSettings
from sqlalchemy import insert, update, select

from app.core.constants import API_VERSION, DEFAULT_CREATE_IMAGE_MODEL, DEFAULT_FILTER_MODELS, DEFAULT_MODEL, DEFAULT_STREAM_CHUNK_SIZE, DEFAULT_STREAM_LONG_TEXT_THRESHOLD, DEFAULT_STREAM_MAX_DELAY, DEFAULT_STREAM_MIN_DELAY, DEFAULT_STREAM_SHORT_TEXT_THRESHOLD, DEFAULT_TIMEOUT
from app.log.logger import get_config_logger
# 延迟导入以避免循环依赖，仅在 sync_initial_settings 中使用
# from app.database.connection import database
# from app.database.models import Settings as SettingsModel
# from app.database.services import get_all_settings # get_all_settings 可能不适合启动时调用，直接查询

logger = get_config_logger()


class Settings(BaseSettings):
    """应用程序配置"""
    # 数据库配置
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    
    # API相关配置
    API_KEYS: List[str]
    ALLOWED_TOKENS: List[str]
    BASE_URL: str = f"https://generativelanguage.googleapis.com/{API_VERSION}"
    AUTH_TOKEN: str = ""
    MAX_FAILURES: int = 3
    TEST_MODEL: str = DEFAULT_MODEL
    TIME_OUT: int = DEFAULT_TIMEOUT
    
    # 模型相关配置
    SEARCH_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    IMAGE_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    FILTERED_MODELS: List[str] = DEFAULT_FILTER_MODELS
    TOOLS_CODE_EXECUTION_ENABLED: bool = False
    SHOW_SEARCH_LINK: bool = True
    SHOW_THINKING_PROCESS: bool = True
    
    # 图像生成相关配置
    PAID_KEY: str = ""
    CREATE_IMAGE_MODEL: str = DEFAULT_CREATE_IMAGE_MODEL
    UPLOAD_PROVIDER: str = "smms"
    SMMS_SECRET_TOKEN: str = ""
    PICGO_API_KEY: str = ""
    CLOUDFLARE_IMGBED_URL: str = ""
    CLOUDFLARE_IMGBED_AUTH_CODE: str = ""
    
    # 流式输出优化器配置
    STREAM_OPTIMIZER_ENABLED: bool = False
    STREAM_MIN_DELAY: float = DEFAULT_STREAM_MIN_DELAY
    STREAM_MAX_DELAY: float = DEFAULT_STREAM_MAX_DELAY
    STREAM_SHORT_TEXT_THRESHOLD: int = DEFAULT_STREAM_SHORT_TEXT_THRESHOLD
    STREAM_LONG_TEXT_THRESHOLD: int = DEFAULT_STREAM_LONG_TEXT_THRESHOLD
    STREAM_CHUNK_SIZE: int = DEFAULT_STREAM_CHUNK_SIZE
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置默认AUTH_TOKEN（如果未提供）
        if not self.AUTH_TOKEN and self.ALLOWED_TOKENS:
            self.AUTH_TOKEN = self.ALLOWED_TOKENS[0]

# 创建全局配置实例
settings = Settings()

def _parse_db_value(key: str, db_value: str, target_type: Type) -> Any:
    """尝试将数据库字符串值解析为目标 Python 类型"""
    try:
        if target_type == List[str]:
            # 尝试解析 JSON 列表，如果失败则按逗号分割
            try:
                parsed = json.loads(db_value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                # 回退到逗号分割，去除空格
                return [item.strip() for item in db_value.split(',') if item.strip()]
            # 如果解析后不是列表或解析失败，返回空列表或进行其他处理
            logger.warning(f"Could not parse '{db_value}' as List[str] for key '{key}', falling back to comma split or empty list.")
            return [item.strip() for item in db_value.split(',') if item.strip()] # Fallback
        elif target_type == bool:
            return db_value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(db_value)
        elif target_type == float:
            return float(db_value)
        else: # 默认为 str 或其他 pydantic 能处理的类型
            return db_value
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to parse db_value '{db_value}' for key '{key}' as type {target_type}: {e}. Using original string value.")
        return db_value # 解析失败则返回原始字符串

async def sync_initial_settings():
    """
    应用启动时同步配置：
    1. 从数据库加载设置。
    2. 将数据库设置合并到内存 settings (数据库优先)。
    3. 将最终的内存 settings 同步回数据库。
    """
    # 延迟导入以避免循环依赖和确保数据库连接已初始化
    from app.database.connection import database
    from app.database.models import Settings as SettingsModel

    global settings
    logger.info("Starting initial settings synchronization...")

    if not database.is_connected:
        try:
            await database.connect()
            logger.info("Database connection established for initial sync.")
        except Exception as e:
            logger.error(f"Failed to connect to database for initial settings sync: {e}. Skipping sync.")
            return

    try:
        # 1. 从数据库加载设置
        db_settings_raw: List[Dict[str, Any]] = []
        try:
            query = select(SettingsModel.key, SettingsModel.value)
            results = await database.fetch_all(query)
            db_settings_raw = [{"key": row["key"], "value": row["value"]} for row in results]
            logger.info(f"Fetched {len(db_settings_raw)} settings from database.")
        except Exception as e:
            logger.error(f"Failed to fetch settings from database: {e}. Proceeding with environment/dotenv settings.")
            # 即使数据库读取失败，也要继续执行，确保基于 env/dotenv 的配置能同步到数据库

        db_settings_map: Dict[str, str] = {s['key']: s['value'] for s in db_settings_raw}

        # 2. 将数据库设置合并到内存 settings (数据库优先)
        updated_in_memory = False

        for key, db_value in db_settings_map.items():
            if hasattr(settings, key):
                target_type = Settings.__annotations__.get(key)
                if target_type:
                    try:
                        parsed_db_value = _parse_db_value(key, db_value, target_type)
                        memory_value = getattr(settings, key)

                        # 比较解析后的值和内存中的值
                        # 注意：对于列表等复杂类型，直接比较可能不够健壮，但这里简化处理
                        if parsed_db_value != memory_value:
                             # 检查类型是否匹配，以防解析函数返回了不兼容的类型
                            # 优先处理 List[str] 类型，避免直接对泛型使用 isinstance
                            if target_type == List[str]:
                                if isinstance(parsed_db_value, list):
                                    # 可以选择性地添加对列表元素的检查，但这里保持简化
                                    setattr(settings, key, parsed_db_value)
                                    logger.info(f"Updated setting '{key}' in memory from database value (List[str]).")
                                    updated_in_memory = True
                                else:
                                     logger.warning(f"Parsed DB value type mismatch for key '{key}'. Expected List[str], got {type(parsed_db_value)}. Skipping update.")
                            # 对于其他非泛型类型，使用常规的 isinstance 检查
                            elif isinstance(parsed_db_value, target_type):
                                setattr(settings, key, parsed_db_value)
                                logger.info(f"Updated setting '{key}' in memory from database value.")
                                updated_in_memory = True
                            else:
                                logger.warning(f"Parsed DB value type mismatch for key '{key}'. Expected {target_type}, got {type(parsed_db_value)}. Skipping update.")

                    except Exception as e:
                        logger.error(f"Error processing database setting for key '{key}': {e}")
            else:
                 logger.warning(f"Database setting '{key}' not found in Settings model definition. Ignoring.")


        # 如果内存中有更新，重新验证 Pydantic 模型（可选但推荐）
        if updated_in_memory:
            try:
                # 重新加载以确保类型转换和验证
                settings = Settings(**settings.model_dump())
                logger.info("Settings object re-validated after merging database values.")
            except ValidationError as e:
                 logger.error(f"Validation error after merging database settings: {e}. Settings might be inconsistent.")


        # 3. 将最终的内存 settings 同步回数据库
        final_memory_settings = settings.model_dump()
        settings_to_update: List[Dict[str, Any]] = []
        settings_to_insert: List[Dict[str, Any]] = []
        now = datetime.datetime.now(datetime.timezone.utc)

        existing_db_keys = set(db_settings_map.keys())

        for key, value in final_memory_settings.items():
            # 序列化值为字符串或 JSON 字符串
            if isinstance(value, list):
                db_value = json.dumps(value)
            elif isinstance(value, bool):
                db_value = str(value).lower()
            else:
                db_value = str(value)

            data = {
                'key': key,
                'value': db_value,
                'description': f"{key} configuration setting", # 默认描述
                'updated_at': now
            }

            if key in existing_db_keys:
                # 仅当值与数据库中的不同时才更新
                if db_settings_map[key] != db_value:
                    settings_to_update.append(data)
            else:
                # 如果键不在数据库中，则插入
                data['created_at'] = now
                settings_to_insert.append(data)

        # 在事务中执行批量插入和更新
        if settings_to_insert or settings_to_update:
            try:
                async with database.transaction():
                    if settings_to_insert:
                        # 获取现有描述以避免覆盖
                        query_existing = select(SettingsModel.key, SettingsModel.description).where(SettingsModel.key.in_([s['key'] for s in settings_to_insert]))
                        existing_desc = {row['key']: row['description'] for row in await database.fetch_all(query_existing)}
                        for item in settings_to_insert:
                            item['description'] = existing_desc.get(item['key'], item['description'])

                        query_insert = insert(SettingsModel).values(settings_to_insert)
                        await database.execute(query=query_insert)
                        logger.info(f"Synced (inserted) {len(settings_to_insert)} settings to database.")

                    if settings_to_update:
                        # 获取现有描述以避免覆盖
                        query_existing = select(SettingsModel.key, SettingsModel.description).where(SettingsModel.key.in_([s['key'] for s in settings_to_update]))
                        existing_desc = {row['key']: row['description'] for row in await database.fetch_all(query_existing)}

                        for setting_data in settings_to_update:
                            setting_data['description'] = existing_desc.get(setting_data['key'], setting_data['description'])
                            query_update = (
                                update(SettingsModel)
                                .where(SettingsModel.key == setting_data['key'])
                                .values(
                                    value=setting_data['value'],
                                    description=setting_data['description'],
                                    updated_at=setting_data['updated_at']
                                )
                            )
                            await database.execute(query=query_update)
                        logger.info(f"Synced (updated) {len(settings_to_update)} settings to database.")
            except Exception as e:
                logger.error(f"Failed to sync settings to database during startup: {str(e)}")
        else:
            logger.info("No setting changes detected between memory and database during initial sync.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during initial settings sync: {e}")
    finally:
        if database.is_connected:
             try:
                 # Don't disconnect if it's managed elsewhere (e.g., FastAPI lifespan)
                 # await database.disconnect()
                 # logger.info("Database connection closed after initial sync.")
                 pass # Assume connection lifecycle is managed by the application lifespan
             except Exception as e:
                 logger.error(f"Error disconnecting database after initial sync: {e}")

    logger.info("Initial settings synchronization finished.")
