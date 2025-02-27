# app/services/chat/message_converter.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

SUPPORTED_ROLES = ["user", "model", "system"]


class MessageConverter(ABC):
    """消息转换器基类"""

    @abstractmethod
    def convert(self, messages: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        pass


def _convert_image(image_url: str) -> Dict[str, Any]:
    if image_url.startswith("data:image"):
        return {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_url.split(",")[1]
            }
        }
    return {
        "image_url": {
            "url": image_url
        }
    }


class OpenAIMessageConverter(MessageConverter):
    """OpenAI消息格式转换器"""

    def convert(self, messages: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        converted_messages = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "")
            if role not in SUPPORTED_ROLES:
                role = "model"

            parts = []
            if isinstance(msg["content"], str) and msg["content"]:
                # 请求 gemini 接口时如果包含 content 字段但内容为空时会返回 400 错误，所以需要判断是否为空并移除
                parts.append({"text": msg["content"]})
            elif isinstance(msg["content"], list):
                for content in msg["content"]:
                    if isinstance(content, str) and content:
                        parts.append({"text": content})
                    elif isinstance(content, dict):
                        if content["type"] == "text" and content["text"]:
                            parts.append({"text": content["text"]})
                        elif content["type"] == "image_url":
                            parts.append(_convert_image(content["image_url"]["url"]))

            if parts:
                if role == "system":
                    system_instruction = {"role": "system", "parts": parts}
                else:
                    converted_messages.append({"role": role, "parts": parts})

        return converted_messages, system_instruction
