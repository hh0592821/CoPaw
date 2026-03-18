# -*- coding: utf-8 -*-
"""Browser plugin API request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class BrowserMessageContent(BaseModel):
    """Message content for browser plugin."""

    type: str = "text"
    text: str
    metadata: Optional[Dict[str, Any]] = None


class BrowserMessageRequest(BaseModel):
    """Request schema for browser plugin messages."""

    user_id: str = Field(default="browser-user")
    content_parts: List[BrowserMessageContent]
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class BrowserMessageResponse(BaseModel):
    """Response schema for browser plugin message polling."""

    messages: List[str]
    session_id: str = Field(default="browser-plugin:global")
