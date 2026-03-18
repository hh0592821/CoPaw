# -*- coding: utf-8 -*-
"""Browser plugin schema definitions."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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
