"""Asset type widget module."""

from __future__ import annotations

from Qt import QtCore as qtc
from Qt import QtGui as qtg
from Qt import QtWidgets as qtw

from atlas_const import c_db
from atlas_db.context import DbCommitContext
from atlas_db.context import DbQueryContext
from atlas_db.errors import DbPublishTypeAlreadyExistError
from atlas_db.models import Base
from atlas_db.models import PublishType
from atlas_db_ui.models.entity_type import EntityTypeTableModel


class AddPublishTypeDialog(qtw.QDialog):
    """Dialog to add Entity."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Add Publish type")

        # Widgets
        self.code = qtw.QLineEdit()
        publish_type_code_re = qtc.QRegExp(r"[a-z]+(?:_[a-z]+)*")
        publish_type_code_validator = qtg.QRegExpValidator(publish_type_code_re)
        self.code.setValidator(publish_type_code_validator)

        self.description = qtw.QLineEdit()
        file_desc_re = qtc.QRegExp(c_db.file_desc_grp)
        file_desc_validator = qtg.QRegExpValidator(file_desc_re)
        self.description.setValidator(file_desc_validator)

        self.extension = qtw.QLineEdit()
        extension_re = qtc.QRegExp(r"\.\w+")
        extension_validator = qtg.QRegExpValidator(extension_re)
        self.extension.setValidator(extension_validator)

        btn_ok = qtw.QPushButton("Ok")
        btn_cancel = qtw.QPushButton("Cancel")

        # Layout
        lay_main = qtw.QVBoxLayout(self)
        lay_lines = qtw.QFormLayout()

        lay_lines.addRow("Code:", self.code)
        lay_lines.addRow("Description:", self.description)
        lay_lines.addRow("Extension:", self.extension)

        lay_btn = qtw.QHBoxLayout()
        lay_btn.addStretch()
        lay_btn.addWidget(btn_ok)
        lay_btn.addWidget(btn_cancel)

        lay_main.addLayout(lay_lines)
        lay_main.addLayout(lay_btn)

        # Connections
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)


class PublishTypeTableWidget(qtw.QWidget):
    """Base entity widget."""

    EntityAdded = qtc.Signal(Base)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Publish Type")

        self._view = qtw.QTableView(self)
        self._model = EntityTypeTableModel(PublishType)

        self._view.setModel(self._model)

        btn_add = qtw.QPushButton("Add Publish Type")
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
        """Update asset type table content."""
        with DbQueryContext() as db:
            query = db.query(PublishType)
            entities = list(query)

        self.set_entities(entities)

    def add_entity(self):
        """Add entity to model."""
        dlg = AddPublishTypeDialog()
        if not dlg.exec():
            return

        code = dlg.code.text()
        desc = dlg.description.text()
        extension = dlg.extension.text()

        if not code or not desc or not extension:
            qtw.QMessageBox.critical(
                self,
                "Value Error",
                "Publish type code, name or extension can't be None",
            )
            raise ValueError("Publish type code, name or extension can't be None")

        # Ensure existing Asset type:
        with DbQueryContext() as db:
            publish_type = db.query(PublishType).where(PublishType.code == code).first()

        if publish_type is not None:
            msg = f"Publish type {code!r} already exists."
            qtw.QMessageBox.critical(
                self,
                "Publish Type already exists",
                msg,
            )
            raise DbPublishTypeAlreadyExistError(msg)

        with DbCommitContext() as db:
            new_entity = PublishType(code, desc, extension)
            db.add(new_entity)

        self._model.add_entity(new_entity)
        self.EntityAdded.emit(new_entity)
