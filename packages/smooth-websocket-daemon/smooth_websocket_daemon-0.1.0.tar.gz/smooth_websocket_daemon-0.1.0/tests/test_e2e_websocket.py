"""
End-to-end tests for WebSocket server with WebSocketRunner
Tests actual handler functionality through WebSocket connections
"""

import asyncio
import json
from typing import Dict, List

import pytest
import websockets
from fastapi import FastAPI
from starlette.websockets import WebSocket

from transcriber.message_handler import (
    BytesMessageHandler,
    MessageHandlerExecutor,
    TextMessageHandler,
    WebSocketRunner,
)


# Handler that processes text messages and counts words
class WordCountHandler(TextMessageHandler):
    """Handler that counts words in text messages"""
    
    def __init__(self):
        self.word_count: int = 0
        self.processed_messages: List[str] = []
    
    def handle(self, data: str) -> None:
        """Count words in the text message"""
        words = data.split()
        self.word_count += len(words)
        self.processed_messages.append(data)


# Handler that processes JSON text messages
class JsonProcessingHandler(TextMessageHandler):
    """Handler that processes JSON text messages"""
    
    def __init__(self):
        self.processed_data: List[Dict] = []
        self.error_count: int = 0
    
    def handle(self, data: str) -> None:
        """Parse and process JSON messages"""
        try:
            json_data = json.loads(data)
            self.processed_data.append(json_data)
        except json.JSONDecodeError:
            self.error_count += 1


# Handler that processes bytes and calculates checksum
class ChecksumHandler(BytesMessageHandler):
    """Handler that calculates simple checksum for bytes messages"""
    
    def __init__(self):
        self.checksums: List[int] = []
        self.total_bytes: int = 0
    
    def handle(self, data: bytes) -> None:
        """Calculate checksum (sum of byte values)"""
        checksum = sum(data)
        self.checksums.append(checksum)
        self.total_bytes += len(data)


# Handler that processes audio bytes (simulated)
class AudioProcessingHandler(BytesMessageHandler):
    """Handler that simulates audio processing"""
    
    def __init__(self):
        self.processed_chunks: int = 0
        self.total_audio_bytes: int = 0
    
    def handle(self, data: bytes) -> None:
        """Process audio chunk (simulated)"""
        # Simulate processing: check if data looks like audio
        if len(data) > 0:
            self.processed_chunks += 1
            self.total_audio_bytes += len(data)


def create_test_app_with_handlers(
    text_handler: TextMessageHandler, bytes_handler: BytesMessageHandler
) -> FastAPI:
    """Create a FastAPI app with WebSocket endpoint using WebSocketRunner"""
    app = FastAPI()

    # Create executor and register handlers
    executor = MessageHandlerExecutor()
    executor.register_bytes_handler(bytes_handler)
    executor.register_text_handler(text_handler)
    runner = WebSocketRunner(executor)

    # Store handlers in app state for test access
    app.state.bytes_handler = bytes_handler
    app.state.text_handler = text_handler
    app.state.executor = executor
    app.state.runner = runner

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        await runner.run(websocket)

    return app


@pytest.mark.asyncio
async def test_e2e_word_count_handler():
    """Test WordCountHandler through WebSocket - counts words in text messages"""
    import socket
    import uvicorn

    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Create handler and app
    word_count_handler = WordCountHandler()
    checksum_handler = ChecksumHandler()
    app = create_test_app_with_handlers(word_count_handler, checksum_handler)

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    try:
        await asyncio.sleep(0.5)  # Wait for server to start

        uri = f"ws://127.0.0.1:{port}/ws"
        async with websockets.connect(uri) as websocket:
            # Send text messages
            await websocket.send("Hello world")
            await websocket.send("This is a test message")
            await websocket.send("Final message")

            # Give some time for processing
            await asyncio.sleep(0.2)

            # Verify handler processed messages correctly
            assert word_count_handler.word_count == 9  # "Hello world" (2) + "This is a test message" (5) + "Final message" (2)
            assert len(word_count_handler.processed_messages) == 3
            assert "Hello world" in word_count_handler.processed_messages
            assert "This is a test message" in word_count_handler.processed_messages

    finally:
        server.should_exit = True
        await server_task
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_e2e_checksum_handler():
    """Test ChecksumHandler through WebSocket - calculates checksums for bytes messages"""
    import socket
    import uvicorn

    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Create handler and app
    word_count_handler = WordCountHandler()
    checksum_handler = ChecksumHandler()
    app = create_test_app_with_handlers(word_count_handler, checksum_handler)

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    try:
        await asyncio.sleep(0.5)  # Wait for server to start

        uri = f"ws://127.0.0.1:{port}/ws"
        async with websockets.connect(uri) as websocket:
            # Send bytes messages
            data1 = b"\x01\x02\x03"
            data2 = b"\x04\x05"
            await websocket.send(data1)
            await websocket.send(data2)

            # Give some time for processing
            await asyncio.sleep(0.2)

            # Verify handler calculated checksums correctly
            assert len(checksum_handler.checksums) == 2
            assert checksum_handler.checksums[0] == 6  # 1+2+3
            assert checksum_handler.checksums[1] == 9  # 4+5
            assert checksum_handler.total_bytes == 5  # 3+2 bytes

    finally:
        server.should_exit = True
        await server_task
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_e2e_json_processing_handler():
    """Test JsonProcessingHandler through WebSocket - processes JSON text messages"""
    import socket
    import uvicorn

    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Create handler and app
    json_handler = JsonProcessingHandler()
    checksum_handler = ChecksumHandler()
    app = create_test_app_with_handlers(json_handler, checksum_handler)

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    try:
        await asyncio.sleep(0.5)  # Wait for server to start

        uri = f"ws://127.0.0.1:{port}/ws"
        async with websockets.connect(uri) as websocket:
            # Send valid JSON messages
            await websocket.send('{"type": "test", "value": 123}')
            await websocket.send('{"name": "Alice", "age": 30}')

            # Send invalid JSON
            await websocket.send("not json")

            # Give some time for processing
            await asyncio.sleep(0.2)

            # Verify handler processed JSON correctly
            assert len(json_handler.processed_data) == 2
            assert json_handler.processed_data[0] == {"type": "test", "value": 123}
            assert json_handler.processed_data[1] == {"name": "Alice", "age": 30}
            assert json_handler.error_count == 1  # One invalid JSON

    finally:
        server.should_exit = True
        await server_task
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_e2e_audio_processing_handler():
    """Test AudioProcessingHandler through WebSocket - processes audio bytes"""
    import socket
    import uvicorn

    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Create handler and app
    word_count_handler = WordCountHandler()
    audio_handler = AudioProcessingHandler()
    app = create_test_app_with_handlers(word_count_handler, audio_handler)

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    try:
        await asyncio.sleep(0.5)  # Wait for server to start

        uri = f"ws://127.0.0.1:{port}/ws"
        async with websockets.connect(uri) as websocket:
            # Send audio chunks (simulated)
            chunk1 = b"\x00" * 1024  # 1KB chunk
            chunk2 = b"\x01" * 2048  # 2KB chunk
            chunk3 = b"\x02" * 512   # 512B chunk
            await websocket.send(chunk1)
            await websocket.send(chunk2)
            await websocket.send(chunk3)

            # Give some time for processing
            await asyncio.sleep(0.2)

            # Verify handler processed audio correctly
            assert audio_handler.processed_chunks == 3
            assert audio_handler.total_audio_bytes == 3584  # 1024 + 2048 + 512

    finally:
        server.should_exit = True
        await server_task
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_e2e_mixed_handler_processing():
    """Test multiple handlers working together through WebSocket"""
    import socket
    import uvicorn
    
    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()
    
    # Create handlers
    word_count_handler = WordCountHandler()
    checksum_handler = ChecksumHandler()
    app = create_test_app_with_handlers(word_count_handler, checksum_handler)
    
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    
    try:
        await asyncio.sleep(0.5)  # Wait for server to start
        
        uri = f"ws://127.0.0.1:{port}/ws"
        async with websockets.connect(uri) as websocket:
            # Send text messages (processed by word_count_handler)
            await websocket.send("Hello world")
            await websocket.send("Test message")
            
            # Send bytes messages (processed by checksum_handler)
            await websocket.send(b"\x01\x02")
            await websocket.send(b"\x03\x04\x05")
            
            await asyncio.sleep(0.2)
            
            # Verify both handlers processed correctly
            assert word_count_handler.word_count == 4  # 2 + 2 words
            assert len(word_count_handler.processed_messages) == 2
            
            assert len(checksum_handler.checksums) == 2
            assert checksum_handler.checksums[0] == 3  # 1+2
            assert checksum_handler.checksums[1] == 12  # 3+4+5
            assert checksum_handler.total_bytes == 5
    
    finally:
        server.should_exit = True
        await server_task
        await asyncio.sleep(0.1)

