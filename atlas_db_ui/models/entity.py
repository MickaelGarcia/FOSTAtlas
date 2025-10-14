"""Global entity model."""

from __future__ import annotations

from typing import Any

from Qt import QtCore as qtc
from typing_extensions import override

from atlas_db.models import Base


class EntityItem:
    """Base entity node."""

    def __init__(
        self, entity: Base | None, columns: list[str], parent: EntityItem | None = None
    ):
        self._entity = entity
        self._parent = parent
        self._children: list[EntityItem] = []
        self._columns = columns

    @property
    def parent(self) -> EntityItem | None:
        """Return entity parent."""
        return self._parent

    @property
    def child_count(self) -> int:
        """Return number of children."""
        return len(self._children)

    @property
    def column_count(self) -> int:
        """Return number of column."""
        return len(self._columns)

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
            return self._columns[column] if 0 <= column < self.column_count else None
        elif role == qtc.Qt.UserRole:
            return self._entity
        return None

    def row(self) -> int:
        """Return node index in parent's children list."""
        if self._parent is None:
            return 0
        return self._parent.child_index(self)


class EntityTreeModel(qtc.QAbstractItemModel):
    """Entity tree model to show entities."""

    def __init__(self, entity_type: type[Base], headers: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self._root_item = EntityItem(None, headers)

        self._items = []

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
    def columnCount(self, parent = ...):
        return self._root_item.column_count

    @override
    def headerData(self, section, orientation, role = ...):
        if orientation == qtc.Qt.Horizontal and role == qtc.Qt.DisplayRole:
            return self._root_item.data(section, qtc.Qt.DisplayRole)
        return None

    @override
    def data(self, index, role = ...):
        if not index.isValid():
            return None

        item: EntityItem = index.internalPointer()

        if role == qtc.Qt.DisplayRole:
            return item.data(index.column(), qtc.Qt.DisplayRole)
        elif role == qtc.Qt.UserRole:
            return item.data(index.column(), qtc.Qt.UserRole)

        return None
