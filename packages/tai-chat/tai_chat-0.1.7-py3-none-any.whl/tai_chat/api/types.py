from enum import Enum
from typing import Optional
from pydantic import BaseModel

class WebsocketMessageType(Enum):
    # LLM
    USER = "human"
    AI = "ai"
    AICHUNK = "AIMessageChunk"
    SYSTEM = "system"
    TOOL = "tool"
    TOOLCHUNK = "ToolMessageChunk"
    TOOLCALL = "tool_call"
    TOOLCALLCHUNK = "tool_call_chunk"
    # SERVICES
    CONNECTION_ESTABLISHED = "connection_established"
    PONG = "pong"
    MESSAGE_RECEIVED = "message_received"
    ASSISTANT_RESPONSE_START = "assistant_response_start"
    ASSISTANT_RESPONSE_COMPLETE = "assistant_response_complete"
    ASSISTANT_RESPONSE_ERROR = "assistant_response_error"

# Modelos de request/response
class StreamMessageRequest(BaseModel):
    content: str
    chat_id: int

class StreamMessageResponse(BaseModel):
    user_id: str
    msg_id: int
    connections_notified: int
    chat_id: int

class StreamingStatus(BaseModel):
    status: str
    message: str
    connections: int
    chat_id: Optional[int] = None