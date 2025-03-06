# app/services/chat_service.py

from copy import deepcopy
import json
from typing import Dict, Any, AsyncGenerator, List, Optional, Union
from app.core.logger import get_openai_logger
from app.services.chat.message_converter import OpenAIMessageConverter
from app.services.chat.response_handler import OpenAIResponseHandler
from app.services.chat.api_client import GeminiApiClient
from app.services.chat.stream_optimizer import openai_optimizer
from app.schemas.openai_models import ChatRequest, ImageGenerationRequest
from app.core.config import settings
from app.services.image_create_service import ImageCreateService
from app.services.key_manager import KeyManager

logger = get_openai_logger()


def _has_image_parts(contents: List[Dict[str, Any]]) -> bool:
    """判断消息是否包含图片部分"""
    for content in contents:
        if "parts" in content:
            for part in content["parts"]:
                if "image_url" in part or "inline_data" in part:
                    return True
    return False


def _build_tools(
        request: ChatRequest, messages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """构建工具"""
    tools = []
    model = request.model

    if (
            settings.TOOLS_CODE_EXECUTION_ENABLED
            and not (model.endswith("-search") or "-thinking" in model)
            and not _has_image_parts(messages)
    ):
        tools.append({"code_execution": {}})
    if model.endswith("-search"):
        tools.append({"googleSearch": {}})

    # 将 request 中的 tools 合并到 tools 中
    if request.tools:
        function_declarations = []
        for tool in request.tools:
            if not tool or not isinstance(tool, dict):
                continue

            if tool.get("type", "") == "function" and tool.get("function"):
                function = deepcopy(tool.get("function"))
                parameters = function.get("parameters", {})
                if parameters.get("type") == "object" and not parameters.get("properties", {}):
                    function.pop("parameters", None)

                function_declarations.append(function)

        if function_declarations:
            # 按照 function 的 name 去重
            names, functions = set(), []
            for item in function_declarations:
                if item.get("name") not in names:
                    names.add(item.get("name"))
                    functions.append(item)

            tools.append({"functionDeclarations": functions})
            
    return tools


def _get_safety_settings(model: str) -> List[Dict[str, str]]:
    """获取安全设置"""
    # if (
    #     "2.0" in model
    #     and "gemini-2.0-flash-thinking-exp" not in model
    #     and "gemini-2.0-pro-exp" not in model
    # ):
    if model == "gemini-2.0-flash-exp":
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "OFF"},
        ]
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
    ]


def _build_payload(
    request: ChatRequest, messages: List[Dict[str, Any]], instruction: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """构建请求payload"""
    payload = {
        "contents": messages,
        "generationConfig": {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
            "stopSequences": request.stop,
            "topP": request.top_p,
            "topK": request.top_k,
        },
        "tools": _build_tools(request, messages),
        "safetySettings": _get_safety_settings(request.model),
    }

    if (
        instruction
        and isinstance(instruction, dict)
        and instruction.get("role") == "system"
        and instruction.get("parts")
    ):
        payload["systemInstruction"] = instruction

    return payload


class OpenAIChatService:
    """聊天服务"""
    def __init__(self, base_url: str, key_manager: KeyManager = None):
        self.message_converter = OpenAIMessageConverter()
        self.response_handler = OpenAIResponseHandler(config=None)
        self.api_client = GeminiApiClient(base_url)
        self.key_manager = key_manager
        self.image_create_service = ImageCreateService()
        
    def _extract_text_from_openai_chunk(self, chunk: Dict[str, Any]) -> str:
        """从OpenAI响应块中提取文本内容"""
        if not chunk.get("choices"):
            return ""
            
        choice = chunk["choices"][0]
        if "delta" in choice and "content" in choice["delta"]:
            return choice["delta"]["content"]
        return ""
        
    def _create_char_openai_chunk(self, original_chunk: Dict[str, Any], text: str) -> Dict[str, Any]:
        """创建包含指定文本的OpenAI响应块"""
        chunk_copy = json.loads(json.dumps(original_chunk))  # 深拷贝
        if chunk_copy.get("choices") and "delta" in chunk_copy["choices"][0]:
            chunk_copy["choices"][0]["delta"]["content"] = text
        return chunk_copy

    async def create_chat_completion(
            self,
            request: ChatRequest,
            api_key: str,
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """创建聊天完成"""
        # 转换消息格式
        messages, instruction = self.message_converter.convert(request.messages)

        # 构建请求payload
        payload = _build_payload(request, messages, instruction)

        if request.stream:
            return self._handle_stream_completion(request.model, payload, api_key)
        return await self._handle_normal_completion(request.model, payload, api_key)

    async def _handle_normal_completion(
            self, model: str, payload: Dict[str, Any], api_key: str
    ) -> Dict[str, Any]:
        """处理普通聊天完成"""
        response = await self.api_client.generate_content(payload, model, api_key)
        return self.response_handler.handle_response(
            response, model, stream=False, finish_reason="stop"
        )

    async def _handle_stream_completion(
            self, model: str, payload: Dict[str, Any], api_key: str
    ) -> AsyncGenerator[str, None]:
        """处理流式聊天完成，添加重试逻辑"""
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                async for line in self.api_client.stream_generate_content(
                        payload, model, api_key
                ):
                    # print(line)
                    if line.startswith("data:"):
                        chunk = json.loads(line[6:])
                        openai_chunk = self.response_handler.handle_response(
                            chunk, model, stream=True, finish_reason=None
                        )
                        if openai_chunk:
                            # 提取文本内容
                            text = self._extract_text_from_openai_chunk(openai_chunk)
                            if text:
                                # 使用流式输出优化器处理文本输出
                                async for optimized_chunk in openai_optimizer.optimize_stream_output(
                                    text,
                                    lambda t: self._create_char_openai_chunk(openai_chunk, t),
                                    lambda c: f"data: {json.dumps(c)}\n\n"
                                ):
                                    yield optimized_chunk
                            else:
                                # 如果没有文本内容（如工具调用等），整块输出
                                yield f"data: {json.dumps(openai_chunk)}\n\n"
                yield f"data: {json.dumps(self.response_handler.handle_response({}, model, stream=True, finish_reason='stop'))}\n\n"
                yield "data: [DONE]\n\n"
                logger.info("Streaming completed successfully")
                break  # 成功后退出循环
            except Exception as e:
                retries += 1
                logger.warning(
                    f"Streaming API call failed with error: {str(e)}. Attempt {retries} of {max_retries}"
                )
                api_key = await self.key_manager.handle_api_failure(api_key)
                logger.info(f"Switched to new API key: {api_key}")
                if retries >= max_retries:
                    logger.error(
                        f"Max retries ({max_retries}) reached for streaming. Raising error"
                    )
                    yield f"data: {json.dumps({'error': 'Streaming failed after retries'})}\n\n"
                    yield "data: [DONE]\n\n"
                    break

    async def create_image_chat_completion(
            self,
            request: ChatRequest,
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        
        image_generate_request = ImageGenerationRequest()
        image_generate_request.prompt = request.messages[-1]["content"]
        image_res = self.image_create_service.generate_images_chat(image_generate_request)
        
        if request.stream:
            return self._handle_stream_image_completion(request.model,image_res)
        else:
            return self._handle_normal_image_completion(request.model,image_res)
        
    async def _handle_stream_image_completion(
            self, model: str, image_data: str
    ) -> AsyncGenerator[str, None]:
        if image_data:
            openai_chunk = self.response_handler.handle_image_chat_response(
                image_data, model, stream=True, finish_reason=None
            )
            if openai_chunk:
                # 提取文本内容
                text = self._extract_text_from_openai_chunk(openai_chunk)
                if text:
                    # 使用流式输出优化器处理文本输出
                    async for optimized_chunk in openai_optimizer.optimize_stream_output(
                        text,
                        lambda t: self._create_char_openai_chunk(openai_chunk, t),
                        lambda c: f"data: {json.dumps(c)}\n\n"
                    ):
                        yield optimized_chunk
                else:
                    # 如果没有文本内容（如图片URL等），整块输出
                    yield f"data: {json.dumps(openai_chunk)}\n\n"
        yield f"data: {json.dumps(self.response_handler.handle_response({}, model, stream=True, finish_reason='stop'))}\n\n"
        yield "data: [DONE]\n\n"
        logger.info("Image chat streaming completed successfully")
    
    def _handle_normal_image_completion(
            self, model: str, image_data: str
    ) -> Dict[str, Any]:
        
        return self.response_handler.handle_image_chat_response(
            image_data, model, stream=False, finish_reason="stop"
        )
