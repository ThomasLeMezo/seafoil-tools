import sys
from PyQt5 import QtWidgets, uic
from .seafoilUiSession import SeafoilUiSession
from device.seafoil_configuration import SeafoilConfiguration
import os

class SeafoilUi(QtWidgets.QMainWindow):
    def __init__(self, seafoil_directory):
        super().__init__()

        # Conversion kt to m/s
        self.kt_to_ms = 0.514444
        self.ms_to_kt = 1.0 / self.kt_to_ms

        # Get directory of the current file
        self.seafoil_directory = seafoil_directory
        self.ui = uic.loadUi(self.seafoil_directory + '/ui/main_window.ui', self)
        self.configuration_ui_was_connected = False

        # connect the menu/action_new_session to function on_new_session_clicked
        self.ui.action_new_session.triggered.connect(self.on_new_session_clicked)

        # connect the pushButton_send_config to function on_send_config_clicked
        self.ui.pushButton_send_config.clicked.connect(self.on_send_config_clicked)

        # connect the pushButton_remove_config to function on_remove_config_clicked
        self.ui.pushButton_remove_config.clicked.connect(self.on_remove_config_clicked)

        # Seafoil Configuration
        self.sc = SeafoilConfiguration()
        self.update_ui_from_configuration()

        self.connect_value_changed_configuration(True)

    def connect_value_changed_configuration(self, enable):
        if enable and not self.configuration_ui_was_connected:
            self.ui.doubleSpinBox_v500.valueChanged.connect(self.on_change_configuration)
            self.ui.doubleSpinBox_v1850.valueChanged.connect(self.on_change_configuration)
            self.ui.checkBox_enable_heading.stateChanged.connect(self.on_change_configuration)
            self.ui.spinBox_voice_interval.valueChanged.connect(self.on_change_configuration)
            self.ui.doubleSpinBox_height_too_high.valueChanged.connect(self.on_change_configuration)
            self.ui.doubleSpinBox_height_high.valueChanged.connect(self.on_change_configuration)
            self.ui.comboBox_configuration_list.currentIndexChanged.connect(self.on_change_index_configuration)
            self.configuration_ui_was_connected = True
        elif not enable and self.configuration_ui_was_connected:
            self.ui.doubleSpinBox_v500.valueChanged.disconnect(self.on_change_configuration)
            self.ui.doubleSpinBox_v1850.valueChanged.disconnect(self.on_change_configuration)
            self.ui.checkBox_enable_heading.stateChanged.disconnect(self.on_change_configuration)
            self.ui.spinBox_voice_interval.valueChanged.disconnect(self.on_change_configuration)
            self.ui.doubleSpinBox_height_too_high.valueChanged.disconnect(self.on_change_configuration)
            self.ui.doubleSpinBox_height_high.valueChanged.disconnect(self.on_change_configuration)
            self.ui.comboBox_configuration_list.currentIndexChanged.disconnect(self.on_change_index_configuration)
            self.configuration_ui_was_connected = False

    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        session = SeafoilUiSession(self.seafoil_directory)
        session.exec_()

    def update_ui_from_configuration(self):
        self.connect_value_changed_configuration(False)
        self.ui.doubleSpinBox_v500.setValue(self.sc.v500)
        self.ui.doubleSpinBox_v1850.setValue(self.sc.v1850)
        self.ui.checkBox_enable_heading.setChecked(self.sc.heading_enable)
        self.ui.spinBox_voice_interval.setValue(self.sc.voice_interval)
        self.ui.doubleSpinBox_height_too_high.setValue(self.sc.height_too_high)
        self.ui.doubleSpinBox_height_high.setValue(self.sc.height_high)

        # Update the comboBox_configuration_list
        self.ui.comboBox_configuration_list.clear()
        for config in self.sc.configuration_list:
            self.ui.comboBox_configuration_list.addItem(config['name'])
        # Add "New" at the end of the list
        self.ui.comboBox_configuration_list.addItem("** New **")

        if self.sc.current_index is not None:
            self.ui.comboBox_configuration_list.setCurrentIndex(self.sc.current_index)

        self.connect_value_changed_configuration(True)

    def update_configuration_from_ui(self):
        self.sc.v500 = self.ui.doubleSpinBox_v500.value()
        self.sc.v1850 = self.ui.doubleSpinBox_v1850.value()
        self.sc.heading_enable = self.ui.checkBox_enable_heading.isChecked()
        self.sc.voice_interval = self.ui.spinBox_voice_interval.value()
        self.sc.height_too_high = self.ui.doubleSpinBox_height_too_high.value()
        self.sc.height_high = self.ui.doubleSpinBox_height_high.value()

    def on_change_configuration(self):
        # Set the minimum of doubleSpinBox_height_too_high to doubleSpinBox_height_high
        self.ui.doubleSpinBox_height_too_high.setMinimum(self.ui.doubleSpinBox_height_high.value())
        self.update_configuration_from_ui()
        self.sc.db_save_configuration(is_new=False)

    def on_change_index_configuration(self):
        self.update_configuration_from_ui()

        index = self.ui.comboBox_configuration_list.currentIndex()
        if index >= len(self.sc.configuration_list):
            text, ok = QtWidgets.QInputDialog.getText(self, 'Save configuration', 'Enter the name of the configuration:')
            if ok:
                self.sc.db_save_configuration(text, is_new=True)

        if self.sc.update_index(index):
            self.connect_value_changed_configuration(False)
            self.update_ui_from_configuration()
            self.connect_value_changed_configuration(True)

    def on_remove_config_clicked(self):
        self.sc.db_remove_configuration()
        self.update_ui_from_configuration()

    def on_send_config_clicked(self):
        self.update_configuration_from_ui()

        if self.sc.upload_configuration():
            # Dialog box to confirm the configuration was sent
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("The configuration was sent successfully.")
            msg.setWindowTitle("Information")
            msg.exec_()
        else:
            # Dialog box to confirm the configuration was not sent
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("The configuration was not sent.")
            msg.setWindowTitle("Warning")
            msg.exec_()

# Test the class
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = SeafoilUi()
    ui.show()
    sys.exit(app.exec_())