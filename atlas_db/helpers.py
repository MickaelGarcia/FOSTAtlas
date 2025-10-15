"""Database helper module."""
from __future__ import annotations

from atlas_db.context import DbQueryContext
from atlas_db.errors import MissingDbAssetTypeError
from atlas_db.errors import MissingDbProjectError
from atlas_db.errors import MissingDbTaskTypeError
from atlas_db.models import AssetType
from atlas_db.models import Base
from atlas_db.models import Project
from atlas_db.models import TaskType


def entity_by_code(entity: type[Base], code: str):
    """Get entity by his type and code."""
    with DbQueryContext() as db:
        db.expire_on_commit = False
        value = db.query(entity).where(entity.code == code).first()

    return value

def get_project(code: str) -> Project:
    """Get project by code."""
    project = entity_by_code(Project, code)
    if not project:
        raise MissingDbProjectError
    return project

def get_asset_type(code: str) -> AssetType:
    """Get asset type by code."""
    asset_type = entity_by_code(AssetType, code)
    if not asset_type:
        raise MissingDbAssetTypeError
    return asset_type

def get_task_type(code: str) -> TaskType:
    """Get task type by code."""
    task_type = entity_by_code(TaskType, code)
    if not task_type:
        raise MissingDbTaskTypeError
    return task_type
