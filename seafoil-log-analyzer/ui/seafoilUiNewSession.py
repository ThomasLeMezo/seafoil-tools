import sys
from PyQt5 import QtWidgets, uic
import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout

from device.seafoil_new_session import SeafoilNewSession
from PyQt5.QtCore import QAbstractListModel, Qt

class TwoFieldInputDialog(QDialog):
    def __init__(self, windows_title, first_label_text, second_label_text):
        super().__init__()

        self.setWindowTitle(windows_title)

        # Layouts
        layout = QVBoxLayout()

        # First input field
        self.first_label = QLabel(first_label_text, self)
        self.first_input = QLineEdit(self)

        # Second input field
        self.second_label = QLabel(second_label_text, self)
        self.second_input = QLineEdit(self)

        # Ok and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Add widgets to the layout
        layout.addWidget(self.first_label)
        layout.addWidget(self.first_input)
        layout.addWidget(self.second_label)
        layout.addWidget(self.second_input)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals to slots
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_inputs(self):
        """Return the input values from the dialog."""
        return self.first_input.text(), self.second_input.text()

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

        self.comboBox_list = [self.ui.comboBox_board, self.ui.comboBox_sail, self.ui.comboBox_front_foil, self.ui.comboBox_stabilizer,
                              self.ui.comboBox_foil_mast, self.ui.comboBox_fuselage]

        self.model = DictListModel(self.sns.log_list)
        self.ui.listView_log.setModel(self.model)
        # Enable custom context menu on the QListView
        self.listView_log.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView_log.customContextMenuRequested.connect(self.show_context_menu)

        # Connect ok and cancel buttons
        # self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # connect the change rider index
        self.ui.comboBox_rider.currentIndexChanged.connect(self.on_change_rider_index)
        for i, comboBox in enumerate(self.comboBox_list):
            comboBox.currentIndexChanged.connect(lambda index, i=i: self.on_change_equipment_index(index, i))

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
        # Update the comboBox_configuration_list
        self.ui.comboBox_rider.clear()
        for rider in self.sns.rider_list:
            self.ui.comboBox_rider.addItem(rider['first_name'] + ' ' + rider['last_name'])
        # Add "New" at the end of the list
        self.ui.comboBox_rider.addItem("** New **")

        if self.sns.rider_current_index is not None:
            self.ui.comboBox_rider.setCurrentIndex(self.sns.rider_current_index)

        # Update the combo boxes
        for i, comboBox in enumerate(self.comboBox_list):
            comboBox.clear()
            for equipment in self.sns.se.equipment_data[i]:
                comboBox.addItem(self.sns.se.get_equipment_name(equipment, self.sns.se.equipment_names[i]))
            comboBox.addItem("** New **")

            if self.sns.equipment_current_index[i] is not None:
                comboBox.setCurrentIndex(self.sns.equipment_current_index[i])

    def update_configuration_from_ui(self):
        # Get the selected index
        index = self.ui.comboBox_rider.currentIndex()

        # If the selected index is the last one (New)
        if index == len(self.sns.rider_list):
            self.sns.rider_current_index = None
        else:
            self.sns.rider_current_index = index

        for i, comboBox in enumerate(self.comboBox_list):
            index = comboBox.currentIndex()
            if index == len(self.sns.se.equipment_data[i]):
                self.sns.equipment_current_index[i] = None
            else:
                self.sns.equipment_current_index[i] = index

    def on_change_rider_index(self, index):
        self.update_configuration_from_ui()
        # if the index is the last one (New)
        index = self.ui.comboBox_rider.currentIndex()
        if index >= len(self.sns.rider_list):
            # Open a dialog to add a new rider (First name, Last name)
            dialog = TwoFieldInputDialog("New Rider", "First Name", "Last Name")
            if dialog.exec_() == QDialog.Accepted:
                first_name, last_name = dialog.get_inputs()
                self.sns.add_rider(first_name, last_name)
            else:
                # Reset the index to the previous one
                self.sns.rider_current_index = 0
            self.update_ui_from_configuration()

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