from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.config.config import settings
from app.core.security import SecurityService
from app.domain.openai_models import (
    ChatRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
)
from app.handler.retry_handler import RetryHandler
from app.log.logger import get_openai_logger
from app.service.chat.openai_chat_service import OpenAIChatService
from app.service.embedding.embedding_service import EmbeddingService
from app.service.image.image_create_service import ImageCreateService
from app.service.key.key_manager import KeyManager, get_key_manager_instance
from app.service.model.model_service import ModelService

router = APIRouter()
logger = get_openai_logger()

# 初始化服务
security_service = SecurityService(settings.ALLOWED_TOKENS, settings.AUTH_TOKEN)
model_service = ModelService(settings.SEARCH_MODELS, settings.IMAGE_MODELS)
embedding_service = EmbeddingService(settings.BASE_URL)
image_create_service = ImageCreateService()


async def get_key_manager():
    return await get_key_manager_instance()


async def get_next_working_key_wrapper(
    key_manager: KeyManager = Depends(get_key_manager),
):
    return await key_manager.get_next_working_key()


@router.get("/v1/models")
@router.get("/hf/v1/models")
async def list_models(
    _=Depends(security_service.verify_authorization),
    key_manager: KeyManager = Depends(get_key_manager),
):
    logger.info("-" * 50 + "list_models" + "-" * 50)
    logger.info("Handling models list request")
    api_key = await key_manager.get_next_working_key()
    logger.info(f"Using API key: {api_key}")
    try:
        return model_service.get_gemini_openai_models(api_key)
    except Exception as e:
        logger.error(f"Error getting models list: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching models list"
        ) from e


@router.post("/v1/chat/completions")
@router.post("/hf/v1/chat/completions")
@RetryHandler(max_retries=3, key_arg="api_key")
async def chat_completion(
    request: ChatRequest,
    _=Depends(security_service.verify_authorization),
    api_key: str = Depends(get_next_working_key_wrapper),
    key_manager: KeyManager = Depends(get_key_manager),
):
    # 如果model是imagen3,使用paid_key
    if request.model == f"{settings.CREATE_IMAGE_MODEL}-chat":
        api_key = await key_manager.get_paid_key()
    chat_service = OpenAIChatService(settings.BASE_URL, key_manager)
    logger.info("-" * 50 + "chat_completion" + "-" * 50)
    logger.info(f"Handling chat completion request for model: {request.model}")
    logger.info(f"Request: \n{request.model_dump_json(indent=2)}")
    logger.info(f"Using API key: {api_key}")

    if not model_service.check_model_support(request.model):
        raise HTTPException(
            status_code=400, detail=f"Model {request.model} is not supported"
        )

    try:
        # 如果model是imagen3,使用paid_key
        if request.model == f"{settings.CREATE_IMAGE_MODEL}-chat":
            response = await chat_service.create_image_chat_completion(request=request)
        else:
            response = await chat_service.create_chat_completion(request, api_key)
        # 处理流式响应
        if request.stream:
            return StreamingResponse(response, media_type="text/event-stream")
        logger.info("Chat completion request successful")
        return response
    except Exception as e:
        logger.error(f"Chat completion failed after retries: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat completion failed") from e


@router.post("/v1/images/generations")
@router.post("/hf/v1/images/generations")
async def generate_image(
    request: ImageGenerationRequest,
    _=Depends(security_service.verify_authorization),
):
    logger.info("-" * 50 + "generate_image" + "-" * 50)
    logger.info(f"Handling image generation request for prompt: {request.prompt}")

    try:
        response = image_create_service.generate_images(request)
        logger.info("Image generation request successful")
        return response
    except Exception as e:
        logger.error(f"Image generation request failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Image generation request failed"
        ) from e


@router.post("/v1/embeddings")
@router.post("/hf/v1/embeddings")
async def embedding(
    request: EmbeddingRequest,
    _=Depends(security_service.verify_authorization),
    key_manager: KeyManager = Depends(get_key_manager),
):
    logger.info("-" * 50 + "embedding" + "-" * 50)
    logger.info(f"Handling embedding request for model: {request.model}")
    api_key = await key_manager.get_next_working_key()
    logger.info(f"Using API key: {api_key}")
    try:
        response = await embedding_service.create_embedding(
            input_text=request.input, model=request.model, api_key=api_key
        )
        logger.info("Embedding request successful")
        return response
    except Exception as e:
        logger.error(f"Embedding request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Embedding request failed") from e


@router.get("/v1/keys/list")
@router.get("/hf/v1/keys/list")
async def get_keys_list(
    _=Depends(security_service.verify_auth_token),
    key_manager: KeyManager = Depends(get_key_manager),
):
    """获取有效和无效的API key列表"""
    logger.info("-" * 50 + "get_keys_list" + "-" * 50)
    logger.info("Handling keys list request")
    try:
        keys_status = await key_manager.get_keys_by_status()
        return {
            "status": "success",
            "data": {
                "valid_keys": keys_status["valid_keys"],
                "invalid_keys": keys_status["invalid_keys"],
            },
            "total": len(keys_status["valid_keys"]) + len(keys_status["invalid_keys"]),
        }
    except Exception as e:
        logger.error(f"Error getting keys list: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching keys list"
        ) from e
