import uuid
from typing import Any
from sqlalchemy import String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.inspection import inspect

# ─── Base Class ───────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""

    def serialize(
        self, include_relationships: bool = True, exclude_columns: list[str] | None = []
    ) -> dict:
        mapper = inspect(self)
        data = {}

        # serialize columns
        for column in mapper.mapper.column_attrs:
            if column.key not in exclude_columns:
                data[column.key] = getattr(self, column.key)

        if include_relationships:
            for rel in mapper.mapper.relationships:
                value = getattr(self, rel.key)

                if value is None:
                    data[rel.key] = None
                elif rel.uselist:
                    data[rel.key] = [
                        obj.serialize(False, exclude_columns) for obj in value
                    ]
                else:
                    data[rel.key] = value.serialize(False, exclude_columns)

        return data


# ─── Database Models ──────────────────────────────────────────────────────


class AIMessageRecord(Base):
    __tablename__ = "ai_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )

    human_message_id: Mapped[str] = mapped_column(
        ForeignKey("human_messages.id", ondelete="CASCADE"), nullable=False
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    thinking: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    tool_calls: Mapped[list["ToolCallRecord"]] = relationship(
        back_populates="ai_message", cascade="all, delete-orphan"
    )
    # <--- ADDED THIS: The Python bridge back to the Human message
    human_message: Mapped["HumanMessageRecord"] = relationship(
        back_populates="response"
    )

    def serialize(self, include_relationships: bool = True) -> dict:
        serialized = super().serialize(include_relationships)
        serialized["role"] = "assistant"
        return serialized


class HumanMessageRecord(Base):
    __tablename__ = "human_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)

    # <--- ADDED THIS: The Python bridge back to the Session
    session: Mapped["SessionRecord"] = relationship(back_populates="messages")

    attachments: Mapped[list["AttachmentRecord"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    response: Mapped["AIMessageRecord"] = relationship(
        back_populates="human_message", uselist=False, cascade="all, delete-orphan"
    )

    def serialize(self, include_relationships: bool = True) -> dict:
        serialized = super().serialize(include_relationships)
        serialized["role"] = "user"
        return serialized


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)

    # One-to-Many relationship with Messages
    messages: Mapped[list["HumanMessageRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AttachmentRecord(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # <--- ADDED THIS: The physical link to the Human Message
    human_message_id: Mapped[str] = mapped_column(
        ForeignKey("human_messages.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[str | None] = mapped_column(String)

    # Relationships
    message: Mapped["HumanMessageRecord"] = relationship(back_populates="attachments")


class ToolCallRecord(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # <--- ADDED THIS: The physical link to the AI Message
    ai_message_id: Mapped[str] = mapped_column(
        ForeignKey("ai_messages.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)

    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    # <--- ADDED THIS: The Python bridge back to the AI Message
    ai_message: Mapped["AIMessageRecord"] = relationship(back_populates="tool_calls")


class AIModel(Base):
    __tablename__ = "ai_models"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    custom: Mapped[bool] = mapped_column(Boolean, nullable=False)
