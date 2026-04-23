from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


class ChatRequest(BaseModel):
    model: str = "gemini-auto"
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0


class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "gemini-imagen"
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = None
    quality: Optional[str] = "standard"
    style: Optional[str] = "natural"
