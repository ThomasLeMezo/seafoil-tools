import sys
from PyQt5 import QtWidgets, uic
import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QApplication


class SeafoilUiProcess(QtWidgets.QDialog):
    def __init__(self, file_nb=0, total_file_nb=0):
        super().__init__()
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(self.directory + '/process.ui', self)

        # Set title of the window
        self.update_title(file_nb, total_file_nb)

    def update_ui(self, pourcentage, message):
        # Update the progress bar
        self.ui.progressBar.setValue(pourcentage)
        # Update the label
        self.ui.label.setText(message)
        QApplication.processEvents()

    def update_title(self, file_nb, total_file_nb):
        self.setWindowTitle(f"Processing {file_nb} of {total_file_nb} files")

