"""Db models module."""

from __future__ import annotations

import dataclasses
import json

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


Base = declarative_base()


class Project(Base):
    """Project table."""

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=False, nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
    meta: Mapped[JSON]

    asset: Mapped[list[Asset]] = relationship(back_populates="project")

    def set_metadata(self, meta: dict):
        """Set project metadata."""
        json.dumps(meta, indent=4)

    def get_metadata(self) -> dict:
        """Return metadata as dict"""
        return json.loads(self._meta)


class AssetType(Base):
    """Asset type table."""

    __tablename__ = "asset_type"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code: str = Column(String, unique=True, nullable=False)
    name: str = Column(String, unique=True, nullable=False)
    active: bool = Column(Boolean, default=True)

    asset: Asset = relationship("Asset", back_populates="asset_type")


class Asset(Base):
    """Asset table."""

    __tablename__ = "asset"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code: str = Column(String, nullable=False)
    active: bool = Column(Boolean, default=True)

    asset_type_id: int = Column(Integer, ForeignKey("asset_type.id"))
    project_id: int = Column(Integer, ForeignKey("project.id"))

    project: Project = relationship("Project", back_populates="asset")
    asset_type: AssetType = relationship("AssetType", back_populates="asset")
    task: Task = relationship("Task", back_populates="asset")

    @property
    def name(self):
        """Return asset name."""
        return self.code


class TaskType(Base):
    """Task type table."""

    __tablename__ = "task_type"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code: str = Column(String, unique=True, nullable=False)
    name: str = Column(String, unique=True, nullable=False)
    active: bool = Column(Boolean, default=True)

    task: Task = relationship("Task", back_populates="task_type")


class Task(Base):
    """Task table."""

    __tablename__ = "task"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    asset_id: int = Column(Integer, ForeignKey("asset.id"))
    task_type_id: int = Column(Integer, ForeignKey("task_type.id"))
    active: bool = Column(Boolean, default=True)

    asset: Asset = relationship("Asset", back_populates="task")
    task_type: TaskType = relationship("TaskType", back_populates="task")
    publish: Publish = relationship("Publish", back_populates="task")

    @property
    def name(self):
        """Wrap name from task_type code."""
        return self.task_type.name

class PublishType(Base):
    """Publish type table."""

    __tablename__ = "publish_type"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code: str = Column(String, nullable=False, unique=True)
    description: str = Column(String, nullable=False)
    extension: str = Column(String, nullable=False)
    active: bool = Column(Boolean, default=True)

    publish: Publish = relationship("Publish", back_populates="publish_type")


class Publish(Base):
    """Publish table."""

    __tablename__ = "publish"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code: str = Column(String, nullable=False)
    path: str = Column(String, nullable=False, unique=True)
    version: int = Column(Integer, nullable=False)
    release: str = Column(String, nullable=False)
    size: int = Column(Integer)
    active: bool = Column(Boolean, default=True)

    publish_type_id: int = Column(Integer, ForeignKey("publish_type.id"))
    task_id: int = Column(Integer, ForeignKey("task.id"))
    user_id: int = Column(Integer, ForeignKey("user.id"))

    publish_type: PublishType = relationship("PublishType", back_populates="publish")
    task: Task = relationship("Task", back_populates="publish")
    user: User = relationship("User", backref="publish")


class User(Base):
    """User table."""

    __tablename__ = "user"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code: str = Column(String, nullable=False)
    last_name: str = Column(String)
    first_name: str = Column(String)
    os_name: str = Column(String, nullable=False)
    mail: str = Column(String, nullable=False, unique=True)

    publish: Publish = relationship("User", back_populates="publish")
