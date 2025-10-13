"""Project widget module."""

from __future__ import annotations

import json

from Qt import QtCore as qtc
from Qt import QtGui as qtg
from Qt import QtWidgets as qtw

from atlas_const import c_db
from atlas_db.context import DbCommitContext
from atlas_db.models import Project
from atlas_db_ui.models.entity_type import EntityTypeListModel


class AddProjectDialog(qtw.QDialog):
    """Dialog to add project."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Add Project")

        # Widgets
        self.code = qtw.QLineEdit()
        project_code_re = qtc.QRegExp(c_db.project_code_str)
        code_validator = qtg.QRegExpValidator(project_code_re)
        self.code.setValidator(code_validator)

        self.name = qtw.QLineEdit()
        project_name_re = qtc.QRegExp("[a-zA-Z].+")
        name_validator = qtg.QRegExpValidator(project_name_re)
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



class ProjectEditableWidget(qtw.QWidget):
    """Project based widget to view project list and edit metadata."""

    ProjectEdited = qtc.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Widgets
        self._lst_projects = qtw.QListView(self)
        self._project_model = EntityTypeListModel(Project)
        self._lst_projects.setModel(self._project_model)
        btn_add_project = qtw.QPushButton("Add")

        self._btn_locked = qtw.QPushButton("Locked")
        self._btn_locked.setCheckable(True)
        self._btn_locked.setChecked(True)

        self._cbx_active = qtw.QCheckBox(self)
        self._cbx_active.setEnabled(False)

        self._lne_project_code = qtw.QLineEdit(self)
        self._lne_project_code.setEnabled(False)

        self._lne_project_name = qtw.QLineEdit(self)
        self._lne_project_name.setEnabled(False)

        self._txt_metadata = qtw.QTextEdit(self)
        self._txt_metadata.setEnabled(False)

        self._btn_save = qtw.QPushButton("Save")
        self._btn_save.setEnabled(False)

        self._btn_undo = qtw.QPushButton("Cancel edit")
        self._btn_undo.setEnabled(False)

        # Layout
        lay_main = qtw.QHBoxLayout(self)

        lay_projects_list = qtw.QVBoxLayout()

        lay_property = qtw.QVBoxLayout()
        lay_lines_prop = qtw.QFormLayout()
        lay_btn_prop = qtw.QHBoxLayout()

        lay_projects_list.addWidget(self._lst_projects)
        lay_projects_list.addWidget(btn_add_project)

        lay_lines_prop.addRow("Active:", self._cbx_active)
        lay_lines_prop.addRow("Code:", self._lne_project_code)
        lay_lines_prop.addRow("Display Name:", self._lne_project_name)

        lay_btn_prop.addWidget(self._btn_save)
        lay_btn_prop.addWidget(self._btn_undo)

        lay_main.addLayout(lay_projects_list)

        lay_property.addWidget(self._btn_locked)
        lay_property.addLayout(lay_lines_prop)
        lay_property.addWidget(self._txt_metadata)
        lay_property.addLayout(lay_btn_prop)

        lay_main.addLayout(lay_projects_list)
        lay_main.addLayout(lay_property)

        # Connections
        self._btn_locked.clicked.connect(self._on_btn_locked_clicked)
        self._lst_projects.clicked.connect(self._on_project_selected)
        self._btn_undo.clicked.connect(self._on_btn_cancel_clicked)
        self._btn_save.clicked.connect(self._on_btn_save_clicked)
        btn_add_project.clicked.connect(self._on_btn_add_clicked)

        # Initialisation

    def set_projects(self, projects: list[Project]):
        """Set projects list to model."""
        current_index = self._lst_projects.currentIndex()

        self._project_model.set_entities(projects)

        if current_index.isValid():
            self._lst_projects.setCurrentIndex(current_index)

    def _on_btn_locked_clicked(self):
        current_index = self._lst_projects.currentIndex()
        if not current_index.isValid():
            self._btn_locked.setChecked(True)
            return

        value = not self._btn_locked.isChecked()
        self._cbx_active.setEnabled(value)
        self._lne_project_code.setEnabled(value)
        self._lne_project_name.setEnabled(value)
        self._txt_metadata.setEnabled(value)
        self._btn_save.setEnabled(value)
        self._btn_undo.setEnabled(value)
        if not value:
            self._on_btn_cancel_clicked()

    def _on_project_selected(self, index: qtc.QModelIndex):
        if not index.isValid():
            return
        project: Project = self._lst_projects.model().data(index, role=qtc.Qt.UserRole)
        self._cbx_active.setChecked(project.active)
        self._lne_project_code.setText(project.code)
        self._lne_project_name.setText(project.name)
        metadata = project.meta
        self._txt_metadata.setText(json.dumps(metadata, indent=4))

        if self._btn_locked.isChecked():
            return

        self._btn_locked.setChecked(True)
        self._cbx_active.setEnabled(False)
        self._lne_project_code.setEnabled(False)
        self._lne_project_name.setEnabled(False)
        self._txt_metadata.setEnabled(False)
        self._btn_save.setEnabled(False)
        self._btn_undo.setEnabled(False)

    def _on_btn_cancel_clicked(self):
        index = self._lst_projects.currentIndex()
        self._on_project_selected(index)

    def _on_btn_save_clicked(self):
        code = self._lne_project_code.text()
        name = self._lne_project_name.text()
        metadata_text = self._txt_metadata.toPlainText()
        if not metadata_text:
            return

        metadata = eval(metadata_text)

        project = self._lst_projects.model().data(
            self._lst_projects.currentIndex(), role=qtc.Qt.UserRole
        )
        with DbCommitContext() as db:
            db.expire_on_commit = False
            db_project = db.query(Project).filter(Project.id == project.id).first()

            db_project.meta = metadata
            db_project.code = code
            db_project.name = name

        project.meta = metadata
        project.code = code
        project.name = name

        self.ProjectEdited.emit()
        self._btn_locked.setChecked(True)
        self._on_btn_locked_clicked()

    def _on_btn_add_clicked(self):
        dlg = AddProjectDialog()

        if not dlg.exec():
            return

        code = dlg.code.text()
        name = dlg.name.text()
        if not code or not name:
            return

        if self._project_model.get_entity(code):
            qtw.QMessageBox.critical(
                self,
                "Project already exists",
                f"Project {code!r} already exists in database.",
                qtw.QMessageBox.Ok,
            )
            return

        with DbCommitContext() as db:
            db.expire_on_commit = False
            project = Project(code=code, name=name, meta=c_db.MINIMAL_PROJECT_ENV)
            db.add(project)

        self._project_model.add_entity(project)
