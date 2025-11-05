"""
Unit tests for message_handler module
"""

import pytest
from unittest.mock import Mock

from transcriber.message_handler import (
    MessageHandler,
    BytesMessageHandler,
    TextMessageHandler,
    MessageType,
    MessageHandlerExecutor,
)


class TestMessageType:
    """Test MessageType enum"""

    def test_message_type_enum_values(self):
        """Test that MessageType enum has correct values"""
        assert MessageType.BYTES.value == "bytes"
        assert MessageType.TEXT.value == "text"

    def test_message_type_enum_members(self):
        """Test that MessageType enum has correct members"""
        assert MessageType.BYTES in MessageType
        assert MessageType.TEXT in MessageType


class TestMessageHandler:
    """Test MessageHandler abstract base class"""

    def test_message_handler_is_abstract(self):
        """Test that MessageHandler cannot be instantiated directly"""
        with pytest.raises(TypeError):
            MessageHandler()  # type: ignore

    def test_message_handler_has_abstract_methods(self):
        """Test that MessageHandler has abstract methods"""
        assert hasattr(MessageHandler, "handle")
        assert hasattr(MessageHandler, "handle_message")

    def test_message_handler_handle_message_not_implemented(self):
        """Test that calling handle_message on incomplete subclass raises NotImplementedError"""
        class IncompleteHandler(MessageHandler[str]):
            def handle(self, data: str) -> None:
                pass

        handler = IncompleteHandler()
        message = {"text": "test"}

        with pytest.raises(NotImplementedError, match="Subclasses must implement handle_message"):
            handler.handle_message(message)


class TestBytesMessageHandler:
    """Test BytesMessageHandler class"""

    def test_bytes_message_handler_can_be_instantiated(self):
        """Test that BytesMessageHandler can be instantiated"""
        handler = BytesMessageHandler()
        assert isinstance(handler, MessageHandler)
        assert isinstance(handler, BytesMessageHandler)

    def test_handle_bytes_message_with_valid_data(self):
        """Test handling a bytes message with valid data"""
        handled_data = []

        class TestHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message = {"bytes": b"test data"}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == b"test data"
        assert isinstance(handled_data[0], bytes)

    def test_handle_bytes_message_missing_bytes_key(self):
        """Test that handle_message raises ValueError when 'bytes' key is missing"""
        handler = BytesMessageHandler()
        message = {"text": "some text"}

        with pytest.raises(ValueError, match="Message does not contain 'bytes' key"):
            handler.handle_message(message)

    def test_handle_bytes_message_with_wrong_type(self):
        """Test that handle_message raises TypeError when data is not bytes"""
        handler = BytesMessageHandler()
        message = {"bytes": "not bytes"}

        with pytest.raises(TypeError, match="Expected bytes, got str"):
            handler.handle_message(message)

    def test_handle_bytes_message_with_none(self):
        """Test that handle_message raises TypeError when data is None"""
        handler = BytesMessageHandler()
        message = {"bytes": None}

        with pytest.raises(TypeError, match="Expected bytes, got"):
            handler.handle_message(message)

    def test_handle_method_can_be_overridden(self):
        """Test that handle method can be overridden in subclass"""
        handled_data = []

        class CustomHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data.upper())

        handler = CustomHandler()
        message = {"bytes": b"test"}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == b"TEST"

    def test_handle_method_default_implementation(self):
        """Test that handle method has a default implementation that does nothing"""
        handler = BytesMessageHandler()
        message = {"bytes": b"test"}

        # Should not raise an error
        handler.handle_message(message)

    def test_multiple_bytes_messages(self):
        """Test handling multiple bytes messages"""
        handled_data = []

        class TestHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message1 = {"bytes": b"data1"}
        message2 = {"bytes": b"data2"}
        message3 = {"bytes": b"data3"}

        handler.handle_message(message1)
        handler.handle_message(message2)
        handler.handle_message(message3)

        assert len(handled_data) == 3
        assert handled_data == [b"data1", b"data2", b"data3"]


class TestTextMessageHandler:
    """Test TextMessageHandler class"""

    def test_text_message_handler_can_be_instantiated(self):
        """Test that TextMessageHandler can be instantiated"""
        handler = TextMessageHandler()
        assert isinstance(handler, MessageHandler)
        assert isinstance(handler, TextMessageHandler)

    def test_handle_text_message_with_valid_data(self):
        """Test handling a text message with valid data"""
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message = {"text": "test message"}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == "test message"
        assert isinstance(handled_data[0], str)

    def test_handle_text_message_missing_text_key(self):
        """Test that handle_message raises ValueError when 'text' key is missing"""
        handler = TextMessageHandler()
        message = {"bytes": b"some bytes"}

        with pytest.raises(ValueError, match="Message does not contain 'text' key"):
            handler.handle_message(message)

    def test_handle_text_message_with_wrong_type(self):
        """Test that handle_message raises TypeError when data is not str"""
        handler = TextMessageHandler()
        message = {"text": b"not text"}

        with pytest.raises(TypeError, match="Expected str, got bytes"):
            handler.handle_message(message)

    def test_handle_text_message_with_none(self):
        """Test that handle_message raises TypeError when data is None"""
        handler = TextMessageHandler()
        message = {"text": None}

        with pytest.raises(TypeError, match="Expected str, got"):
            handler.handle_message(message)

    def test_handle_method_can_be_overridden(self):
        """Test that handle method can be overridden in subclass"""
        handled_data = []

        class CustomHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data.upper())

        handler = CustomHandler()
        message = {"text": "test"}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == "TEST"

    def test_handle_method_default_implementation(self):
        """Test that handle method has a default implementation that does nothing"""
        handler = TextMessageHandler()
        message = {"text": "test"}

        # Should not raise an error
        handler.handle_message(message)

    def test_multiple_text_messages(self):
        """Test handling multiple text messages"""
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message1 = {"text": "message1"}
        message2 = {"text": "message2"}
        message3 = {"text": "message3"}

        handler.handle_message(message1)
        handler.handle_message(message2)
        handler.handle_message(message3)

        assert len(handled_data) == 3
        assert handled_data == ["message1", "message2", "message3"]


class TestMessageHandlerIntegration:
    """Integration tests for MessageHandler subclasses"""

    def test_bytes_and_text_handlers_are_independent(self):
        """Test that bytes and text handlers work independently"""
        bytes_data = []
        text_data = []

        class BytesHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                bytes_data.append(data)

        class TextHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                text_data.append(data)

        bytes_handler = BytesHandler()
        text_handler = TextHandler()

        bytes_message = {"bytes": b"binary data"}
        text_message = {"text": "text data"}

        bytes_handler.handle_message(bytes_message)
        text_handler.handle_message(text_message)

        assert len(bytes_data) == 1
        assert len(text_data) == 1
        assert bytes_data[0] == b"binary data"
        assert text_data[0] == "text data"

    def test_handler_exception_propagation(self):
        """Test that exceptions in handle method propagate correctly"""
        class FailingHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                raise ValueError("Handler error")

        handler = FailingHandler()
        message = {"bytes": b"test"}

        with pytest.raises(ValueError, match="Handler error"):
            handler.handle_message(message)

    def test_empty_bytes_message(self):
        """Test handling empty bytes message"""
        handled_data = []

        class TestHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message = {"bytes": b""}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == b""

    def test_empty_text_message(self):
        """Test handling empty text message"""
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message = {"text": ""}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == ""

    def test_message_with_extra_keys(self):
        """Test that handlers work with messages containing extra keys"""
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        handler = TestHandler()
        message = {"text": "test", "extra": "data", "another": 123}
        handler.handle_message(message)

        assert len(handled_data) == 1
        assert handled_data[0] == "test"


class TestMessageHandlerExecutor:
    """Test MessageHandlerExecutor class"""

    def test_executor_initialization(self):
        """Test that executor initializes with no handlers"""
        executor = MessageHandlerExecutor()
        assert not executor.has_bytes_handler()
        assert not executor.has_text_handler()
        assert executor.get_bytes_handler() is None
        assert executor.get_text_handler() is None

    def test_register_bytes_handler(self):
        """Test registering a bytes handler"""
        executor = MessageHandlerExecutor()
        handler = BytesMessageHandler()
        
        executor.register_bytes_handler(handler)
        
        assert executor.has_bytes_handler()
        assert executor.get_bytes_handler() == handler

    def test_register_text_handler(self):
        """Test registering a text handler"""
        executor = MessageHandlerExecutor()
        handler = TextMessageHandler()
        
        executor.register_text_handler(handler)
        
        assert executor.has_text_handler()
        assert executor.get_text_handler() == handler

    def test_register_bytes_handler_wrong_type(self):
        """Test that registering wrong type raises TypeError"""
        executor = MessageHandlerExecutor()
        
        with pytest.raises(TypeError, match="Expected BytesMessageHandler"):
            executor.register_bytes_handler(TextMessageHandler())  # type: ignore

    def test_register_text_handler_wrong_type(self):
        """Test that registering wrong type raises TypeError"""
        executor = MessageHandlerExecutor()
        
        with pytest.raises(TypeError, match="Expected TextMessageHandler"):
            executor.register_text_handler(BytesMessageHandler())  # type: ignore

    def test_execute_bytes_message(self):
        """Test executing a bytes message"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class TestHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append(data)

        handler = TestHandler()
        executor.register_bytes_handler(handler)
        
        message = {"bytes": b"test data"}
        executor.execute(message)
        
        assert len(handled_data) == 1
        assert handled_data[0] == b"test data"

    def test_execute_text_message(self):
        """Test executing a text message"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class TestHandler(TextMessageHandler):
            def handle(self, data: str) -> None:
                handled_data.append(data)

        handler = TestHandler()
        executor.register_text_handler(handler)
        
        message = {"text": "test message"}
        executor.execute(message)
        
        assert len(handled_data) == 1
        assert handled_data[0] == "test message"

    def test_execute_bytes_message_no_handler(self):
        """Test that executing bytes message without handler raises ValueError"""
        executor = MessageHandlerExecutor()
        message = {"bytes": b"test"}
        
        with pytest.raises(ValueError, match="No bytes handler registered"):
            executor.execute(message)

    def test_execute_text_message_no_handler(self):
        """Test that executing text message without handler raises ValueError"""
        executor = MessageHandlerExecutor()
        message = {"text": "test"}
        
        with pytest.raises(ValueError, match="No text handler registered"):
            executor.execute(message)

    def test_execute_message_without_bytes_or_text_key(self):
        """Test that executing message without bytes or text key raises ValueError"""
        executor = MessageHandlerExecutor()
        message = {"other": "data"}
        
        with pytest.raises(ValueError, match="Message must contain either 'bytes' or 'text' key"):
            executor.execute(message)

    def test_execute_multiple_messages(self):
        """Test executing multiple messages with both handlers"""
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
        
        executor.execute({"bytes": b"data1"})
        executor.execute({"text": "message1"})
        executor.execute({"bytes": b"data2"})
        executor.execute({"text": "message2"})
        
        assert len(bytes_data) == 2
        assert len(text_data) == 2
        assert bytes_data == [b"data1", b"data2"]
        assert text_data == ["message1", "message2"]

    def test_replace_handler(self):
        """Test that registering a new handler replaces the old one"""
        executor = MessageHandlerExecutor()
        handled_data = []

        class Handler1(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append("handler1")

        class Handler2(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                handled_data.append("handler2")

        executor.register_bytes_handler(Handler1())
        executor.execute({"bytes": b"test"})
        
        executor.register_bytes_handler(Handler2())
        executor.execute({"bytes": b"test"})
        
        assert handled_data == ["handler1", "handler2"]

    def test_handler_exception_propagation(self):
        """Test that exceptions from handlers propagate correctly"""
        executor = MessageHandlerExecutor()

        class FailingHandler(BytesMessageHandler):
            def handle(self, data: bytes) -> None:
                raise ValueError("Handler error")

        executor.register_bytes_handler(FailingHandler())
        
        with pytest.raises(ValueError, match="Handler error"):
            executor.execute({"bytes": b"test"})

    def test_empty_message(self):
        """Test executing empty messages"""
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
        
        executor.execute({"bytes": b""})
        executor.execute({"text": ""})
        
        assert len(bytes_data) == 1
        assert len(text_data) == 1
        assert bytes_data[0] == b""
        assert text_data[0] == ""
