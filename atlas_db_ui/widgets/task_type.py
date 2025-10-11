"""Task type widget module."""

from __future__ import annotations

from Qt import QtCore as qtc
from Qt import QtGui as qtg
from Qt import QtWidgets as qtw

from atlas_const import c_db
from atlas_db.context import DbCommitContext
from atlas_db.context import DbQueryContext
from atlas_db.errors import DbTaskTypeAlreadyExistError
from atlas_db.models import Base
from atlas_db.models import TaskType
from atlas_db_ui.models.entity_type import EntityTypeTableModel


class AddTaskTypeDialog(qtw.QDialog):
    """Dialog to add Entity."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Add Task Type")

        # Widgets
        self.code = qtw.QLineEdit()
        asset_type_code_re = qtc.QRegExp(c_db.asset_type_code_str)
        code_validator = qtg.QRegExpValidator(asset_type_code_re)
        self.code.setValidator(code_validator)

        self.name = qtw.QLineEdit()
        asset_type_name_re = qtc.QRegExp("[a-z]+")
        name_validator = qtg.QRegExpValidator(asset_type_name_re)
        self.name.setValidator(name_validator)

        btn_ok = qtw.QPushButton("Ok")
        btn_cancel = qtw.QPushButton("Cancel")

        # Layout
        lay_main = qtw.QVBoxLayout(self)
        lay_lines = qtw.QFormLayout()

        lay_lines.addRow("Code:", self.code)
        lay_lines.addRow("Name:", self.name)

        lay_btn = qtw.QHBoxLayout()
        lay_btn.addStretch()
        lay_btn.addWidget(btn_ok)
        lay_btn.addWidget(btn_cancel)

        lay_main.addLayout(lay_lines)
        lay_main.addLayout(lay_btn)

        # Connections
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)


class TaskTypeTableWidget(qtw.QWidget):
    """Base entity widget."""

    EntityAdded = qtc.Signal(Base)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Task Type")

        self._view = qtw.QTableView(self)
        self._model = EntityTypeTableModel(TaskType)

        self._view.setModel(self._model)

        btn_add = qtw.QPushButton("Add Task Type")
        btn_refresh = qtw.QPushButton("Refresh")

        lay_main = qtw.QVBoxLayout(self)
        lay_main.setContentsMargins(0, 0, 0, 0)

        lay_btn = qtw.QHBoxLayout()
        lay_btn.addWidget(btn_add)
        lay_btn.addWidget(btn_refresh)

        lay_main.addWidget(self._view)
        lay_main.addLayout(lay_btn)

        btn_add.clicked.connect(self.add_entity)
        btn_refresh.clicked.connect(self.refresh)

        # Init
        self.refresh()

    def set_entities(self, entities: list[Base]):
        """Set entities to model."""
        self._model.set_entities(entities)

    def refresh(self):
        """Update task type table content."""
        with DbQueryContext() as db:
            query = db.query(TaskType)
            entities = list(query)

        self.set_entities(entities)

    def add_entity(self):
        """Add entity to model."""
        dlg = AddTaskTypeDialog()
        if not dlg.exec():
            return

        code = dlg.code.text()
        name = dlg.name.text()

        if not code or not name:
            qtw.QMessageBox.critical(
                self,
                "Value Error",
                "Task type code and name can't be None",
            )
            raise ValueError("Task type code and name can't be None")

        # Ensure existing Task type:
        with DbQueryContext() as db:
            asset_type = db.query(TaskType).where(TaskType.code == code).first()

        if asset_type is not None:
            msg = f"Task type {code!r} already exists."
            qtw.QMessageBox.critical(
                self,
                "Task Type already exists",
                msg,
            )
            raise DbTaskTypeAlreadyExistError(msg)

        with DbCommitContext() as db:
            db.expire_on_commit = False
            new_entity = TaskType(code, name)
            db.add(new_entity)

        self._model.add_entity(new_entity)
        self.EntityAdded.emit(new_entity)
