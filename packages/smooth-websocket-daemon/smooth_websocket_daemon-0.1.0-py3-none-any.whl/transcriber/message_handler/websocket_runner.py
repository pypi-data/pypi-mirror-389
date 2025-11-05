"""WebSocket runner for processing messages"""

from starlette.websockets import WebSocket, WebSocketDisconnect

from transcriber.message_handler.executor import MessageHandlerExecutor


class WebSocketRunner:
    """Runner class for processing WebSocket messages through MessageHandlerExecutor"""
    
    def __init__(self, executor: MessageHandlerExecutor):
        """
        Initialize the WebSocket runner with a MessageHandlerExecutor
        
        Args:
            executor: The MessageHandlerExecutor instance to use for processing messages
        """
        if not isinstance(executor, MessageHandlerExecutor):
            raise TypeError(f"Expected MessageHandlerExecutor, got {type(executor).__name__}")
        self._executor = executor
    
    async def run(self, websocket: WebSocket) -> None:
        """
        Run the message processing loop, receiving messages from WebSocket and passing to executor
        
        Args:
            websocket: The WebSocket connection to receive messages from
            
        This method will continuously receive messages from the WebSocket and pass them
        to the MessageHandlerExecutor until the connection is closed or an error occurs.
        When WebSocketDisconnect is raised, the loop will exit normally.
        """
        try:
            while True:
                message = await websocket.receive()
                # Only process messages with 'bytes' or 'text' keys
                if "bytes" in message or "text" in message:
                    self._executor.execute(message)
        except WebSocketDisconnect:
            # Connection closed - exit loop normally
            return
        except Exception:
            # Other errors - re-raise to let caller handle
            raise
    
    def get_executor(self) -> MessageHandlerExecutor:
        """
        Get the MessageHandlerExecutor instance
        
        Returns:
            The MessageHandlerExecutor instance
        """
        return self._executor

