"""Message handler executor"""

from typing import Optional

from starlette.types import Message

from transcriber.message_handler.bytes_handler import BytesMessageHandler
from transcriber.message_handler.text_handler import TextMessageHandler


class MessageHandlerExecutor:
    """Executor for managing and executing message handlers"""
    
    def __init__(self):
        """Initialize the executor with empty handlers"""
        self._bytes_handler: Optional[BytesMessageHandler] = None
        self._text_handler: Optional[TextMessageHandler] = None
    
    def register_bytes_handler(self, handler: BytesMessageHandler) -> None:
        """
        Register a bytes message handler
        
        Args:
            handler: The bytes message handler to register
        """
        if not isinstance(handler, BytesMessageHandler):
            raise TypeError(f"Expected BytesMessageHandler, got {type(handler).__name__}")
        self._bytes_handler = handler
    
    def register_text_handler(self, handler: TextMessageHandler) -> None:
        """
        Register a text message handler
        
        Args:
            handler: The text message handler to register
        """
        if not isinstance(handler, TextMessageHandler):
            raise TypeError(f"Expected TextMessageHandler, got {type(handler).__name__}")
        self._text_handler = handler
    
    def execute(self, message: Message) -> None:
        """
        Execute the appropriate handler for the message
        
        Args:
            message: Starlette Message dictionary containing 'bytes' or 'text' key
            
        Raises:
            ValueError: If message does not contain 'bytes' or 'text' key
            ValueError: If no handler is registered for the message type
        """
        if "bytes" in message:
            if self._bytes_handler is None:
                raise ValueError("No bytes handler registered")
            self._bytes_handler.handle_message(message)
        elif "text" in message:
            if self._text_handler is None:
                raise ValueError("No text handler registered")
            self._text_handler.handle_message(message)
        else:
            raise ValueError("Message must contain either 'bytes' or 'text' key")
    
    def has_bytes_handler(self) -> bool:
        """
        Check if a bytes handler is registered
        
        Returns:
            True if bytes handler is registered, False otherwise
        """
        return self._bytes_handler is not None
    
    def has_text_handler(self) -> bool:
        """
        Check if a text handler is registered
        
        Returns:
            True if text handler is registered, False otherwise
        """
        return self._text_handler is not None
    
    def get_bytes_handler(self) -> Optional[BytesMessageHandler]:
        """
        Get the registered bytes handler
        
        Returns:
            The bytes handler if registered, None otherwise
        """
        return self._bytes_handler
    
    def get_text_handler(self) -> Optional[TextMessageHandler]:
        """
        Get the registered text handler
        
        Returns:
            The text handler if registered, None otherwise
        """
        return self._text_handler

