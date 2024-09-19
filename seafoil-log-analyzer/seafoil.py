import sys
from PyQt5 import QtWidgets, uic
from ui.seafoilUi import SeafoilUi
import os

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = SeafoilUi()
    ui.show()
    sys.exit(app.exec_())