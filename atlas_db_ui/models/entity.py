"""Global entity model."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from Qt import QtCore as qtc
from sqlalchemy.orm import Query
from typing_extensions import override

from atlas_db.context import DbCommitContext
from atlas_db.context import DbQueryContext
from atlas_db.models import Asset
from atlas_db.models import AssetType
from atlas_db.models import Base
from atlas_db.models import Project
from atlas_db.models import Task
from atlas_db.models import TaskType

EntityRole = qtc.Qt.UserRole + 1

COLUMN_BY_ENTITY_TYPE = {
    Asset: (
        ("Project", "Asset", "Type", "Active"),
        (Project.name, Asset.code, AssetType.name, Asset.active)
    ),
    Task: (
        ("Asset", "Name", "Active"),
        (Asset.code, TaskType.name, Task.active)
    )
}


class EntityItem:
    """Base entity node."""

    def __init__(
        self, entity: Base | None, columns: list[str], parent: EntityItem | None = None
    ):
        self._entity = entity
        self._parent = parent
        self._children: list[EntityItem] = []
        self.columns = columns

    @property
    def parent(self) -> EntityItem | None:
        """Return entity parent."""
        return self._parent

    @parent.setter
    def parent(self, value: EntityItem):
        """Set parent."""
        self._parent = value

    @property
    def child_count(self) -> int:
        """Return number of children."""
        return len(self._children)

    @property
    def column_count(self) -> int:
        """Return number of column."""
        return len(self.columns)

    def add_child(self, item: EntityItem):
        """Add child to item."""
        self._children.append(item)

    def child(self, row: int) -> EntityItem:
        """Return child at given row."""
        return self._children[row] if 0 <= row < self.child_count else None

    def child_index(self, item: EntityItem) -> int:
        """Return child index if given item is child."""
        if item not in self._children:
            return 0
        return self._children.index(item)

    def data(self, column: int, role: qtc.Qt.ItemDataRole) -> Any:
        """Return data from given column index."""
        if role == qtc.Qt.DisplayRole:
            return self.columns[column] if 0 <= column < self.column_count else None

        if role == qtc.Qt.UserRole and isinstance(self.columns[column], bool):
            return qtc.Qt.Checked if self._entity.active else qtc.Qt.Unchecked

        if role == EntityRole:
            return self._entity
        return None

    def row(self) -> int:
        """Return node index in parent's children list."""
        if self._parent is None:
            return 0
        return self._parent.child_index(self)


class EntityTreeModel(qtc.QAbstractItemModel):
    """Entity tree model to show entities."""

    def __init__(self, entity_type: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self._headers, query_args = COLUMN_BY_ENTITY_TYPE[entity_type]
        self._root_item = EntityItem(None, self._headers, None)
        self.entities: list[EntityItem] = []

        with DbQueryContext() as db:
            db.expire_on_commit = False
            query = (
                db.query(self._entity_type, *query_args)
                .select_from(Task)
                .join(Asset)
                .join(TaskType)

            )

        self._set_items(query)

    def _set_items(self, entities: list[Query]):
        """Set item in model."""
        self.beginResetModel()

        for entity in entities:
            name = list(entity)
            item = EntityItem(name[0], name[1:], self._root_item)
            self.entities.append(item)
            self._root_item.add_child(item)
        self.endResetModel()

    def group_by(self, property_name: str):
        """Group entity by given property_name."""
        if property_name not in self._headers:
            return
        index = self._headers.index(property_name)

        self.beginResetModel()
        entity_by_group = defaultdict(list)
        self._root_item = EntityItem(None, self._headers, None)
        for item in self.entities:
            entity_by_group[item.columns[index]].append(item)

        for name, entities in entity_by_group.items():
            header_len = len(self._headers)
            group = EntityItem(
                None,
                [name, *["" for _ in range(header_len)]],
                self._root_item
            )
            self._root_item.add_child(group)
            for entity in entities:
                entity.parent = group
                group.add_child(entity)

        self.endResetModel()

    @override
    def index(self, row: int, column: int, parent: qtc.QModelIndex | None = None):
        if parent is None:
            parent = qtc.QModelIndex()

        if not self.hasIndex(row, column, parent):
            return qtc.QModelIndex()

        parent_item = (
            self._root_item if not parent.isValid() else parent.internalPointer()
        )
        child_item = parent_item.child(row)
        if child_item is None:
            return qtc.QModelIndex()

        return self.createIndex(row, column, child_item)

    @override
    def parent(self, index: qtc.QModelIndex) -> qtc.QModelIndex:
        """Return parent of current node."""
        if not index.isValid():
            return qtc.QModelIndex()

        child_item: EntityItem = index.internalPointer()

        if child_item.parent is None or child_item.parent is self._root_item:
            return qtc.QModelIndex()

        return self.createIndex(child_item.parent.row(), 0, child_item.parent)

    @override
    def rowCount(self, parent=...):
        parent_item = (
            self._root_item if not parent.isValid() else parent.internalPointer()
        )
        return parent_item.child_count

    @override
    def columnCount(self, parent=...):
        return self._root_item.column_count

    @override
    def headerData(self, section, orientation, role=...):
        if orientation == qtc.Qt.Horizontal and role == qtc.Qt.DisplayRole:
            return self._root_item.data(section, qtc.Qt.DisplayRole)
        return None

    @override
    def flags(self, index):
        if not index.isValid():
            return qtc.Qt.NoItemFlags

        if self._root_item.columns[index.column()] == "Active":
            return super().flags(index) | qtc.Qt.ItemIsUserCheckable
        return super().flags(index)

    @override
    def data(self, index, role=...):
        if not index.isValid():
            return None

        item: EntityItem = index.internalPointer()
        column_name = self._root_item.columns[index.column()]

        if role == qtc.Qt.DisplayRole and column_name != "Active":
            return item.data(index.column(), qtc.Qt.DisplayRole)
        elif role == qtc.Qt.CheckStateRole and column_name == "Active":
            return item.data(index.column(), qtc.Qt.UserRole)

        elif role == qtc.Qt.UserRole:
            return item.data(index.column(), qtc.Qt.UserRole)

        return None

    @override
    def setData(self, index, value, role=...):
        if not index.isValid():
            return False

        entity: EntityItem = index.internalPointer()
        if role == qtc.Qt.CheckStateRole:
            entity.columns[index.column()] = value >= 1
            with DbCommitContext() as db:
                db_entity = entity.data(0, EntityRole)
                query = (
                    db.query(self._entity_type)
                    .where(self._entity_type.id == db_entity.id)
                    .first()
                )
                query.active = value >= 1

            return True
        return False
