import sys
from PyQt5 import QtWidgets, uic
import os
from device.seafoil_new_session import SeafoilNewSession
from PyQt5.QtCore import QAbstractListModel, Qt

# Custom Model Class Based on a Dictionary
class DictListModel(QAbstractListModel):
    def __init__(self, data_dict=None):
        super().__init__()
        # Initialize with a dictionary
        self._data = data_dict if data_dict else {}

    def rowCount(self, parent=None):
        # Return the number of rows (keys) in the dictionary
        return len(self._data)

    def data(self, index, role):
        # Return the data to be displayed
        if role == Qt.DisplayRole:
            # Return the key corresponding to the row index
            val = self._data[index.row()]

            type_str = ''
            if val['type'] == 0:
                type_str = 'rosbag'
            elif val['type'] == 1:
                type_str = 'gpx'

            # return a string representation of the key
            return str(val['name']) + ' - ' + type_str

    def roleNames(self):
        # Optional: Define custom roles if needed
        roles = super().roleNames()
        roles[Qt.DisplayRole] = b'display'
        return roles

    # Optional: Method to update data
    def update_data(self, new_data):
        # Update the dictionary and refresh the view
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class SeafoilUiNewSession(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.sns = SeafoilNewSession()
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(self.directory + '/session.ui', self)



        self.model = DictListModel(self.sns.log_list)
        self.ui.listView_log.setModel(self.model)
        # Enable custom context menu on the QListView
        self.listView_log.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView_log.customContextMenuRequested.connect(self.show_context_menu)

        # Connect the buttons to the functions
        # self.ui.pushButton_upload_log.clicked.connect(self.on_upload_log_clicked)
        self.ui.pushButton_upload_gpx.clicked.connect(self.on_import_gpx_clicked)
        # self.ui.pushButton_search_log.clicked.connect(self.on_search_log_clicked)

        # Connect ok and cancel buttons
        # self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    # Import a gpx file
    def on_import_gpx_clicked(self):
        # Open file dialog to select a gpx file
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '', 'GPX files (*.gpx)')

        # If a file is selected
        if file_path:
            if self.sns.import_gpx(file_path):
                QtWidgets.QMessageBox.information(self, 'Success', 'GPX file added successfully')
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'An error occurred while importing the GPX file')

            # Update the list view
            self.update_log_list()


    def show_context_menu(self, position):
        # Create the context menu
        menu = QtWidgets.QMenu(self)
        remove_action = menu.addAction("Remove Item")

        # Execute the menu and get the selected action
        action = menu.exec_(self.listView_log.mapToGlobal(position))

        if action == remove_action:
            self.remove_selected_item()

    def remove_selected_item(self):
        # Get the currently selected index
        index = self.listView_log.currentIndex()

        if not index.isValid():
            return
        else:
            self.sns.remove_log(index.row())

        # Update the model with the modified dictionary
        self.model.update_data(self.log_list)

    def update_log_list(self):
        # Clear the list view
        self.model.update_data(self.sns.log_list)

    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        print("Button clicked!")