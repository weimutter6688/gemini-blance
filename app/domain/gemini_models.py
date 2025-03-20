from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel


class SafetySetting(BaseModel):
    category: Optional[Literal["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_CIVIC_INTEGRITY"]] = None
    threshold: Optional[Literal["HARM_BLOCK_THRESHOLD_UNSPECIFIED", "BLOCK_LOW_AND_ABOVE", "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_ONLY_HIGH", "BLOCK_NONE", "OFF"]] = None


class GenerationConfig(BaseModel):
    stopSequences: Optional[List[str]] = None
    responseMimeType: Optional[str] = None
    responseSchema: Optional[Dict[str, Any]] = None
    candidateCount: Optional[int] = 1
    maxOutputTokens: Optional[int] = None
    temperature: Optional[float] = None
    topP: Optional[float] = None
    topK: Optional[int] = None
    presencePenalty: Optional[float] = None
    frequencyPenalty: Optional[float] = None
    responseLogprobs: Optional[bool] = None
    logprobs: Optional[int] = None


class SystemInstruction(BaseModel):
    role: str = "system"
    parts: List[Dict[str, Any]]


class GeminiContent(BaseModel):
    role: str
    parts: List[Dict[str, Any]]


class GeminiRequest(BaseModel):
    contents: List[GeminiContent] = []
    tools: Optional[List[Dict[str, Any]]] = []
    safetySettings: Optional[List[SafetySetting]] = None
    generationConfig: Optional[GenerationConfig] = None
    systemInstruction: Optional[SystemInstruction] = None
