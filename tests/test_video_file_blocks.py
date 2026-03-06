# -*- coding: utf-8 -*-
"""Test video and file block handling in agentscope_msg_to_message."""

from copaw.app.runner.utils import agentscope_msg_to_message


class TestVideoAndFileBlocks:
    """Test video and file block conversion."""

    def test_video_block_url_source(self):
        """Test video block with URL source."""
        msg = {
            "id": "test-1",
            "name": "test",
            "role": "assistant",
            "content": [
                {
                    "type": "video",
                    "source": {
                        "type": "url",
                        "url": "file:///tmp/test.mp4",
                    },
                },
            ],
        }

        results = agentscope_msg_to_message(msg)

        assert len(results) == 1
        assert results[0]["type"] == "message"
        assert len(results[0]["content"]) == 1
        assert results[0]["content"][0]["type"] == "video"
        assert results[0]["content"][0]["video_url"] == "file:///tmp/test.mp4"

    def test_video_block_base64_source(self):
        """Test video block with base64 source."""
        msg = {
            "id": "test-2",
            "name": "test",
            "role": "assistant",
            "content": [
                {
                    "type": "video",
                    "source": {
                        "type": "base64",
                        "media_type": "video/mp4",
                        "data": "AAAAIGZ0eXBpc29tAAACAGlzb21pc28y...",
                    },
                },
            ],
        }

        results = agentscope_msg_to_message(msg)

        assert len(results) == 1
        assert results[0]["type"] == "message"
        assert len(results[0]["content"]) == 1
        assert results[0]["content"][0]["type"] == "video"
        assert results[0]["content"][0]["video_url"].startswith(
            "data:video/mp4;base64,",
        )

    def test_file_block_url_source(self):
        """Test file block with URL source."""
        msg = {
            "id": "test-3",
            "name": "test",
            "role": "assistant",
            "content": [
                {
                    "type": "file",
                    "source": {
                        "type": "url",
                        "url": "file:///tmp/document.pdf",
                    },
                    "filename": "document.pdf",
                },
            ],
        }

        results = agentscope_msg_to_message(msg)

        assert len(results) == 1
        assert results[0]["type"] == "message"
        assert len(results[0]["content"]) == 1
        assert results[0]["content"][0]["type"] == "file"
        assert (
            results[0]["content"][0]["file_url"] == "file:///tmp/document.pdf"
        )
        assert results[0]["content"][0]["filename"] == "document.pdf"

    def test_file_block_base64_source(self):
        """Test file block with base64 source."""
        msg = {
            "id": "test-4",
            "name": "test",
            "role": "assistant",
            "content": [
                {
                    "type": "file",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": "JVBERi0xLjQK...",
                    },
                    "filename": "report.pdf",
                },
            ],
        }

        results = agentscope_msg_to_message(msg)

        assert len(results) == 1
        assert results[0]["type"] == "message"
        assert len(results[0]["content"]) == 1
        assert results[0]["content"][0]["type"] == "file"
        assert results[0]["content"][0]["file_url"].startswith(
            "data:application/pdf;base64,",
        )
        assert results[0]["content"][0]["filename"] == "report.pdf"

    def test_file_block_without_filename(self):
        """Test file block without filename."""
        msg = {
            "id": "test-5",
            "name": "test",
            "role": "assistant",
            "content": [
                {
                    "type": "file",
                    "source": {
                        "type": "url",
                        "url": "file:///tmp/data.bin",
                    },
                },
            ],
        }

        results = agentscope_msg_to_message(msg)

        assert len(results) == 1
        assert results[0]["type"] == "message"
        assert len(results[0]["content"]) == 1
        assert results[0]["content"][0]["type"] == "file"
        assert results[0]["content"][0]["file_url"] == "file:///tmp/data.bin"

    def test_mixed_blocks(self):
        """Test message with mixed block types."""
        msg = {
            "id": "test-6",
            "name": "test",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Here is the video:"},
                {
                    "type": "video",
                    "source": {
                        "type": "url",
                        "url": "file:///tmp/video.mp4",
                    },
                },
                {"type": "text", "text": "And the document:"},
                {
                    "type": "file",
                    "source": {
                        "type": "url",
                        "url": "file:///tmp/doc.pdf",
                    },
                    "filename": "doc.pdf",
                },
            ],
        }

        results = agentscope_msg_to_message(msg)

        assert len(results) == 1
        assert results[0]["type"] == "message"
        assert len(results[0]["content"]) == 4

        # Check text blocks
        assert results[0]["content"][0]["type"] == "text"
        assert results[0]["content"][0]["text"] == "Here is the video:"

        # Check video block
        assert results[0]["content"][1]["type"] == "video"
        assert results[0]["content"][1]["video_url"] == "file:///tmp/video.mp4"

        # Check text block
        assert results[0]["content"][2]["type"] == "text"
        assert results[0]["content"][2]["text"] == "And the document:"

        # Check file block
        assert results[0]["content"][3]["type"] == "file"
        assert results[0]["content"][3]["file_url"] == "file:///tmp/doc.pdf"
        assert results[0]["content"][3]["filename"] == "doc.pdf"
