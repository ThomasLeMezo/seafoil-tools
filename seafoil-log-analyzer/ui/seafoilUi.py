import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from .seafoilUiSession import SeafoilUiSession
from device.seafoil_configuration import SeafoilConfiguration
from device.seafoil_equipement import SeafoilEquipement
import os

class SeafoilUiConfiguration:

    def __init__(self, seafoil_ui, ui):
        self.seafoil_ui = seafoil_ui
        self.ui = ui

        self.configuration_ui_was_connected = False



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
            text, ok = QtWidgets.QInputDialog.getText(self.seafoil_ui, 'Save configuration', 'Enter the name of the configuration:')
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

class SeafoilUiEquipement:
    def __init__(self, seafoil_ui):
        self.seafoil_ui = seafoil_ui
        self.ui = seafoil_ui.ui
        self.se = SeafoilEquipement()

        self.equipment_name_list = {}
        for names in self.se.equipment_names:
            self.equipment_name_list[names] = None

        self.update_ui_from_equipement()

        # Add a menu (add/remove) for each type of equipment
        self.ui.treeWidget_equipment.setContextMenuPolicy(3)
        self.ui.treeWidget_equipment.customContextMenuRequested.connect(self.show_context_menu)


    def show_context_menu(self, position):
        # Create the context menu
        menu = QtWidgets.QMenu(self.ui.treeWidget_equipment)

        # Get the selected item
        item = self.ui.treeWidget_equipment.currentItem()

        category = item.text(0)
        remove_action = None
        add_action = None
        update_action = None
        is_child = item.parent() is not None
        item_index = self.ui.treeWidget_equipment.currentIndex()

        if is_child:
            item_top = self.ui.treeWidget_equipment.currentItem().parent()
            category = item_top.text(0)
            remove_action = menu.addAction("Remove " + category)
            update_action = menu.addAction("Update " + category)
        else:
            add_action = menu.addAction("Add " + category)

        # Execute the menu and get the selected action
        action = menu.exec_(self.ui.treeWidget_equipment.mapToGlobal(position))

        if is_child and action == remove_action:
            self.remove_selected_item(category, item_index)
        elif is_child and action == update_action:
            pass
        elif action == add_action:
            pass

    def remove_selected_item(self, category, item_index):
        if not item_index.isValid():
            return
        # Ask for confirmation
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setText(f"Do you want to remove this {category}?")
        msg.setWindowTitle(f"Remove {category}")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        ret = msg.exec_()
        if ret == QtWidgets.QMessageBox.No:
            return
        self.se.db_remove_equipment(category, item_index.row())
        self.update_ui_from_equipement()

    def update_ui_from_equipement(self):
        # Add items from equipment_name_list
        self.ui.treeWidget_equipment.clear()
        self.ui.treeWidget_equipment.setHeaderLabels(["Equipement"])
        for i, name in enumerate(self.equipment_name_list.keys()):
            item = QTreeWidgetItem([name], i)
            self.ui.treeWidget_equipment.addTopLevelItem(item)
            self.equipment_name_list[name] = item

        def equipment_text(data):
            return f"{data['manufacturer']} {data['model']} ({data['year']}) {data['comment']}"
        def equipment_text_postfix(data, id):
            if id == 0:
                return f" [{data['volume']:.0f} L]"
            elif id == 1:
                return f" [{data['size']:.0f} m²]"
            elif id == 2:
                return f" [{data['surface']:.0f} cm²]"
            elif id == 3:
                return f" [{data['surface']:.0f} m²]"
            elif id == 4:
                return f" [{data['length']*100:.0f} cm]"
            elif id == 5:
                return f" [{data['length']*100:.0f} cm]"
            else:
                return ""

        for i, equipment_type in enumerate(self.se.data):
            if equipment_type is not None and len(equipment_type)>0:
                for equipment in equipment_type:
                    text = equipment_text(equipment) + equipment_text_postfix(equipment, i)
                    self.equipment_name_list[self.se.equipment_names[i]].addChild(QTreeWidgetItem([text]))
        self.ui.treeWidget_equipment.expandAll()


class SeafoilUi(QtWidgets.QMainWindow):
    def __init__(self, seafoil_directory):
        super().__init__()

        # Get directory of the current file
        self.seafoil_directory = seafoil_directory
        self.ui = uic.loadUi(self.seafoil_directory + '/ui/main_window.ui', self)

        self.seafoil_ui_configuration = SeafoilUiConfiguration(self, self.ui)
        self.seafoil_ui_equipment = SeafoilUiEquipement(self)

        # connect the menu/action_new_session to function on_new_session_clicked
        self.ui.action_new_session.triggered.connect(self.on_new_session_clicked)

    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        session = SeafoilUiSession(self.seafoil_ui.seafoil_directory)
        session.exec_()
