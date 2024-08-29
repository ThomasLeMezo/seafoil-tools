import sys
from PyQt5 import QtWidgets, uic
from .seafoilUiSession import SeafoilUiSession
import os

class SeafoilUi(QtWidgets.QMainWindow):
    def __init__(self, seafoil_directory):
        super().__init__()
        # Get directory of the current file
        self.seafoil_directory = seafoil_directory
        self.ui = uic.loadUi(self.seafoil_directory + '/ui/main_window.ui', self)

        # connect the menu/action_new_session to function on_new_session_clicked
        self.ui.action_new_session.triggered.connect(self.on_new_session_clicked)

    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        self.session = SeafoilUiSession(self.seafoil_directory)
        self.session.exec_()


# Test the class
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = SeafoilUi()
    ui.show()
    sys.exit(app.exec_())