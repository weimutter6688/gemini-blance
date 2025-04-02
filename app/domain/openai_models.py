from pydantic import BaseModel
from typing import List, Optional, Union

from app.core.constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_TOP_K, DEFAULT_TOP_P


class ChatRequest(BaseModel):
    messages: List[dict]
    model: str = DEFAULT_MODEL
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    stream: Optional[bool] = False
    tools: Optional[List[dict]] = []
    max_tokens: Optional[int] = None
    top_p: Optional[float] = DEFAULT_TOP_P
    top_k: Optional[int] = DEFAULT_TOP_K
    stop: Optional[List[str]] = []


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "text-embedding-004"
    encoding_format: Optional[str] = "float"


class ImageGenerationRequest(BaseModel):
    model: str = "DALL-E-3"
    prompt: str = ""
    n: int = 1
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = ""
    style: Optional[str] = ""
    response_format: Optional[str] = "url"
