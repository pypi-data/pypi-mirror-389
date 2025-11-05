"""
Unit tests for WebSocketRunner class
"""

import pytest
from unittest.mock import AsyncMock

from starlette.websockets import WebSocketDisconnect

from transcriber.message_handler import (
    BytesMessageHandler,
    TextMessageHandler,
    MessageHandlerExecutor,
    WebSocketRunner,
)


class TestWebSocketRunner:
    """Test WebSocketRunner class"""

    def test_websocket_runner_initialization(self):
        """Test that WebSocketRunner can be initialized with a MessageHandlerExecutor"""
        executor = MessageHandlerExecutor()
        runner = WebSocketRunner(executor)
        
        assert runner.get_executor() == executor

    def test_websocket_runner_initialization_wrong_type(self):
        """Test that initializing with wrong type raises TypeError"""
        with pytest.raises(TypeError, match="Expected MessageHandlerExecutor"):
            WebSocketRunner("not an executor")  # type: ignore

    def test_get_executor(self):
        """Test that get_executor returns the correct executor"""
        executor = MessageHandlerExecutor()
        runner = WebSocketRunner(executor)
        
        assert runner.get_executor() == executor
        assert isinstance(runner.get_executor(), MessageHandlerExecutor)

    @pytest.mark.asyncio
    async def test_run_processes_bytes_messages(self):
        """Test that run processes bytes messages correctly"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class TestHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data)

        executor.register_bytes_handler(TestHandler())
        runner = WebSocketRunner(executor)
        
        # Create a mock websocket that returns bytes messages then disconnects
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"bytes": b"test data"},
            WebSocketDisconnect(),
        ]
        
        await runner.run(websocket)
        
        assert len(handled_data) == 1
        assert handled_data[0] == b"test data"

    @pytest.mark.asyncio
    async def test_run_processes_text_messages(self):
        """Test that run processes text messages correctly"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        executor.register_text_handler(TestHandler())
        runner = WebSocketRunner(executor)
        
        # Create a mock websocket that returns text messages then disconnects
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"text": "test message"},
            WebSocketDisconnect(),
        ]
        
        await runner.run(websocket)
        
        assert len(handled_data) == 1
        assert handled_data[0] == "test message"

    @pytest.mark.asyncio
    async def test_run_handles_multiple_messages(self):
        """Test that run processes multiple messages correctly"""
        executor = MessageHandlerExecutor()
        bytes_data = []
        text_data = []

        class BytesHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                bytes_data.append(data)

        class TextHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                text_data.append(data)

        executor.register_bytes_handler(BytesHandler())
        executor.register_text_handler(TextHandler())
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"bytes": b"data1"},
            {"text": "message1"},
            {"bytes": b"data2"},
            {"text": "message2"},
            WebSocketDisconnect(),
        ]
        
        await runner.run(websocket)
        
        assert len(bytes_data) == 2
        assert len(text_data) == 2
        assert bytes_data == [b"data1", b"data2"]
        assert text_data == ["message1", "message2"]

    @pytest.mark.asyncio
    async def test_run_skips_messages_without_bytes_or_text(self):
        """Test that run skips messages without 'bytes' or 'text' keys"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        executor.register_text_handler(TestHandler())
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"type": "other"},  # Should be skipped
            {"text": "valid message"},
            {"other": "key"},  # Should be skipped
            WebSocketDisconnect(),
        ]
        
        await runner.run(websocket)
        
        # Only the valid text message should be processed
        assert len(handled_data) == 1
        assert handled_data[0] == "valid message"

    @pytest.mark.asyncio
    async def test_run_handles_websocket_disconnect(self):
        """Test that run exits normally when WebSocketDisconnect is raised"""
        executor = MessageHandlerExecutor()
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = WebSocketDisconnect()
        
        # Should not raise an exception, just return normally
        await runner.run(websocket)
        
        # Verify receive was called
        assert websocket.receive.called

    @pytest.mark.asyncio
    async def test_run_handles_websocket_disconnect_after_messages(self):
        """Test that run exits normally after processing messages when WebSocketDisconnect is raised"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class TestHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data)

        executor.register_bytes_handler(TestHandler())
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"bytes": b"message1"},
            {"bytes": b"message2"},
            WebSocketDisconnect(),
        ]
        
        await runner.run(websocket)
        
        # Messages should be processed before disconnect
        assert len(handled_data) == 2
        assert handled_data == [b"message1", b"message2"]

    @pytest.mark.asyncio
    async def test_run_re_raises_other_exceptions(self):
        """Test that run re-raises exceptions other than WebSocketDisconnect"""
        executor = MessageHandlerExecutor()
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = ValueError("Some error")
        
        with pytest.raises(ValueError, match="Some error"):
            await runner.run(websocket)

    @pytest.mark.asyncio
    async def test_run_propagates_executor_exceptions(self):
        """Test that exceptions from executor are propagated"""
        executor = MessageHandlerExecutor()
        # Don't register any handlers, so executor will raise ValueError
        
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"bytes": b"test"},
            WebSocketDisconnect(),  # This won't be reached
        ]
        
        with pytest.raises(ValueError, match="No bytes handler registered"):
            await runner.run(websocket)

    @pytest.mark.asyncio
    async def test_run_with_empty_messages(self):
        """Test that run processes empty messages correctly"""
        executor = MessageHandlerExecutor()
        bytes_data = []
        text_data = []

        class BytesHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                bytes_data.append(data)

        class TextHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                text_data.append(data)

        executor.register_bytes_handler(BytesHandler())
        executor.register_text_handler(TextHandler())
        runner = WebSocketRunner(executor)
        
        websocket = AsyncMock()
        websocket.receive.side_effect = [
            {"bytes": b""},
            {"text": ""},
            WebSocketDisconnect(),
        ]
        
        await runner.run(websocket)
        
        assert len(bytes_data) == 1
        assert len(text_data) == 1
        assert bytes_data[0] == b""
        assert text_data[0] == ""

