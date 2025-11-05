"""Bytes message handler implementation"""

from starlette.types import Message

from transcriber.message_handler.base import MessageHandler


class BytesMessageHandler(MessageHandler[bytes]):
    """Handler for bytes messages"""
    
    def handle_message(self, message: Message) -> None:
        """Extract bytes data from message and handle it"""
        if "bytes" not in message:
            raise ValueError("Message does not contain 'bytes' key")
        data = message["bytes"]
        if not isinstance(data, bytes):
            raise TypeError(f"Expected bytes, got {type(data).__name__}")
        self.handle(data)
    
    def handle(self, data: bytes) -> None:
        """
        Handle bytes message data
        
        Args:
            data: The bytes data to handle
        """
        pass

