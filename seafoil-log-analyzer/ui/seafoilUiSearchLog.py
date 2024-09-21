import sys
from PyQt5 import QtWidgets, uic
import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout

from ..device.seafoil_log import SeafoilLog
from .seafoilUiLogTableWidget import SeafoilUiLogTableWidget


class SeafoilUiSearchLog(QtWidgets.QDialog):
    def __init__(self, only_unlinked=True):
        super().__init__()
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(self.directory + '/search_log.ui', self)
        self.sl = SeafoilLog(load_only_unlinked=only_unlinked)

        self.seafoil_log_table_widget = SeafoilUiLogTableWidget(None, self.ui.tableWidget_logs, self.sl, False, False)

        # double click on a row is accepted
        self.ui.tableWidget_logs.itemDoubleClicked.connect(self.accept)

        # List of selected logs
        self.selected_logs = []

    def accept(self):
        # Get the row of the item and retrieve the value of the id column
        self.selected_logs = self.seafoil_log_table_widget.get_list_of_selected_logs()
        self.close()

