from __future__ import annotations

from typing import Any
from typing import override

from Qt import QtCore as qtc
from sqlalchemy import select
from sqlalchemy import text

from atlas_db.context import DbCommitContext
from atlas_db.context import DbQueryContext
from atlas_db.models import update_model_value


class EntityTypeTableModel(qtc.QAbstractTableModel):
    """Entity table model object."""

    ActiveRole = qtc.Qt.UserRole + 1

    SetActive = qtc.Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entities: list[dict[str, Any]] = []
        self._column_names: list[str] = []

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
        column_name = self._column_names[index.column()]
        value = entity.get(column_name)

        if (
            role == qtc.Qt.DisplayRole
            and "active" not in column_name
            and not isinstance(value, bool)
        ):
            return str(value) if value is not None else ""

        if (
            role == qtc.Qt.CheckStateRole
            and "active" in column_name
            and isinstance(value, bool)
        ):
            return qtc.Qt.Checked if value else qtc.Qt.Unchecked

        if role == qtc.Qt.UserRole:
            return value

        return None

    @override
    def setData(self, index, value, role=...):
        if not index.isValid():
            return False

        entity = self._entities[index.row()]
        current_col_index = index.column()
        current_col_value = self._column_names[current_col_index]

        if role == qtc.Qt.CheckStateRole and "active" in current_col_value:
            active_value = entity.get(current_col_value)
            table_name, column_name = current_col_value.split(".")
            entity_id = entity.get(f"{table_name}.id")

            if entity_id is None:
                return None

            update_model_value(
                table_name,
                entity_id,
                column_name,
                not active_value
            )

            for i, entity in enumerate(self._entities):

                filter_entity_id = entity[f"{table_name}.id"]
                if filter_entity_id == entity_id:
                    entity[current_col_value] = not active_value
                    self.dataChanged.emit(
                        self.index(i, current_col_index),
                        self.index(self.rowCount() -1, current_col_index),
                        [int(qtc.Qt.CheckStateRole)]
                    )
            return True

        return False

    @override
    def flags(self, index):
        flags = super().flags(index)
        col = index.column()

        if "active" in self._column_names[col]:
            flags |= qtc.Qt.ItemIsUserCheckable

        return flags

    @override
    def headerData(self, section, orientation, role=...):
        if role == qtc.Qt.DisplayRole and orientation == qtc.Qt.Horizontal:
            return self._column_names[section].capitalize()

        return None

    def set_entities(self, entities: list[dict]):
        """Set entities in model."""
        self.beginResetModel()
        self._column_names = list({h: True for data in entities for h in data}.keys())
        self._entities = entities
        self.endResetModel()

    def add_entity(self, entity: dict[str, Any]):
        """Add entity in model."""
        self.beginInsertRows(
            qtc.QModelIndex(),
            len(self._entities),
            len(self._entities) + 1,
        )
        self._entities.append(entity)
        self.endInsertRows()

    def get_entity(self, code: str) -> dict[str, Any] | None:
        """Get entity by code."""
        try:
            entity = next(entity for entity in self._entities if entity["code"] == code)
        except StopIteration:
            return None

        return entity
