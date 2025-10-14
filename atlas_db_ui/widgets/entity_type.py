"""Entity type widget module."""

from __future__ import annotations

import sys

from typing import Any
from typing import override

from Qt import QtCore as qtc
from Qt import QtWidgets as qtw
from sqlalchemy import inspect

from atlas_db.context import DbCommitContext
from atlas_db.context import DbQueryContext
from atlas_db.models import Base
from atlas_db.models import Project
from atlas_db_ui.models.entity_type import EntityTypeTableModel
from atlas_db_ui.widgets.asset_type import AssetTypeTableWidget
from atlas_db_ui.widgets.projects_create import ProjectEditableWidget
from atlas_db_ui.widgets.publish_type import PublishTypeTableWidget
from atlas_db_ui.widgets.task_type import TaskTypeTableWidget


class EntityAddDialog(qtw.QDialog):
    """Dialog to add Entity."""

    def __init__(self, entity_type: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self.kwargs: dict[str, Any] = {}

        # Widgets
        lay_options = qtw.QFormLayout()
        self._column_names = self._entity_type.__table__.columns.keys()
        self._widget_by_names = {}

        # Create dynamically widgets by columns names
        mapper = inspect(entity_type)
        for name in self._column_names:
            col = mapper.columns[name]
            col_type = col.type.python_type
            if col_type is not str:
                continue
            option_widget = qtw.QLineEdit(self)
            self._widget_by_names[name] = option_widget
            lay_options.addRow(f"{name.capitalize()} :", option_widget)

        btn_ok = qtw.QPushButton("Ok")
        btn_cancel = qtw.QPushButton("Cancel")

        # Layouts
        lay_main = qtw.QVBoxLayout(self)

        lay_btn = qtw.QHBoxLayout()
        lay_btn.addStretch()
        lay_btn.addWidget(btn_ok)
        lay_btn.addWidget(btn_cancel)

        lay_main.addLayout(lay_options)
        lay_main.addLayout(lay_btn)

        # Connections
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

    @override
    def accept(self):
        for key, value in self._widget_by_names.items():
            self.kwargs[key] = value.text()
        super().accept()


class EntityTableWidget(qtw.QWidget):
    """Base entity widget."""

    EntityAdded = qtc.Signal(Base)

    def __init__(self, entity_type: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self.setWindowTitle(f"{self._entity_type.__name__}")

        self._view = qtw.QTableView(self)
        self._model = EntityTypeTableModel(entity_type)

        self._view.setModel(self._model)

        btn_add = qtw.QPushButton(f"Add {entity_type.__name__}")

        lay_main = qtw.QVBoxLayout(self)
        lay_main.setContentsMargins(0, 0, 0, 0)
        lay_main.addWidget(self._view)
        lay_main.addWidget(btn_add)

        btn_add.clicked.connect(self.add_entity)

        with DbQueryContext() as db:
            query = db.query(entity_type)
            entities = list(query)

        self.set_entities(entities)

    def set_entities(self, entities: list[Base]):
        """Set entities to model."""
        self._model.set_entities(entities)

    def add_entity(self):
        """Add entity to model."""
        dlg = EntityAddDialog(self._entity_type)
        if not dlg.exec():
            return

        with DbCommitContext() as db:
            db.expire_on_commit = False
            new_entity = self._entity_type(**dlg.kwargs)
            db.add(new_entity)

        self._model.add_entity(new_entity)


class EntityTypesWidget(qtw.QWidget):
    """Global entity types widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Entity Type Manager")
        self.setWindowFlag(qtc.Qt.Window)

        self._tab = qtw.QTabWidget(self)
        self._project = ProjectEditableWidget()
        self._asset_type = AssetTypeTableWidget()
        self._task_type = TaskTypeTableWidget()
        self._publish_type = PublishTypeTableWidget()

        self._tab.addTab(self._project, "Project")
        self._tab.addTab(self._asset_type, "Asset Type")
        self._tab.addTab(self._task_type, "Task Type")
        self._tab.addTab(self._publish_type, "Publish Type")

        lay_main = qtw.QVBoxLayout(self)
        lay_main.addWidget(self._tab)

        with DbQueryContext() as db:
            project_query = db.query(Project)
            projects = list(project_query)

        self._project.set_projects(projects)



if __name__ == "__main__":
    qt_app = qtw.QApplication(sys.argv)
    widget = EntityTypesWidget()
    widget.show()
    qt_app.exec()
