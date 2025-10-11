"""Db models module."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import MappedAsDataclass
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(MappedAsDataclass, DeclarativeBase):
    """Subclasses will be converted to dataclasses."""


class Project(Base):
    """Project table."""

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
        init=False,
    )
    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=False, nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="project", init=False)

    meta: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON()),
        default=dict,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(default=True)


class AssetType(Base):
    """Asset type table."""

    __tablename__ = "asset_type"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
        init=False,
    )
    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="asset_type", init=False)

    active: Mapped[bool] = mapped_column(default=True)


class Asset(Base):
    """Asset table."""

    __tablename__ = "asset"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True, init=False
    )
    code: Mapped[str] = mapped_column(nullable=False)

    asset_type_id: Mapped[int] = mapped_column(ForeignKey("asset_type.id"), init=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), init=False)

    project: Mapped[Project] = relationship(back_populates="asset")
    asset_type: Mapped[AssetType] = relationship(back_populates="asset")
    task: Mapped[Task] = relationship(back_populates="asset", init=False)

    active: Mapped[bool] = mapped_column(default=True)

    @property
    def name(self):
        """Return asset name."""
        return self.code


class TaskType(Base):
    """Task type table."""

    __tablename__ = "task_type"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True, init=False
    )
    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    task: Mapped[Task] = relationship(back_populates="task_type", init=False)

    active: Mapped[bool] = mapped_column(default=True)


class Task(Base):
    """Task table."""

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True, init=False
    )
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id"))
    task_type_id: Mapped[int] = mapped_column(ForeignKey("task_type.id"))

    asset: Mapped[Asset] = relationship(back_populates="task")
    task_type: Mapped[TaskType] = relationship(back_populates="task")
    publish: Mapped[Publish] = relationship(back_populates="task", init=False)

    active: Mapped[bool] = mapped_column(default=True)

    @property
    def name(self):
        """Wrap name from task_type code."""
        return self.task_type.name


class PublishType(Base):
    """Publish type table."""

    __tablename__ = "publish_type"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True, init=False
    )
    code: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False)
    extension: Mapped[str] = mapped_column(nullable=False)

    publish: Mapped[Publish] = relationship(back_populates="publish_type", init=False)

    active: Mapped[bool] = mapped_column(default=True)


class Publish(Base):
    """Publish table."""

    __tablename__ = "publish"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True, init=False
    )
    code: Mapped[str] = mapped_column(nullable=False)
    path: Mapped[str] = mapped_column(nullable=False, unique=True)
    version: Mapped[int] = mapped_column(nullable=False)
    release: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[int]

    publish_type_id: Mapped[int] = mapped_column(ForeignKey("publish_type.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))

    publish_type: Mapped[PublishType] = relationship(back_populates="publish")
    task: Mapped[Task] = relationship(back_populates="publish")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        default=None,
    )
    active: Mapped[bool] = mapped_column(default=True)
