"""SQLAlchemy models."""

from __future__ import annotations

from typing import Any
import uuid

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Workspace(Base, TimestampMixin):
    """A user-owned workspace that groups goals and plans."""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="workspaces")
    goals: Mapped[list["Goal"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class Goal(Base, TimestampMixin):
    """A structured goal stored by backend-api before orchestration."""

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    domain_hint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    interpreted_goal: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ai_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="goals")
    plans: Mapped[list["Plan"]] = relationship(back_populates="goal", cascade="all, delete-orphan")


class Plan(Base, TimestampMixin):
    """Stored plan result returned by ai-service."""

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    execution_decisions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    approval_ready_execution_decisions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    goal: Mapped["Goal"] = relationship(back_populates="plans")
