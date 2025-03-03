from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from app.core.config import settings
from app.core.logger import get_gemini_logger
from app.core.security import SecurityService
from app.schemas.gemini_models import GeminiContent, GeminiRequest
from app.services.gemini_chat_service import GeminiChatService
from app.services.key_manager import KeyManager, get_key_manager_instance
from app.services.model_service import ModelService
from app.services.chat.retry_handler import RetryHandler

router = APIRouter(prefix="/gemini/v1beta")
router_v1beta = APIRouter(prefix="/v1beta")
logger = get_gemini_logger()

# 初始化服务
security_service = SecurityService(settings.ALLOWED_TOKENS, settings.AUTH_TOKEN)

async def get_key_manager():
    return await get_key_manager_instance()

async def get_next_working_key_wrapper(key_manager: KeyManager = Depends(get_key_manager)):
    return await key_manager.get_next_working_key()

model_service = ModelService(settings.MODEL_SEARCH)


@router.get("/models")
@router_v1beta.get("/models")
async def list_models(_=Depends(security_service.verify_key),
    key_manager: KeyManager = Depends(get_key_manager)):
    """获取可用的Gemini模型列表"""
    logger.info("-" * 50 + "list_gemini_models" + "-" * 50)
    logger.info("Handling Gemini models list request")
    api_key = await key_manager.get_next_working_key()
    logger.info(f"Using API key: {api_key}")
    models_json = model_service.get_gemini_models(api_key)
    models_json["models"].append({"name": "models/gemini-2.0-flash-exp-search", "version": "2.0",
                                  "displayName": "Gemini 2.0 Flash Search Experimental",
                                  "description": "Gemini 2.0 Flash Search Experimental", "inputTokenLimit": 32767,
                                  "outputTokenLimit": 8192,
                                  "supportedGenerationMethods": ["generateContent", "countTokens"], "temperature": 1,
                                  "topP": 0.95, "topK": 64, "maxTemperature": 2})
    return models_json


@router.post("/models/{model_name}:generateContent")
@router_v1beta.post("/models/{model_name}:generateContent")
@RetryHandler(max_retries=3, key_arg="api_key")
async def generate_content(
        model_name: str,
        request: GeminiRequest,
        _=Depends(security_service.verify_goog_api_key),
        api_key: str = Depends(get_next_working_key_wrapper),
        key_manager: KeyManager = Depends(get_key_manager)
):
    chat_service = GeminiChatService(settings.BASE_URL, key_manager)
    """非流式生成内容"""
    logger.info("-" * 50 + "gemini_generate_content" + "-" * 50)
    logger.info(f"Handling Gemini content generation request for model: {model_name}")
    logger.info(f"Request: \n{request.model_dump_json(indent=2)}")
    logger.info(f"Using API key: {api_key}")

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
@RetryHandler(max_retries=3, key_arg="api_key")
async def stream_generate_content(
        model_name: str,
        request: GeminiRequest,
        _=Depends(security_service.verify_goog_api_key),
        api_key: str = Depends(get_next_working_key_wrapper),
        key_manager: KeyManager = Depends(get_key_manager)
):
    chat_service = GeminiChatService(settings.BASE_URL, key_manager)
    """流式生成内容"""
    logger.info("-" * 50 + "gemini_stream_generate_content" + "-" * 50)
    logger.info(f"Handling Gemini streaming content generation for model: {model_name}")
    logger.info(f"Request: \n{request.model_dump_json(indent=2)}")
    logger.info(f"Using API key: {api_key}")

    try:
        response_stream = chat_service.stream_generate_content(
            model=model_name,
            request=request,
            api_key=api_key
        )
        return StreamingResponse(response_stream, media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Streaming request failed: {str(e)}")


@router.post("/verify-key/{api_key}")
async def verify_key(api_key: str):
    key_manager = await get_key_manager()
    chat_service = GeminiChatService(settings.BASE_URL, key_manager)
    """验证Gemini API密钥的有效性"""
    logger.info("-" * 50 + "verify_gemini_key" + "-" * 50)
    logger.info("Verifying API key validity")
    
    try:
        # 使用generate_content接口测试key的有效性
        gemini_requset = GeminiRequest(
            contents=[
                GeminiContent(
                    role="user",
                    parts=[{"text": "hi"}]
                )
            ]
        )
        response = await chat_service.generate_content(settings.TEST_MODEL,gemini_requset, api_key)
        if response:
            return JSONResponse({"status": "valid"})
        return JSONResponse({"status": "invalid"})
    except Exception as e:
        logger.error(f"Key verification failed: {str(e)}")
        return JSONResponse({"status": "invalid", "error": str(e)})
