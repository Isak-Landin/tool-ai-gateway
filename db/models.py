from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    orchestrator_name: Mapped[str] = mapped_column(String(255), nullable=False)

    system_prompt_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    system_prompt_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Message.sequence_no",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("project_id", "sequence_no", name="uq_messages_project_sequence"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    thinking: Mapped[str | None] = mapped_column(Text, nullable=True)

    tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_calls_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    images_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)

    ollama_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ollama_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    done: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    done_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)

    total_duration: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    load_duration: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    prompt_eval_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_eval_duration: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    eval_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eval_duration: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    raw_message_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    raw_response_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="messages")

class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    project_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )