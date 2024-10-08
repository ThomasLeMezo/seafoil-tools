import datetime
import sys
from PyQt5 import QtWidgets, uic
import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import QAbstractListModel, Qt, QDateTime

from .qgisUiLog import QgisUiLog
from ..device.seafoil_new_session import SeafoilNewSession
from .seafoilUi import upload_gpx
from .ui_utils import TwoFieldInputDialog
from .seafoilUiDownload import SeafoilUiDownload
from .seafoilUiSearchLog import SeafoilUiSearchLog


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

            rider = f"{val['rider_first_name']} {val['rider_last_name']}"
            name = val['name']

            # return a string representation of the key
            return f"{rider} - {name} - {type_str}"

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
    def __init__(self, session_id = None):
        super().__init__()

        self.sns = SeafoilNewSession(session_id)
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(self.directory + '/session.ui', self)

        self.comboBox_list = [self.ui.comboBox_board, self.ui.comboBox_sail, self.ui.comboBox_front_foil, self.ui.comboBox_stabilizer,
                              self.ui.comboBox_foil_mast, self.ui.comboBox_fuselage]

        self.model_link = DictListModel(self.sns.sl.logs)
        self.model_associated = DictListModel(self.sns.sl.logs_associated)
        self.ui.listView_log.setModel(self.model_link)
        self.ui.listView_log_associated.setModel(self.model_associated)
        # Enable custom context menu on the QListView
        self.listView_log.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView_log.customContextMenuRequested.connect(lambda position: self.show_context_menu(position, False))
        # Enable custom context menu on the QListView
        self.listView_log_associated.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView_log_associated.customContextMenuRequested.connect(lambda position: self.show_context_menu(position, True))

        # Enable double click to launch log
        self.listView_log.doubleClicked.connect(lambda index: self.open_log_from_list(index, False))
        self.listView_log_associated.doubleClicked.connect(lambda index: self.open_log_from_list(index, True))

        # connect the change rider index
        self.ui.comboBox_rider.currentIndexChanged.connect(self.on_change_rider_index)
        for i, comboBox in enumerate(self.comboBox_list):
            comboBox.currentIndexChanged.connect(lambda index, i=i: self.on_change_equipment_index(index, i))

        # connect pushButton_upload_gpx to the upload_gpx method
        self.ui.pushButton_upload_gpx.clicked.connect(lambda: self.on_upload_gpx_clicked(False))
        self.ui.pushButton_upload_gpx_associated.clicked.connect(lambda: self.on_upload_gpx_clicked(True))

        # connect pushButton_upload_log to the upload_log method
        self.ui.pushButton_upload_log.clicked.connect(self.on_upload_log_clicked)

        # connect pushButton_search_log to the search_log method
        self.ui.pushButton_search_log.clicked.connect(lambda: self.on_search_log_list(False))
        self.ui.pushButton_search_log_associated.clicked.connect(lambda: self.on_search_log_list(True))

        # Connect ok and cancel buttons
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.update_ui_from_configuration()

    def open_log_from_list(self, index, is_associated=False):
        # Get the row of the item and retrieve the value of the id column
        self.sns.sl.open_log_from_index(index.row(), is_associated)

    def on_upload_log_clicked(self):
        download = SeafoilUiDownload()
        download.exec_()

        # Get the list of logs to add
        log_list_id = download.log_downloaded

        del download

        for db_id in log_list_id:
            self.sns.add_log_to_list(db_id)
        self.update_ui_from_configuration()

    def on_search_log_list(self, is_associated=False):
        # Open the search log dialog
        self.update_configuration_from_ui()

        search_log = SeafoilUiSearchLog(only_unlinked=(not is_associated))
        search_log.exec_()

        # Get the list of logs to add
        log_list_id = search_log.selected_logs
        for db_id in log_list_id:
            self.sns.add_log_to_list(db_id, is_associated)
        self.update_ui_from_configuration()

    def accept(self):
        # if there is no log, issue a msg error box
        if self.sns.sl.is_empty():
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("No log in the list")
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        self.update_configuration_from_ui()
        self.sns.save()
        super().accept()

    def on_upload_gpx_clicked(self, is_associated=False):
        # Call the upload_gpx function from seafoilUi.py
        list_added = upload_gpx(self, self.sns.sl)
        if list_added is None:
            return
        for db_id in list_added:
            self.sns.add_log_to_list(db_id, is_associated)
        self.update_ui_from_configuration()

    def on_change_equipment_index(self, index, equipment_type):
        self.update_configuration_from_ui()
        # if the index is the last one (New)
        if index >= len(self.sns.se.equipment_data[equipment_type]):
            from ui.seafoilUi import new_equipment_dialog_box
            if new_equipment_dialog_box(self.ui, self.sns.se, self.sns.se.equipment_names[equipment_type],None, True):
                self.sns.update_lists()
                self.update_ui_from_configuration()
                self.comboBox_list[equipment_type].setCurrentIndex(len(self.sns.se.equipment_data[equipment_type]) - 1)

    # Update ui from rider list
    def update_ui_from_configuration(self):
        self.sns.compute_times()
        self.model_link.update_data(self.sns.sl.logs)
        self.model_associated.update_data(self.sns.sl.logs_associated)

        # Update the comboBox_configuration_list
        # Desactivate the signal
        self.ui.comboBox_rider.currentIndexChanged.disconnect()
        self.ui.comboBox_rider.clear()
        for rider in self.sns.rider_list:
            self.ui.comboBox_rider.addItem(rider['first_name'] + ' ' + rider['last_name'])
        # Add "New" at the end of the list
        self.ui.comboBox_rider.addItem("** New **")
        # Reactivate the signal

        if self.sns.rider_current_index is not None:
            self.ui.comboBox_rider.setCurrentIndex(self.sns.rider_current_index)
        self.ui.comboBox_rider.currentIndexChanged.connect(self.on_change_rider_index)

        # Update the combo boxes
        for i, comboBox in enumerate(self.comboBox_list):
            comboBox.currentIndexChanged.disconnect()
            comboBox.clear()
            for equipment in self.sns.se.equipment_data[i]:
                comboBox.addItem(self.sns.se.get_equipment_name(equipment, self.sns.se.equipment_names[i]))
            comboBox.addItem("** New **")

            if self.sns.se.equipment_current_index[i] is not None:
                comboBox.setCurrentIndex(self.sns.se.equipment_current_index[i])
            comboBox.currentIndexChanged.connect(lambda index, i=i: self.on_change_equipment_index(index, i))

        # Update rake
        # Desactivate all signals
        self.ui.doubleSpinBox_rake.setValue(self.sns.se.rake)
        # Update stab shim
        self.ui.doubleSpinBox_stab_shim.setValue(self.sns.se.stab_shim)
        # Update mast foot position
        self.ui.doubleSpinBox_mast_foot_position.setValue(self.sns.se.mast_foot_position)

        # Update label_starting_date
        if self.sns.session['start_date'] is not None:
            self.ui.label_starting_date.setText(QDateTime.fromSecsSinceEpoch(int(self.sns.session['start_date'])).toString('yyyy-MM-dd hh:mm:ss'))

        # Update label_ending_date
        if self.sns.session['end_date'] is not None:
            self.ui.label_ending_date.setText(QDateTime.fromSecsSinceEpoch(int(self.sns.session['end_date'])).toString('yyyy-MM-dd hh:mm:ss'))

        if self.sns.session['duration'] is not None:
            self.ui.label_duration.setText(str(datetime.timedelta(seconds=self.sns.session['duration'])))

        self.ui.plainTextEdit_comment.setPlainText(self.sns.session['comment'])

    def update_configuration_from_ui(self):
        # Get the selected index
        index = self.ui.comboBox_rider.currentIndex()

        self.sns.session['comment'] = self.ui.plainTextEdit_comment.toPlainText()

        # If the selected index is the last one (New)
        if index == len(self.sns.rider_list):
            self.sns.rider_current_index = None
        else:
            self.sns.rider_current_index = index

        for i, comboBox in enumerate(self.comboBox_list):
            index = comboBox.currentIndex()
            if index == len(self.sns.se.equipment_data[i]):
                self.sns.se.equipment_current_index[i] = None
            else:
                self.sns.se.equipment_current_index[i] = index

        # Update rake
        self.sns.se.rake = self.ui.doubleSpinBox_rake.value()
        # Update stab shim
        self.sns.se.stab_shim = self.ui.doubleSpinBox_stab_shim.value()
        # Update mast foot position
        self.sns.se.mast_foot_position = self.ui.doubleSpinBox_mast_foot_position.value()

    def on_change_rider_index(self, index):
        self.update_configuration_from_ui()
        # if the index is the last one (New)
        index = self.ui.comboBox_rider.currentIndex()
        if index >= len(self.sns.rider_list):
            # Open a dialog to add a new rider (First name, Last name)
            dialog = TwoFieldInputDialog("New Rider", "First Name", "Last Name")
            if dialog.exec_() == QDialog.Accepted:
                first_name, last_name = dialog.get_inputs()
                self.sns.add_rider(first_name, last_name, True)
            else:
                # Reset the index to the previous one
                self.sns.rider_current_index = 0
            self.update_ui_from_configuration()

    def show_context_menu(self, position, is_associated=False):
        # Create the context menu
        menu = QtWidgets.QMenu(self)
        display_action = menu.addAction("Display on map")
        remove_action = menu.addAction("Remove Item")

        # Execute the menu and get the selected action
        action = menu.exec_(self.listView_log.mapToGlobal(position) if not is_associated else self.listView_log_associated.mapToGlobal(position))

        if action == remove_action:
            self.remove_selected_item(is_associated)
        elif action == display_action:
            self.display_selected_item(is_associated)

    def remove_selected_item(self, is_associated=False):
        # Get the currently selected index
        index = self.listView_log.currentIndex() if not is_associated else self.listView_log_associated.currentIndex()

        if not index.isValid():
            return
        else:
            self.sns.remove_log(index.row(), is_associated)

        # Update the model with the modified dictionary
        self.update_ui_from_configuration()

    def display_selected_item(self, is_associated=False):
        # Get the currently selected index
        index = self.listView_log.currentIndex() if not is_associated else self.listView_log_associated.currentIndex()

        if not index.isValid():
            return
        else:
            seafoil_bag, log = self.sns.sl.get_seafoil_bag_from_index(index.row(), is_associated)
            QgisUiLog(seafoil_bag, log) # Create a new QgisUiLog object

    def update_log_list(self):
        # Clear the list view
        self.model_link.update_data(self.sns.log_list)