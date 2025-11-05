"""Base message handler class"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from starlette.types import Message

T = TypeVar("T")


class MessageHandler(ABC, Generic[T]):
    """Base message handler class with generic type support"""
    
    @abstractmethod
    def handle(self, data: T) -> None:
        """
        Handle the message data
        
        Args:
            data: The message data of type T
        """
        pass
    
    def handle_message(self, message: Message) -> None:
        """
        Extract data from Message and call handle method
        
        Args:
            message: Starlette Message dictionary
        """
        raise NotImplementedError("Subclasses must implement handle_message")

