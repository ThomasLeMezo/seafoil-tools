import sys
from PyQt5 import QtWidgets, uic
import os
import gpxpy
from db.seafoil_db import SeafoilDB
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

            # return a string representation of the key
            return str(val['name'])

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


class SeafoilUiSession(QtWidgets.QDialog):
    def __init__(self, seafoil_directory):
        super().__init__()
        self.seafoil_directory = seafoil_directory
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(self.directory + '/session.ui', self)
        self.sdb = SeafoilDB()

        self.log_list = []
        self.model = DictListModel(self.log_list)
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
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '', 'GPX files (*.gpx)')

        # If a file is selected
        if file_name:
            # Try to parse the file
            try:
                gpx_file = open(file_name, 'r')
                gpx = gpxpy.parse(gpx_file)

                # Get the starting time of the gpx file
                starting_time = gpx.tracks[0].segments[0].points[0].time


                # Determine the year, month, day and copy the file in the data folder
                year = starting_time.year
                month = starting_time.month
                day = starting_time.day
                log_folder = '/data/log/' + str(year) + '/' + str(month) + '/' + str(day) + '/'
                folder = self.seafoil_directory + log_folder
                os.makedirs(folder, exist_ok=True)
                gpx_file_name = folder + os.path.basename(file_name)

                # Insert the gpx file in the database
                id, exist = self.sdb.insert_gpx(os.path.basename(file_name), log_folder, starting_time)

                if exist:
                    # Open dialog error
                    QtWidgets.QMessageBox.warning(self, 'Information', 'This GPX file is already imported')
                else:
                    os.system('cp ' + file_name + ' ' + gpx_file_name)


                # Add the gpx file in the list if it is not already in the list
                for log in self.log_list:
                    if log['name'] == os.path.basename(file_name):
                        # Open dialog error
                        QtWidgets.QMessageBox.warning(self, 'Information', 'This GPX file is already in the list')
                        return False

                self.log_list.append({'name': os.path.basename(file_name), 'timestamp': starting_time, 'type': 'gpx', 'db_id': id})

                # Update the list view
                self.update_log_list()

                # Open dialog ok for success
                QtWidgets.QMessageBox.information(self, 'Success', 'GPX file added successfully')

                return True

            except Exception as e:
                print(f"An error occurred: {e}")

                # Open dialog error
                QtWidgets.QMessageBox.critical(self, 'Error', 'An error occurred while importing the GPX file')

                return False
        return False

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

        # Remove the selected item from the dictionary
        if index.row() < len(self.log_list):
            # delete the item from the dictionary at position index.row()
            del self.log_list[index.row()]

        # Update the model with the modified dictionary
        self.model.update_data(self.log_list)

    def update_log_list(self):
        # Clear the list view
        self.model.update_data(self.log_list)

    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        print("Button clicked!")