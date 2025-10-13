"""Main window module."""

from __future__ import annotations

import sys

from Qt import QtWidgets as qtw

from atlas_db import __version__

class AtlasHelp(qtw.QDialog):
    """Help window."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Help")

        lbl_python_version = qtw.QLabel(
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        lbl_version = qtw.QLabel(str(__version__))
        btn_ok = qtw.QPushButton("Ok")


        lay_main = qtw.QFormLayout(self)
        lay_main.addRow("Python version:", lbl_python_version)
        lay_main.addRow("Atlas version:", lbl_version)
        lay_main.addWidget(btn_ok)

        btn_ok.clicked.connect(self.accept)



class AtlasMainWindow(qtw.QMainWindow):
    """Atlas main window."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("FOST Atlas")

        self.menu = qtw.QMenuBar(self)
        act_help = qtw.QAction("Help", self)
        act_help.triggered.connect(self._help_menu)

        self.setMenuBar(self.menu)

        self.menu.addAction(act_help)

    def _help_menu(self):
        dlg = AtlasHelp()
        dlg.exec()





if __name__ == "__main__":
    qt_app = qtw.QApplication(sys.argv)
    widget = AtlasMainWindow()
    widget.show()
    qt_app.exec()
