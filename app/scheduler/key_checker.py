from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.service.key.key_manager import get_key_manager_instance
from app.service.chat.gemini_chat_service import GeminiChatService
from app.domain.gemini_models import GeminiRequest, GeminiContent
from app.config.config import settings
from app.log.logger import Logger # 导入 Logger 类

logger = Logger.setup_logger("scheduler") # 使用 Logger.setup_logger

async def check_failed_keys():
    """
    定时检查失败次数大于0的API密钥，并尝试验证它们。
    如果验证成功，重置失败计数；如果失败，增加失败计数。
    """
    logger.info("Starting scheduled check for failed API keys...")
    try:
        key_manager = await get_key_manager_instance()
        # 确保 KeyManager 已经初始化
        if not key_manager or not hasattr(key_manager, 'key_failure_counts'):
            logger.warning("KeyManager instance not available or not initialized. Skipping check.")
            return

        # 创建 GeminiChatService 实例用于验证
        # 注意：这里直接创建实例，而不是通过依赖注入，因为这是后台任务
        chat_service = GeminiChatService(settings.BASE_URL, key_manager)

        # 获取需要检查的 key 列表 (失败次数 > 0)
        keys_to_check = []
        async with key_manager.failure_count_lock: # 访问共享数据需要加锁
            # 复制一份以避免在迭代时修改字典
            failure_counts_copy = key_manager.key_failure_counts.copy()
            keys_to_check = [key for key, count in failure_counts_copy.items() if count > 0] # 检查所有失败次数大于0的key

        if not keys_to_check:
            logger.info("No keys with failure count > 0 found. Skipping verification.")
            return

        logger.info(f"Found {len(keys_to_check)} keys with failure count > 0 to verify.")

        for key in keys_to_check:
            # 隐藏部分 key 用于日志记录
            log_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else key
            logger.info(f"Verifying key: {log_key}...")
            try:
                # 构造测试请求
                gemini_request = GeminiRequest(
                    contents=[
                        GeminiContent(
                            role="user",
                            parts=[{"text": "hi"}] # 使用简单的文本进行验证
                        )
                    ]
                )
                # 调用 generate_content 进行验证
                await chat_service.generate_content(
                    settings.TEST_MODEL, # 使用配置中定义的测试模型
                    gemini_request,
                    key
                )
                # 如果没有抛出异常，说明 key 有效
                logger.info(f"Key {log_key} verification successful. Resetting failure count.")
                await key_manager.reset_key_failure_count(key)
            except Exception as e:
                # 验证失败，增加失败计数
                logger.warning(f"Key {log_key} verification failed: {str(e)}. Incrementing failure count.")
                # 直接操作计数器，需要加锁
                async with key_manager.failure_count_lock:
                    # 再次检查 key 是否存在且失败次数未达上限
                    if key in key_manager.key_failure_counts and key_manager.key_failure_counts[key] < key_manager.MAX_FAILURES:
                        key_manager.key_failure_counts[key] += 1
                        logger.info(f"Failure count for key {log_key} incremented to {key_manager.key_failure_counts[key]}.")
                    elif key in key_manager.key_failure_counts:
                         logger.warning(f"Key {log_key} reached MAX_FAILURES ({key_manager.MAX_FAILURES}). Not incrementing further.")


    except Exception as e:
        logger.error(f"An error occurred during the scheduled key check: {str(e)}", exc_info=True)

def setup_scheduler():
    """设置并启动 APScheduler"""
    scheduler = AsyncIOScheduler(timezone=str(settings.TIMEZONE)) # 从配置读取时区
    # 添加定时任务，例如每小时执行一次 (可以调整)
    scheduler.add_job(check_failed_keys, 'interval', hours=settings.CHECK_INTERVAL_HOURS)
    scheduler.start()
    logger.info(f"Scheduler started. Key check job scheduled to run every {settings.CHECK_INTERVAL_HOURS} hour(s).")
    return scheduler

# 可以在这里添加一个全局的 scheduler 实例，以便在应用关闭时优雅地停止
scheduler_instance = None

def start_scheduler():
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = setup_scheduler()

def stop_scheduler():
    global scheduler_instance
    if scheduler_instance and scheduler_instance.running:
        scheduler_instance.shutdown()
        logger.info("Scheduler stopped.")