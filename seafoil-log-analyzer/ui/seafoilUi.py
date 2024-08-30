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

        # connect the menu/action_new_session to function on_new_session_clicked
        self.ui.action_new_session.triggered.connect(self.on_new_session_clicked)

        # connect the pushButton_send_config to function on_send_config_clicked
        self.ui.pushButton_send_config.clicked.connect(self.on_send_config_clicked)

        # connect the pushButton_save_config to function on_save_config_clicked
        self.ui.pushButton_save_config.clicked.connect(self.on_save_config_clicked)

        # Seafoil Configuration
        self.sc = SeafoilConfiguration()
        self.update_ui_from_configuration()


    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        session = SeafoilUiSession(self.seafoil_directory)
        session.exec_()

    def update_ui_from_configuration(self):
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

    def update_configuration_from_ui(self):
        self.sc.v500 = self.ui.doubleSpinBox_v500.value()
        self.sc.v1850 = self.ui.doubleSpinBox_v1850.value()
        self.sc.heading_enable = self.ui.checkBox_enable_heading.isChecked()
        self.sc.voice_interval = self.ui.spinBox_voice_interval.value()
        self.sc.height_too_high = self.ui.doubleSpinBox_height_too_high.value()
        self.sc.height_high = self.ui.doubleSpinBox_height_high.value()

    def on_save_config_clicked(self):
        self.update_configuration_from_ui()
        # Open a dialog box to get the name of the configuration
        text, ok = QtWidgets.QInputDialog.getText(self, 'Save configuration', 'Enter the name of the configuration:')
        if ok:
            self.sc.db_save_configuration(text)
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