# -*- coding: utf-8 -*-
"""Browser plugin API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import logging

from ..channels.manager import ChannelManager
from .schemas_browser import BrowserMessageRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/browser", tags=["browser-plugin"])


def get_channel_manager(request: Request) -> ChannelManager:
    """Get channel manager from app state."""
    mgr = getattr(request.app.state, "channel_manager", None)
    if mgr is None:
        raise HTTPException(
            status_code=503,
            detail="Channel manager not initialized",
        )
    return mgr


@router.post("/message")
async def send_message(
    request: BrowserMessageRequest,
    req: Request,
    manager: ChannelManager = Depends(get_channel_manager),
):
    """Send message to browser-plugin channel and stream SSE response.

    This endpoint:
    1. Gets the browser-plugin channel
    2. Converts request to AgentRequest
    3. Enqueues to channel manager
    4. Streams SSE response

    Args:
        request: Browser message request
        req: FastAPI request object
        manager: Channel manager

    Returns:
        StreamingResponse with SSE events
    """
    ch = await manager.get_channel("browser-plugin")

    if not ch:
        raise HTTPException(
            status_code=404,
            detail="browser-plugin channel not enabled",
        )

    # Convert to native payload format
    native_payload = {
        "user_id": request.user_id,
        "content_parts": [cp.model_dump() for cp in request.content_parts],
        "meta": request.meta,
    }

    # Build AgentRequest
    agent_request = ch.build_agent_request_from_native(native_payload)

    # Create SSE stream
    async def event_generator():
        try:
            async for event in ch._process(agent_request):
                # Convert event to JSON
                event_dict = {}
                for attr in ["object", "status", "type", "data"]:
                    val = getattr(event, attr, None)
                    if val is not None:
                        if hasattr(val, "model_dump"):
                            event_dict[attr] = val.model_dump()
                        else:
                            event_dict[attr] = val
                yield f"data: {json.dumps(event_dict)}\n\n"
        except Exception as e:
            logger.exception("browser message processing failed")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/messages")
async def get_messages(
    session_id: Optional[str] = None,
    manager: ChannelManager = Depends(get_channel_manager),
):
    """Get pending messages (polling endpoint).

    Args:
        session_id: Optional session ID (defaults to global session)
        manager: Channel manager

    Returns:
        List of pending messages
    """
    from ..console_push_store import get_recent

    # Use global session if not specified
    if session_id is None:
        session_id = "browser-plugin:global"

    messages = await get_recent(session_id)
    return {"messages": messages, "session_id": session_id}
