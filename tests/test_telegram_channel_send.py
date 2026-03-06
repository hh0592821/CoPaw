# -*- coding: utf-8 -*-
"""Quick test for Telegram channel send() method bug fix."""
from unittest.mock import MagicMock, AsyncMock
import asyncio


def test_send_with_message_thread_id():
    """Test that send() correctly handles message_thread_id from meta."""
    from copaw.app.channels.telegram.channel import TelegramChannel
    
    # Mock dependencies
    process = MagicMock()
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.bot = mock_bot
    
    channel = TelegramChannel(
        process=process,
        enabled=True,
        bot_token="test_token",
        http_proxy="",
        http_proxy_auth="",
        bot_prefix="",
    )
    channel._application = mock_app
    
    # Test with message_thread_id
    async def run_test():
        await channel.send(
            to_handle="test_chat_id",
            text="Hello",
            meta={"chat_id": "123", "message_thread_id": "456"}
        )
        
        # Verify bot.send_message was called with message_thread_id
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == "123"
        assert call_kwargs["message_thread_id"] == "456"
        assert call_kwargs["parse_mode"] == "HTML"
    
    asyncio.run(run_test())


def test_send_without_message_thread_id():
    """Test that send() works without message_thread_id."""
    from copaw.app.channels.telegram.channel import TelegramChannel
    
    process = MagicMock()
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.bot = mock_bot
    
    channel = TelegramChannel(
        process=process,
        enabled=True,
        bot_token="test_token",
        http_proxy="",
        http_proxy_auth="",
        bot_prefix="",
    )
    channel._application = mock_app
    
    async def run_test():
        await channel.send(
            to_handle="test_chat_id",
            text="Hello",
            meta={"chat_id": "123"}
        )
        
        # Verify bot.send_message was called without message_thread_id
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == "123"
        # Should NOT have message_thread_id in kwargs when it's None
        assert "message_thread_id" not in call_kwargs or call_kwargs.get("message_thread_id") is None
    
    asyncio.run(run_test())


if __name__ == "__main__":
    test_send_with_message_thread_id()
    test_send_without_message_thread_id()
    print("✅ All tests passed!")