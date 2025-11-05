"""Text message handler implementation"""

from starlette.types import Message

from transcriber.message_handler.base import MessageHandler


class TextMessageHandler(MessageHandler[str]):
    """Handler for text messages"""
    
    def handle_message(self, message: Message) -> None:
        """Extract text data from message and handle it"""
        if "text" not in message:
            raise ValueError("Message does not contain 'text' key")
        data = message["text"]
        if not isinstance(data, str):
            raise TypeError(f"Expected str, got {type(data).__name__}")
        self.handle(data)
    
    def handle(self, data: str) -> None:
        """
        Handle text message data
        
        Args:
            data: The text data to handle
        """
        pass

