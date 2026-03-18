# -*- coding: utf-8 -*-
"""Browser Plugin Channel."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..base import (
    BaseChannel,
    ContentType,
    OnReplySent,
    OutgoingContentPart,
    ProcessHandler,
    TextContent,
)
from ....config.config import BrowserPluginConfig

logger = logging.getLogger(__name__)


class BrowserChannel(BaseChannel):
    """Browser Plugin Channel for web extension integration.

    This channel enables browser extensions to communicate with CoPaw
    via HTTP + Server-Sent Events (SSE).

    Session Strategy:
    - Global shared session: All browser users share one conversation context
    - session_id: "browser-plugin:global"
    - user_id: "browser-user"
    """

    channel = "browser_plugin"
    uses_manager_queue = True

    # Global shared session identifiers
    GLOBAL_SESSION_ID = "browser-plugin:global"
    GLOBAL_USER_ID = "browser-user"

    def __init__(
        self,
        process: ProcessHandler,
        enabled: bool = True,
        cors_origins: Optional[List[str]] = None,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ):
        """Initialize BrowserChannel.

        Args:
            process: Handler for agent requests (runner.stream_query)
            enabled: Whether this channel is active
            cors_origins: Allowed CORS origins for browser extensions
            on_reply_sent: Callback when reply is sent
            show_tool_details: Whether to show tool execution details
            filter_tool_messages: Whether to filter out tool messages
            filter_thinking: Whether to filter thinking/reasoning blocks
        """
        super().__init__(
            process,
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
        )
        self.enabled = enabled
        self.cors_origins = cors_origins or []

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ) -> "BrowserChannel":
        """Create from environment variables."""
        import os

        enabled = os.getenv("BROWSER_CHANNEL_ENABLED", "1") == "1"
        cors_raw = os.getenv(
            "BROWSER_CORS_ORIGINS",
            "chrome-extension://*,moz-extension://*",
        )
        cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

        return cls(
            process=process,
            enabled=enabled,
            cors_origins=cors_origins,
            on_reply_sent=on_reply_sent,
        )

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: BrowserPluginConfig,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ) -> "BrowserChannel":
        """Create from config (config.json).

        Args:
            process: Handler for agent requests
            config: Browser plugin configuration
            on_reply_sent: Callback when reply is sent
            show_tool_details: Whether to show tool execution details
            filter_tool_messages: Whether to filter out tool messages
            filter_thinking: Whether to filter thinking/reasoning blocks

        Returns:
            Configured BrowserChannel instance
        """
        cors_origins = getattr(config, "cors_origins", [])

        return cls(
            process=process,
            enabled=config.enabled,
            cors_origins=cors_origins,
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
        )

    def build_agent_request_from_native(self, native_payload: Any) -> Any:
        """Convert browser plugin payload to AgentRequest.

        Args:
            native_payload: Dict with user_id, content_parts, meta

        Returns:
            AgentRequest object
        """
        payload = native_payload if isinstance(native_payload, dict) else {}

        channel_id = self.channel
        sender_id = payload.get("user_id", self.GLOBAL_USER_ID)
        content_parts = payload.get("content_parts", [])
        meta = payload.get("meta", {})

        # Use global shared session
        session_id = self.resolve_session_id(sender_id, meta)

        request = self.build_agent_request_from_user_content(
            channel_id=channel_id,
            sender_id=sender_id,
            session_id=session_id,
            content_parts=content_parts,
            channel_meta=meta,
        )

        # Attach metadata for send path
        request.channel_meta = meta
        return request

    def resolve_session_id(
        self,
        sender_id: str,
        channel_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Resolve to global shared session ID.

        Args:
            sender_id: User identifier (not used for global session)
            channel_meta: Optional metadata

        Returns:
            Global session ID
        """
        # Override to always use global session
        return self.GLOBAL_SESSION_ID

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send text message to browser plugin.

        Messages are pushed to the console_push_store for polling by
        the browser extension.

        Args:
            to_handle: Target handle (not used for browser plugin)
            text: Message text
            meta: Optional metadata including session_id
        """
        if not self.enabled:
            return

        from ..console_push_store import append as push_store_append

        session_id = (meta or {}).get(
            "session_id",
            self.GLOBAL_SESSION_ID,
        )

        if text.strip():
            await push_store_append(session_id, text.strip())
            logger.debug(f"browser channel: pushed message to session={session_id}")

    async def send_content_parts(
        self,
        to_handle: str,
        parts: List[OutgoingContentPart],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send content parts to browser plugin.

        Args:
            to_handle: Target handle
            parts: List of content parts
            meta: Optional metadata
        """
        if not self.enabled:
            return

        # Merge text parts
        text_parts = []
        for p in parts:
            t = getattr(p, "type", None)
            if t == ContentType.TEXT and getattr(p, "text", None):
                text_parts.append(p.text or "")
            elif t == ContentType.REFUSAL and getattr(p, "refusal", None):
                text_parts.append(p.refusal or "")

        body = "\n".join(text_parts) if text_parts else ""

        if body.strip():
            await self.send(to_handle, body, meta)

    async def start(self) -> None:
        """Start the browser channel."""
        if not self.enabled:
            logger.debug("browser channel disabled")
            return
        logger.info("Browser channel started")

    async def stop(self) -> None:
        """Stop the browser channel."""
        if not self.enabled:
            return
        logger.info("Browser channel stopped")
