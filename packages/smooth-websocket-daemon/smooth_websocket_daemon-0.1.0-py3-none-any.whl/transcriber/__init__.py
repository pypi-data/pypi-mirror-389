"""
Google API Server Transcriber - A FastAPI-based WebSocket library
"""

__version__ = "0.1.0"

try:
    from .server import WebSocketServer, create_app
except ImportError:
    # server module may not exist
    WebSocketServer = None  # type: ignore
    create_app = None  # type: ignore

from .message_handler import (
    MessageHandler,
    BytesMessageHandler,
    TextMessageHandler,
    MessageType,
    MessageHandlerExecutor,
    WebSocketRunner,
)

__all__ = [
    "MessageHandler",
    "BytesMessageHandler",
    "TextMessageHandler",
    "MessageType",
    "MessageHandlerExecutor",
    "WebSocketRunner",
    "__version__",
]

# Add server exports if available
if WebSocketServer is not None:
    __all__.extend(["WebSocketServer", "create_app"])

