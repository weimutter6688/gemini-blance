from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from copy import deepcopy
from app.config.config import settings
from app.log.logger import get_gemini_logger
from app.core.security import SecurityService
from app.domain.gemini_models import GeminiContent, GeminiRequest
from app.service.chat.gemini_chat_service import GeminiChatService
from app.service.key.key_manager import KeyManager, get_key_manager_instance
from app.service.model.model_service import ModelService
from app.handler.retry_handler import RetryHandler
from app.core.constants import API_VERSION

# 路由设置
router = APIRouter(prefix=f"/gemini/{API_VERSION}")
router_v1beta = APIRouter(prefix=f"/{API_VERSION}")
logger = get_gemini_logger()

# 初始化服务
security_service = SecurityService(settings.ALLOWED_TOKENS, settings.AUTH_TOKEN)
model_service = ModelService(settings.SEARCH_MODELS, settings.IMAGE_MODELS)


async def get_key_manager():
    """获取密钥管理器实例"""
    return await get_key_manager_instance()


async def get_next_working_key(key_manager: KeyManager = Depends(get_key_manager)):
    """获取下一个可用的API密钥"""
    return await key_manager.get_next_working_key()


async def get_chat_service(key_manager: KeyManager = Depends(get_key_manager)):
    """获取Gemini聊天服务实例"""
    return GeminiChatService(settings.BASE_URL, key_manager)


@router.get("/models")
@router_v1beta.get("/models")
async def list_models(
    _=Depends(security_service.verify_key_or_goog_api_key),
    key_manager: KeyManager = Depends(get_key_manager)
):
    """获取可用的Gemini模型列表"""
    logger.info("-" * 50 + "list_gemini_models" + "-" * 50)
    logger.info("Handling Gemini models list request")
    
    api_key = await key_manager.get_first_valid_key()
    logger.info(f"Using API key: {api_key}")
    
    models_json = model_service.get_gemini_models(api_key)
    model_mapping = {x.get("name", "").split("/", maxsplit=1)[1]: x for x in models_json["models"]}
    
    # 添加搜索模型
    if model_service.search_models:
        for name in model_service.search_models:
            model = model_mapping.get(name)
            if not model:
                continue
                
            item = deepcopy(model)
            item["name"] = f"models/{name}-search"
            display_name = f'{item.get("displayName")} For Search'
            item["displayName"] = display_name
            item["description"] = display_name
            
            models_json["models"].append(item)
    
    # 添加图像生成模型
    if model_service.image_models:
        for name in model_service.image_models:
            model = model_mapping.get(name)
            if not model:
                continue
                
            item = deepcopy(model)
            item["name"] = f"models/{name}-image"
            display_name = f'{item.get("displayName")} For Image'
            item["displayName"] = display_name
            item["description"] = display_name
            
            models_json["models"].append(item)
            
    return models_json


@router.post("/models/{model_name}:generateContent")
@router_v1beta.post("/models/{model_name}:generateContent")
@RetryHandler(max_retries=settings.MAX_RETRIES, key_arg="api_key")
async def generate_content(
    model_name: str,
    request: GeminiRequest,
    _=Depends(security_service.verify_key_or_goog_api_key),
    api_key: str = Depends(get_next_working_key),
    chat_service: GeminiChatService = Depends(get_chat_service)
):
    """非流式生成内容"""
    logger.info("-" * 50 + "gemini_generate_content" + "-" * 50)
    logger.info(f"Handling Gemini content generation request for model: {model_name}")
    logger.info(f"Request: \n{request.model_dump_json(indent=2)}")
    logger.info(f"Using API key: {api_key}")
    
    if not model_service.check_model_support(model_name):
        raise HTTPException(status_code=400, detail=f"Model {model_name} is not supported")
    
    try:
        response = await chat_service.generate_content(
            model=model_name,
            request=request,
            api_key=api_key
        )
        return response
    except Exception as e:
        logger.error(f"Chat completion failed after retries: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat completion failed") from e


@router.post("/models/{model_name}:streamGenerateContent")
@router_v1beta.post("/models/{model_name}:streamGenerateContent")
@RetryHandler(max_retries=settings.MAX_RETRIES, key_arg="api_key")
async def stream_generate_content(
    model_name: str,
    request: GeminiRequest,
    _=Depends(security_service.verify_key_or_goog_api_key),
    api_key: str = Depends(get_next_working_key),
    chat_service: GeminiChatService = Depends(get_chat_service)
):
    """流式生成内容"""
    logger.info("-" * 50 + "gemini_stream_generate_content" + "-" * 50)
    logger.info(f"Handling Gemini streaming content generation for model: {model_name}")
    logger.info(f"Request: \n{request.model_dump_json(indent=2)}")
    logger.info(f"Using API key: {api_key}")
    
    if not model_service.check_model_support(model_name):
        raise HTTPException(status_code=400, detail=f"Model {model_name} is not supported")
    
    try:
        response_stream = chat_service.stream_generate_content(
            model=model_name,
            request=request,
            api_key=api_key
        )
        return StreamingResponse(response_stream, media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Streaming request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Streaming request failed") from e

@router.post("/reset-all-fail-counts")
async def reset_all_key_fail_counts(key_type: str = None, key_manager: KeyManager = Depends(get_key_manager)):
    """批量重置Gemini API密钥的失败计数，可选择性地仅重置有效或无效密钥"""
    logger.info("-" * 50 + "reset_all_gemini_key_fail_counts" + "-" * 50)
    logger.info(f"Received reset request with key_type: {key_type}")
    
    try:
        # 获取分类后的密钥
        keys_by_status = await key_manager.get_keys_by_status()
        valid_keys = keys_by_status.get("valid_keys", {})
        invalid_keys = keys_by_status.get("invalid_keys", {})
        
        # 根据类型选择要重置的密钥
        keys_to_reset = []
        if key_type == "valid":
            keys_to_reset = list(valid_keys.keys())
            logger.info(f"Resetting only valid keys, count: {len(keys_to_reset)}")
        elif key_type == "invalid":
            keys_to_reset = list(invalid_keys.keys())
            logger.info(f"Resetting only invalid keys, count: {len(keys_to_reset)}")
        else:
            # 重置所有密钥
            await key_manager.reset_failure_counts()
            return JSONResponse({"success": True, "message": "所有密钥的失败计数已重置"})
        
        # 批量重置指定类型的密钥
        for key in keys_to_reset:
            await key_manager.reset_key_failure_count(key)
        
        return JSONResponse({
            "success": True,
            "message": f"{key_type}密钥的失败计数已重置",
            "reset_count": len(keys_to_reset)
        })
    except Exception as e:
        logger.error(f"Failed to reset key failure counts: {str(e)}")
        return JSONResponse({"success": False, "message": f"批量重置失败: {str(e)}"}, status_code=500)


@router.post("/reset-fail-count/{api_key}")
async def reset_key_fail_count(api_key: str, key_manager: KeyManager = Depends(get_key_manager)):
    """重置指定Gemini API密钥的失败计数"""
    logger.info("-" * 50 + "reset_gemini_key_fail_count" + "-" * 50)
    logger.info(f"Resetting failure count for API key: {api_key}")
    
    try:
        result = await key_manager.reset_key_failure_count(api_key)
        if result:
            return JSONResponse({"success": True, "message": "失败计数已重置"})
        return JSONResponse({"success": False, "message": "未找到指定密钥"}, status_code=404)
    except Exception as e:
        logger.error(f"Failed to reset key failure count: {str(e)}")
        return JSONResponse({"success": False, "message": f"重置失败: {str(e)}"}, status_code=500)

@router.post("/verify-key/{api_key}")
async def verify_key(api_key: str, chat_service: GeminiChatService = Depends(get_chat_service), key_manager: KeyManager = Depends(get_key_manager)):
    """验证Gemini API密钥的有效性"""
    logger.info("-" * 50 + "verify_gemini_key" + "-" * 50)
    logger.info("Verifying API key validity")
    
    try:
        # 使用generate_content接口测试key的有效性
        gemini_request = GeminiRequest(
            contents=[
                GeminiContent(
                    role="user",
                    parts=[{"text": "hi"}]
                )
            ]
        )
        
        response = await chat_service.generate_content(
            settings.TEST_MODEL,
            gemini_request,
            api_key
        )
        
        if response:
            return JSONResponse({"status": "valid"})        
    except Exception as e:
        logger.error(f"Key verification failed: {str(e)}")
        
        # 验证出现异常时增加失败计数
        async with key_manager.failure_count_lock:
            if api_key in key_manager.key_failure_counts:
                key_manager.key_failure_counts[api_key] += 1
                logger.warning(f"Verification exception for key: {api_key}, incrementing failure count")
        
        return JSONResponse({"status": "invalid", "error": str(e)})