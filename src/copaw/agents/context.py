# -*- coding: utf-8 -*-
"""Async context variables for the agent request lifecycle.

These ``ContextVar`` values are set by the runner before dispatching each
agent call, and can be read by tool functions that need request-scoped
information (e.g. the current channel) without requiring it to be threaded
through every call signature.
"""
from contextvars import ContextVar
from typing import Optional

#: The channel name for the current agent request (e.g. ``"telegram"``).
#: Set by the runner; ``None`` when running outside a channel context.
current_channel: ContextVar[Optional[str]] = ContextVar(
    "current_channel",
    default=None,
)
