"""Entity model module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import override

from Qt import QtCore as qtc


if TYPE_CHECKING:
    from atlas_db.models import Base


ActiveRole = qtc.Qt.UserRole + 1


class EntityTableModel(qtc.QAbstractTableModel):
    """Entity table model object."""

    def __init__(self, entity_type: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self._entities = []
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

        if role == qtc.Qt.DisplayRole:
            return getattr(entity, column_name, None)
        if role == qtc.Qt.UserRole:
            return entity

        if role == qtc.Qt.TextAlignmentRole:
            return int(qtc.Qt.AlignCenter)

        return None

    @override
    def setData(self, index, value, role = ...):
        if not index.isValid():
            return False

        entity = self._entities[index.row()]

        if role == ActiveRole:
