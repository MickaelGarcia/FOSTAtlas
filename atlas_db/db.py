"""Database object module."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tk_db.dbassettype import DbAssetType
from tk_db.dbproject import DbProject
from tk_db.dbpublishtype import DbPublishType
from tk_db.dbtasktype import DbTaskType
from tk_db.errors import DbAssetTypeAlreadyExistsError
from tk_db.errors import DbProjectAlreadyExistsError
from tk_db.errors import DbPublishTypeAlreadyExistError
from tk_db.errors import DbTaskTypeAlreadyExistError
from tk_db.errors import MissingDbAssetTypeError
from tk_db.errors import MissingDbProjectError
from tk_db.errors import MissingDbPublishTypeError
from tk_db.errors import MissingDbTaskTypeError
from tk_db.models import AssetType
from tk_db.models import Base
from tk_db.models import Project
from tk_db.models import PublishType
from tk_db.models import TaskType


class Db:
    """Database object."""

    _db_path = f"sqlite:///{os.path.dirname(__file__)}/test_alchemy.db"

    def __init__(self):
        engine = create_engine(self._db_path)
        self.Session = sessionmaker(engine)
        Base.metadata.create_all(bind=engine)

    def __repr__(self):
        return f"Db({self._db_path})"

    def project(self, code: str) -> DbProject:
        """Get Database project from his code.

        Args:
            code (str): Project code.

        Returns:
            Project: Instance of database project.

        Raises:
            MissingDbProjectError: Given project code not found in database.
        """
        with self.Session() as session:
            project_query = session.query(Project).where(Project.code == code)
            found_project = project_query.first()

        if found_project is None:
            raise MissingDbProjectError(f"Unable to found project with code: {code!r}")

        return DbProject(self, found_project)

    def projects(self) -> list[DbProject]:
        """Get all projects in database.

        Returns:
            list[DbProject]
        """
        with self.Session() as session:
            project_query = session.query(Project)
            projects = [DbProject(self, project) for project in project_query]

        return projects

    def create_project(self, code: str, name: str) -> DbProject:
        """Create new project in database project table.

        If given code:name already exist in database, return it.

        Args:
            code (str): Project code.
            name (str): Project name.

        Raises:
            DbProjectAlreadyExistsError

        Returns:
            DbProject
        """
        try:
            self.project(code)
        except MissingDbProjectError:
            with self.Session() as session:
                project_obj = Project(code=code, name=name, metadata_="{}", active=True)

                session.add(project_obj)
                session.commit()
        else:
            raise DbProjectAlreadyExistsError(
                f"Project {code!r} - {name!r} already exist."
            )

        return self.project(code)

    def asset_type(self, code: str) -> DbAssetType:
        """Get database asset type from his code.

        Args:
            code (str): Asset type code

        Returns:
            DbAssetType: Instance of database asset type.

        Raises:
            MissingDbAssetTypeError: Given asset type code not found in database.
        """
        with self.Session() as session:
            asset_type_query = session.query(AssetType).where(AssetType.code == code)
            found_asset_type = asset_type_query.first()

        if found_asset_type is None:
            raise MissingDbAssetTypeError(
                f"Unable to found asset type with code {code!r}"
            )

        return DbAssetType(self, found_asset_type)

    def asset_types(self) -> list[DbAssetType]:
        """Get all asset type table.

        Returns:
            list[DbAssetType
        """
        with self.Session() as session:
            asset_type_query = session.query(AssetType)
            asset_types = [
                DbAssetType(self, asset_type) for asset_type in asset_type_query
            ]

        return asset_types

    def get_or_create_asset_type(self, code: str, name: str) -> DbAssetType:
        """Create new asset type in database asset_type table.

        If given code:name already exist in database, return it.

        Args:
            code (str): Asset type code.
            name (str): Asset type name.

        Returns:
            DbAssetType
        """
        try:
            self.asset_type(code)
        except MissingDbAssetTypeError:
            with self.Session() as session:
                asset_type_obj = AssetType(code=code, name=name, active=True)
                session.add(asset_type_obj)
                session.commit()

        else:
            raise DbAssetTypeAlreadyExistsError(
                f"Asset type {code!r} - {name!r} already exists."
            )

        return self.asset_type(code)

    def task_type(self, code: str) -> DbTaskType:
        """Get task type object.

        Args:
            code (str): Task type code.

        Returns:
            DbTaskType: Instance of database asset type.

        Raises:
            MissingDbTaskTypeError: Given task type code not found in database.
        """
        with self.Session() as session:
            task_type_query = session.query(TaskType).where(TaskType.code == code)
            found_task_type = task_type_query.first()

        if found_task_type is None:
            raise MissingDbTaskTypeError(f"Unable to found task type with code {code!r}")

        return DbTaskType(self, found_task_type)

    def task_types(self) -> list[DbTaskType]:
        """Return all task types table.

        Returns:
            list[DbAssetType]
        """
        with self.Session() as session:
            tasks_query = session.query(TaskType)
            task_types = [DbTaskType(self, task) for task in tasks_query]

        return task_types

    def get_or_create_task_type(self, code: str, name: str) -> DbTaskType:
        """Create new task type in database.

        Args:
            code (str): Task type code.
            name (str): Task type name.

        Raises:
            DbTaskTypeAlreadyExistError

        Returns:
            DbTaskType
        """
        try:
            self.task_type(code)
        except MissingDbTaskTypeError:
            with self.Session() as session:
                task_type_obj = TaskType(code=code, name=name, active=True)
                session.add(task_type_obj)
                session.commit()

        else:
            raise DbTaskTypeAlreadyExistError(
                f"Task type {code!r} - {name!r} already exists."
            )

        return self.task_type(code)

    def publish_type(self, code: str) -> DbPublishType:
        """Get publish type object.

        Args:
            code (str): Publish type code.

        Returns:
            DbPublishType: Instance of database asset type.

        Raises:
            MissingDbPublishTypeError: Given publish type code not found in database.
        """
        with self.Session() as session:
            publish_type_query = session.query(PublishType).where(
                PublishType.code == code
            )
            found_publish_type = publish_type_query.first()

        if found_publish_type is None:
            raise MissingDbPublishTypeError(
                f"Unable to found task type with code {code!r}"
            )

        return DbPublishType(self, found_publish_type)

    def publish_types(self) -> list[DbPublishType]:
        """Return all publish types table.

        Returns:
            list[DbPublishType]
        """
        with self.Session() as session:
            publishs_query = session.query(PublishType)
            publish_types = [DbPublishType(self, publish) for publish in publishs_query]

        return publish_types

    def get_or_create_publish_type(
        self,
        code: str,
        file_type: str,
        extension: str,
    ) -> DbPublishType:
        """Create new task type in database.

        Args:
            code (str): Publish type description.
            file_type (str): Publish type file type.
            extension (str): Publish type extension.

        Raises:
            DbTaskTypeAlreadyExistError

        Returns:
            DbTaskType
        """
        try:
            self.publish_type(code)
        except MissingDbPublishTypeError:
            with self.Session() as session:
                publish_type_obj = PublishType(
                    code=code,
                    file_type=file_type,
                    extension=extension,
                    active=True
                )
                session.add(publish_type_obj)
                session.commit()

        else:
            raise DbPublishTypeAlreadyExistError(f"Publish type {code!r} already exists.")

        return self.publish_type(code)
