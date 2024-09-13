import sys
from PyQt5 import QtWidgets, uic
from ui.seafoilUi import SeafoilUi
import os

if __name__ == "__main__":
    # get the folder of the current file
    directory = os.path.dirname(os.path.abspath(__file__))

    app = QtWidgets.QApplication(sys.argv)
    ui = SeafoilUi(directory)
    ui.show()
    sys.exit(app.exec_())