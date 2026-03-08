import uuid
from typing import Any
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.inspection import inspect

# ─── Base Class ───────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""

    def serialize(self, include_relationships: bool = True) -> dict:
        mapper = inspect(self)

        data = {}

        # serialize columns
        for column in mapper.mapper.column_attrs:
            data[column.key] = getattr(self, column.key)

        if include_relationships:
            for rel in mapper.mapper.relationships:
                value = getattr(self, rel.key)

                if value is None:
                    data[rel.key] = None
                elif rel.uselist:
                    data[rel.key] = [obj.serialize(False) for obj in value]
                else:
                    data[rel.key] = value.serialize(False)

        return data


# ─── Database Models ──────────────────────────────────────────────────────


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)

    # One-to-Many relationship with Messages
    messages: Mapped[list["MessageRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class MessageRecord(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    thinking: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    session: Mapped["SessionRecord"] = relationship(back_populates="messages")

    attachments: Mapped[list["AttachmentRecord"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    tool_calls: Mapped[list["ToolCallRecord"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    
    def serialize(self, include_relationships: bool = True) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "sessionId": self.session_id,
            "content": self.content,
            "thinking": self.thinking,
            "timestamp": self.timestamp,
            "toolCalls": self.tool_calls,
            "attachments": self.attachments
        }


class AttachmentRecord(Base):
    __tablename__ = "attachments"

    # SQLite needs an integer primary key for sub-tables if no UUID is provided by the frontend
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'code' | 'data' | 'image' | 'document'
    size: Mapped[str | None] = mapped_column(String)

    # Relationships
    message: Mapped["MessageRecord"] = relationship(back_populates="attachments")


class ToolCallRecord(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str] = mapped_column(String, nullable=False)  # 'globe' | 'code' | etc.
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'completed' | 'running' | 'error'

    # SQLAlchemy handles converting Python dictionaries to JSON strings for SQLite automatically
    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    message: Mapped["MessageRecord"] = relationship(back_populates="tool_calls")
