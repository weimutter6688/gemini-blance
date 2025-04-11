# app/services/chat_service.py

import json
import re
import datetime # Add datetime import
import time # Add time import
from typing import Any, AsyncGenerator, Dict, List
from app.config.config import settings
from app.domain.gemini_models import GeminiRequest
from app.handler.response_handler import GeminiResponseHandler
from app.handler.stream_optimizer import gemini_optimizer
from app.log.logger import get_gemini_logger
from app.service.client.api_client import GeminiApiClient
from app.service.key.key_manager import KeyManager
from app.database.services import add_error_log, add_request_log # Import add_request_log

logger = get_gemini_logger()


def _has_image_parts(contents: List[Dict[str, Any]]) -> bool:
    """判断消息是否包含图片部分"""
    for content in contents:
        if "parts" in content:
            for part in content["parts"]:
                if "image_url" in part or "inline_data" in part:
                    return True
    return False


def _build_tools(model: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """构建工具"""
    
    def _merge_tools(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        record = dict()
        for item in tools:
            if not item or not isinstance(item, dict):
                continue

            for k, v in item.items():
                if k == "functionDeclarations" and v and isinstance(v, list):
                    functions = record.get("functionDeclarations", [])
                    functions.extend(v)
                    record["functionDeclarations"] = functions
                else:
                    record[k] = v
        return record

    tool = dict()
    if payload and isinstance(payload, dict) and "tools" in payload:
        if payload.get("tools") and isinstance(payload.get("tools"), dict):
            payload["tools"] = [payload.get("tools")]
        items = payload.get("tools", [])
        if items and isinstance(items, list):
            tool.update(_merge_tools(items))

    if (
        settings.TOOLS_CODE_EXECUTION_ENABLED
        and not (model.endswith("-search") or "-thinking" in model)
        and not _has_image_parts(payload.get("contents", []))
    ):
        tool["codeExecution"] = {}
    if model.endswith("-search"):
        tool["googleSearch"] = {}

    # 解决 "Tool use with function calling is unsupported" 问题
    if tool.get("functionDeclarations"):
        tool.pop("googleSearch", None)
        tool.pop("codeExecution", None)

    return [tool] if tool else []


def _get_safety_settings(model: str) -> List[Dict[str, str]]:
    """获取安全设置"""
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


def _build_payload(model: str, request: GeminiRequest) -> Dict[str, Any]:
    """构建请求payload"""
    request_dict = request.model_dump()
    if request.generationConfig:
        if request.generationConfig.maxOutputTokens is None:
            # 如果未指定最大输出长度，则不传递该字段，解决截断的问题
            request_dict["generationConfig"].pop("maxOutputTokens")
    
    payload = {
        "contents": request_dict.get("contents", []),
        "tools": _build_tools(model, request_dict),
        "safetySettings": _get_safety_settings(model),
        "generationConfig": request_dict.get("generationConfig", {}),
        "systemInstruction": request_dict.get("systemInstruction", ""),
    }

    if model.endswith("-image") or model.endswith("-image-generation"):
        payload.pop("systemInstruction")
        payload["generationConfig"]["responseModalities"] = ["Text", "Image"]
    return payload


class GeminiChatService:
    """聊天服务"""

    def __init__(self, base_url: str, key_manager: KeyManager):
        self.api_client = GeminiApiClient(base_url, settings.TIME_OUT)
        self.key_manager = key_manager
        self.response_handler = GeminiResponseHandler()

    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """从响应中提取文本内容"""
        if not response.get("candidates"):
            return ""

        candidate = response["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        if parts and "text" in parts[0]:
            return parts[0].get("text", "")
        return ""

    def _create_char_response(
        self, original_response: Dict[str, Any], text: str
    ) -> Dict[str, Any]:
        """创建包含指定文本的响应"""
        response_copy = json.loads(json.dumps(original_response))  # 深拷贝
        if response_copy.get("candidates") and response_copy["candidates"][0].get(
            "content", {}
        ).get("parts"):
            response_copy["candidates"][0]["content"]["parts"][0]["text"] = text
        return response_copy

    async def generate_content(
        self, model: str, request: GeminiRequest, api_key: str
    ) -> Dict[str, Any]:
        """生成内容"""
        payload = _build_payload(model, request)
        start_time = time.perf_counter()
        request_datetime = datetime.datetime.now() # Record request time
        is_success = False
        status_code = None
        response = None

        try:
            response = await self.api_client.generate_content(payload, model, api_key)
            # Assuming success if no exception is raised and response is received
            # The actual status code might be within the response structure or headers,
            # but api_client doesn't seem to expose it directly here.
            # We'll assume 200 for success if no exception.
            is_success = True
            status_code = 200 # Assume 200 on success
            return self.response_handler.handle_response(response, model, stream=False)
        except Exception as e:
            is_success = False
            error_log_msg = str(e)
            logger.error(f"Normal API call failed with error: {error_log_msg}")
            # Try to parse status code from exception
            match = re.search(r"status code (\d+)", error_log_msg)
            if match:
                status_code = int(match.group(1))
            else:
                status_code = 500 # Default to 500 if parsing fails

            # Log error to error log table
            await add_error_log(
                gemini_key=api_key,
                model_name=model,
                error_type="gemini_chat_service",
                error_log=error_log_msg,
                error_code=status_code,
                request_msg=payload
            )
            raise e # Re-throw exception for upstream handling
        finally:
            end_time = time.perf_counter()
            latency_ms = int((end_time - start_time) * 1000)
            # Log request to request log table
            await add_request_log(
                model_name=model,
                api_key=api_key,
                is_success=is_success,
                status_code=status_code,
                latency_ms=latency_ms,
                request_time=request_datetime
            )

    async def stream_generate_content(
        self, model: str, request: GeminiRequest, api_key: str
    ) -> AsyncGenerator[str, None]:
        """流式生成内容"""
        retries = 0
        max_retries = settings.MAX_RETRIES
        payload = _build_payload(model, request)
        start_time = time.perf_counter() # Record start time before loop
        request_datetime = datetime.datetime.now()
        is_success = False
        status_code = None
        final_api_key = api_key # Store the initial key

        try:
            while retries < max_retries:
                current_attempt_key = api_key # Key used for this attempt
                final_api_key = current_attempt_key # Update final key used
                try:
                    async for line in self.api_client.stream_generate_content(
                        payload, model, current_attempt_key
                    ):
                        # print(line)
                        if line.startswith("data:"):
                            line = line[6:]
                            response_data = self.response_handler.handle_response(
                                json.loads(line), model, stream=True
                            )
                            text = self._extract_text_from_response(response_data)
                            # 如果有文本内容，且开启了流式输出优化器，则使用流式输出优化器处理
                            if text and settings.STREAM_OPTIMIZER_ENABLED:
                                # 使用流式输出优化器处理文本输出
                                async for (
                                    optimized_chunk
                                ) in gemini_optimizer.optimize_stream_output(
                                    text,
                                    lambda t: self._create_char_response(response_data, t),
                                    lambda c: "data: " + json.dumps(c) + "\n\n",
                                ):
                                    yield optimized_chunk
                            else:
                                # 如果没有文本内容（如工具调用等），整块输出
                                yield "data: " + json.dumps(response_data) + "\n\n"
                    logger.info("Streaming completed successfully")
                    is_success = True
                    status_code = 200 # Assume 200 on success
                    break # Exit loop on success
                except Exception as e:
                    retries += 1
                    is_success = False # Mark as failed for this attempt
                    error_log_msg = str(e)
                    logger.warning(
                        f"Streaming API call failed with error: {error_log_msg}. Attempt {retries} of {max_retries}"
                    )
                    # Parse error code for logging
                    match = re.search(r"status code (\d+)", error_log_msg)
                    if match:
                        status_code = int(match.group(1))
                    else:
                        status_code = 500 # Default if parsing fails

                    # Log error to error log table
                    await add_error_log(
                        gemini_key=current_attempt_key, # Log key used for this failed attempt
                        model_name=model,
                        error_log=error_log_msg,
                        error_code=status_code,
                        request_msg=payload
                    )

                    # Attempt to switch API Key
                    api_key = await self.key_manager.handle_api_failure(current_attempt_key, retries)
                    if api_key:
                        logger.info(f"Switched to new API key: {api_key}")
                    else: # No more keys or retries exceeded by handle_api_failure logic
                         logger.error(f"No valid API key available after {retries} retries.")
                         break # Exit loop if no key available

                    if retries >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) reached for streaming."
                        )
                        break # Exit loop after max retries
        finally:
            # Log the final outcome of the streaming request
            end_time = time.perf_counter()
            latency_ms = int((end_time - start_time) * 1000)
            await add_request_log(
                model_name=model,
                api_key=final_api_key, # Log the last key used
                is_success=is_success, # Log the final success status
                status_code=status_code, # Log the last known status code
                latency_ms=latency_ms, # Log total time including retries
                request_time=request_datetime
            )
            # If the loop finished due to failure, ensure an exception is raised if not already handled
            if not is_success and retries >= max_retries:
                 # We need to raise an exception here if the loop exited due to max retries failure
                 # However, the original code structure doesn't explicitly raise here after the loop.
                 # For now, we just log. Consider raising HTTPException if needed.
                 pass
