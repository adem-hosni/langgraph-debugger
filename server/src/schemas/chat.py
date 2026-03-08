from typing import Any, Literal, TypeAlias
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# ─── Base Configuration ───────────────────────────────────────────────────


class CamelBaseModel(BaseModel):
    """
    Base model that configures Pydantic to accept and output camelCase for the frontend,
    while allowing developers to use standard snake_case in Python.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Allows instantiating with either snake_case or camelCase
        from_attributes=True,
    )


# ─── Types & Enums ────────────────────────────────────────────────────────

ChatModeType: TypeAlias = Literal[
    "default", "thinking", "research", "creative", "concise"
]
AttachmentType: TypeAlias = Literal["code", "data", "image", "document"]
ToolIconType: TypeAlias = Literal["globe", "code", "database", "search"]
ToolStatusType: TypeAlias = Literal["completed", "running", "error"]
RoleType: TypeAlias = Literal["user", "assistant"]

# ─── Pydantic Models ──────────────────────────────────────────────────────


class Attachment(CamelBaseModel):
    name: str
    type: AttachmentType
    size: str | None = None


class ToolCall(CamelBaseModel):
    name: str
    icon: ToolIconType
    status: ToolStatusType
    input: dict[str, Any]
    output: dict[str, Any]


class ChatMessage(CamelBaseModel):
    id: str
    role: RoleType
    content: str
    attachments: list[Attachment] | None = None
    thinking: str | None = None
    toolCalls: list[ToolCall] | None = None
    timestamp: str


class ChatSession(CamelBaseModel):
    id: str
    title: str
    date: str
    messages: list[ChatMessage]


class AIModel(CamelBaseModel):
    value: str
    label: str
    custom: bool | None = None


class ChatModeInfo(CamelBaseModel):
    value: ChatModeType
    label: str
    description: str


# ─── Constants ────────────────────────────────────────────────────────────

CHAT_MODES: list[ChatModeInfo] = [
    ChatModeInfo(value="default", label="Default", description="Balanced responses"),
    ChatModeInfo(
        value="thinking", label="Deep Thinking", description="Step-by-step reasoning"
    ),
    ChatModeInfo(
        value="research", label="Research", description="In-depth analysis with sources"
    ),
    ChatModeInfo(
        value="creative", label="Creative", description="Imaginative and expressive"
    ),
    ChatModeInfo(
        value="concise", label="Concise", description="Brief and to the point"
    ),
]

DEFAULT_MODELS: list[AIModel] = [
    AIModel(value="gpt-4o", label="GPT-4o"),
    AIModel(value="claude-3.5-sonnet", label="Claude 3.5 Sonnet"),
    AIModel(value="gemini-1.5-pro", label="Gemini 1.5 Pro"),
    AIModel(value="gpt-4o-mini", label="GPT-4o Mini"),
]
# Add these to the bottom of langgraph_debugger/schemas/models.py


class SendMessageRequest(CamelBaseModel):
    sessionId: str
    content: str
    attachments: list[Attachment] | None = None
    model_name: str = Field(
        alias="model"
    )  # 'model' is a reserved Pydantic word, so we alias it
    mode: ChatModeType


class SendMessageResponse(CamelBaseModel):
    userMessage: ChatMessage
    assistantMessage: ChatMessage
    updatedSessionTitle: str | None = None
