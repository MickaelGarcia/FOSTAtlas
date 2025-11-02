"""Db models module."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
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

from atlas_db.errors import MissingDbAssetError
from atlas_db.errors import MissingDbTaskError


class Base(MappedAsDataclass, DeclarativeBase):
    """Subclasses will be converted to dataclasses."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def id(self):
        """Index requirement of model."""
        raise NotImplementedError

    @property
    def code(self):
        """Code requirement of model."""
        raise NotImplementedError

    @property
    def name(self):
        """Name requirement of model."""
        raise NotImplementedError

    @property
    def active(self):
        """Active requirement of model."""
        raise NotImplementedError

    @active.setter
    def active(self, value: bool):
        """Active Setter."""
        raise NotImplementedError


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

    asset: Mapped[list[Asset]] = relationship(
        back_populates="project",
        init=False,
        uselist=True,
        cascade="all, delete-orphan",
    )

    meta: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON()),
        default=dict,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(default=True)

    def assets(self) -> list[Asset]:
        """Get asset list related to project."""
        from atlas_db.context import DbQueryContext

        with DbQueryContext() as db:
            db.expire_on_commit = False
            assets = db.query(Asset).join(Project).filter(Asset.project == self)

        return list(assets)

    def get_asset(self, code: str, asset_type: AssetType) -> Asset:
        """Get asset by his code."""
        from atlas_db.context import DbQueryContext

        with DbQueryContext() as db:
            db.expire_on_commit = False
            asset = (
                db.query(Asset)
                .join(Project)
                .join(AssetType)
                .filter(
                    Asset.project == self,
                    Asset.code == code,
                    Asset.asset_type == asset_type,
                )
                .first()
            )
        if not asset:
            raise MissingDbAssetError

        return asset


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

    asset: Mapped[list[Asset]] = relationship(
        back_populates="asset_type",
        init=False,
        uselist=True,
        cascade="all, delete-orphan",
    )

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
    tasks: Mapped[list[Task]] = relationship(
        back_populates="asset",
        init=False,
        uselist=True,
        cascade="all, delete-orphan",
    )

    active: Mapped[bool] = mapped_column(default=True)

    @property
    def name(self):
        """Return asset name."""
        return self.code

    def get_task(self, task_type: TaskType) -> Task:
        """Get specific task from his task_type code or task_type."""
        from atlas_db.context import DbQueryContext

        with DbQueryContext() as db:
            db.expire_on_commit = False
            task = (
                db.query(Task)
                .join(Asset)
                .join(TaskType)
                .filter(Task.asset == self, Task.task_type == task_type)
                .first()
            )

        if not task:
            raise MissingDbTaskError

        return task



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
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id"), init=False)
    task_type_id: Mapped[int] = mapped_column(ForeignKey("task_type.id"), init=False)

    asset: Mapped[Asset] = relationship(back_populates="tasks")
    task_type: Mapped[TaskType] = relationship(back_populates="task")
    publish: Mapped[list[Publish]] = relationship(
        back_populates="task",
        init=False,
        uselist=True,
        cascade="all, delete-orphan",
    )

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


def update_model_value(
    model_name: str,
    row_id: int,
    column_name: str,
    new_value,
) -> None:
    """Update given model_name column_name with new given new_value.

    Args:
        session: Session SQLAlchemy active.
        model_name: Table class name (ex: "Asset").
        row_id: Column id
        column_name: Column name to edit.
        new_value: New value to set.
    """
    from atlas_db.context import DbCommitContext

    model_cls = globals().get(model_name)
    if model_cls is None:
        raise ValueError(f"No table named: {model_name}")

    with DbCommitContext() as db:
        obj = db.query(model_cls).filter_by(id=row_id).first()
        if obj is None:
            raise ValueError(f"No row with id ={row_id} in model {model_name}")

        if not hasattr(obj, column_name):
            raise ValueError(f"Unknown column: {column_name} in model {model_name}")

        setattr(obj, column_name, new_value)
