"""Entity model module."""

from __future__ import annotations

from typing import override

from Qt import QtCore as qtc

from atlas_db.context import DbCommitContext
from atlas_db.models import Base


ActiveRole = qtc.Qt.UserRole + 1


class EntityTypeTableModel(qtc.QAbstractTableModel):
    """Entity table model object."""

    def __init__(self, entity_type: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self._entities: list[Base] = []
        self._column_names = entity_type.__table__.columns.keys()

    @override
    def rowCount(self, parent=...):
        return len(self._entities)

    @override
    def columnCount(self, parent=...):
        return len(self._column_names)

    @override
    def data(self, index, role=...):
        if not index.isValid():
            return None
        entity = self._entities[index.row()]
        column = index.column()
        column_name = self._column_names[column]

        if role == qtc.Qt.DisplayRole and column_name != "active":
            return getattr(entity, column_name, None)
        if role == qtc.Qt.UserRole:
            return entity

        if role == qtc.Qt.TextAlignmentRole:
            return int(qtc.Qt.AlignCenter)

        if role == qtc.Qt.CheckStateRole and column_name == "active":
            return qtc.Qt.Checked if entity.active else qtc.Qt.Unchecked

        return None

    @override
    def setData(self, index, value, role=...):
        if not index.isValid():
            return False

        entity = self._entities[index.row()]
        if role == qtc.Qt.CheckStateRole:
            with DbCommitContext() as db:
                loaded_entity = db.query(self._entity_type).where(
                    self._entity_type.id == entity.id
                ).first()
                loaded_entity.active = bool(value)
            entity.active = bool(value)
            return True

        return False

    @override
    def flags(self, index):
        flags = super().flags(index)
        col = index.column()

        if self._column_names[col] == "active":
            flags |= qtc.Qt.ItemIsUserCheckable

        return flags

    @override
    def headerData(self, section, orientation, role=...):
        if role == qtc.Qt.DisplayRole and orientation == qtc.Qt.Horizontal:
            return self._column_names[section].capitalize()

        return None

    def set_entities(self, entities: list[Base]):
        """Set entities in model."""
        self.beginResetModel()
        self._entities = entities
        self.endResetModel()

    def add_entity(self, entity: Base):
        """Add entity in model."""
        self.beginInsertRows(
            qtc.QModelIndex(),
            len(self._entities),
            len(self._entities) + 1,
        )
        self._entities.append(entity)
        self.endInsertRows()

    def get_entity(self, code: str) -> Base | None:
        """Get entity by code."""
        try:
            entity = next(entity for entity in self._entities if entity.code == code)
        except StopIteration:
            return None

        return entity


class EntityTypeListModel(qtc.QAbstractListModel):
    """Entity table model object."""

    def __init__(self, entity_type: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self._entities: list[Base] = []

    @override
    def rowCount(self, parent=...):
        return len(self._entities)


    @override
    def data(self, index, role=...):
        if not index.isValid():
            return None
        entity = self._entities[index.row()]

        if role == qtc.Qt.DisplayRole:
            return getattr(entity, "name", None)
        if role == qtc.Qt.UserRole:
            return entity

        return None

    def set_entities(self, entities: list[Base]):
        """Set entities in model."""
        self.beginResetModel()
        self._entities = entities
        self.endResetModel()

    def add_entity(self, entity: Base):
        """Add entity in model."""
        self.beginInsertRows(
            qtc.QModelIndex(),
            len(self._entities),
            len(self._entities) + 1,
        )
        self._entities.append(entity)
        self.endInsertRows()

    def get_entity(self, code: str) -> Base | None:
        """Get entity by code."""
        try:
            entity = next(entity for entity in self._entities if entity.code == code)
        except StopIteration:
            return None

        return entity
