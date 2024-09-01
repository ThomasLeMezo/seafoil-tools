import sys
import datetime

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
        # Add action when double clicking on an item
        self.ui.treeWidget_equipment.itemDoubleClicked.connect(self.on_item_double_clicked)


    def on_item_double_clicked(self, item, column):
        # Case of a top level item
        if item.parent() is None:
            self.equipment_dialog_box(item.text(0), None, True)
        else:
            self.equipment_dialog_box(item.parent().text(0), self.ui.treeWidget_equipment.currentIndex(), False)

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
            update_action = menu.addAction("Update " + category)
            remove_action = menu.addAction("Remove " + category)
        else:
            add_action = menu.addAction("Add " + category)

        # Execute the menu and get the selected action
        action = menu.exec_(self.ui.treeWidget_equipment.mapToGlobal(position))

        if is_child and action == remove_action:
            self.remove_selected_item(category, item_index)
        elif is_child and action == update_action:
            self.equipment_dialog_box(category, item_index,False)
        elif action == add_action:
            self.equipment_dialog_box(category,item_index, True)

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
            return f"{data['manufacturer']} {data['model']}, {data['year']}"
        def equipment_text_postfix(data, category):
            if category == 'Board':
                return f" [{data['volume']:.0f} L, {data['width']*100:.0f} cm, {data['length']:.0f} m]"
            elif category == 'Sail':
                return f" [{data['surface']:.1f} m²]"
            elif category == 'Front foil':
                return f" [{data['surface']*1e4:.0f} cm²]"
            elif category == 'Stabilizer':
                return f" [{data['surface']:.0f} m²]"
            elif category == 'Foil mast':
                return f" [{data['length']*100:.0f} cm]"
            elif category == 'Fuselage':
                return f" [{data['length']*100:.0f} cm]"
            else:
                return ""

        for i, equipment_type in enumerate(self.se.equipment_data):
            if equipment_type is not None and len(equipment_type)>0:
                for equipment in equipment_type:
                    text = equipment_text(equipment) + equipment_text_postfix(equipment, self.se.equipment_names[i])
                    self.equipment_name_list[self.se.equipment_names[i]].addChild(QTreeWidgetItem([text]))
        self.ui.treeWidget_equipment.expandAll()

    def equipment_dialog_box(self, category, item_index, is_new):
        # Create the dialog box
        dialog = QtWidgets.QDialog(self.ui)
        dialog.setWindowTitle(f"{category} configuration - {'NOUVEAU' if is_new else 'Update'}")
        dialog.setModal(True)

        # Create the layout
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Create a form layout
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        # Create the fields
        # editing combo box
        manufacturer = QtWidgets.QComboBox()
        form.addRow("Manufacturer", manufacturer)
        manufacturer.setEditable(True) # set editable
        # provide a list of manufacturers
        manufacturer.addItems(self.se.manufacturers_list)
        # default value
        manufacturer.setCurrentText("")

        model = QtWidgets.QLineEdit()
        form.addRow("Model", model)

        year = QtWidgets.QSpinBox()
        year.setMinimum(2010)
        year.setMaximum(2030)
        year.setValue(datetime.datetime.now().year)
        form.addRow("Year", year)

        comment = QtWidgets.QPlainTextEdit()
        form.addRow("Comment", comment)

        if category == 'Board':
            volume = QtWidgets.QSpinBox()
            volume.setSuffix(" L")
            volume.setMaximum(300)
            form.addRow("Volume", volume)
            width = QtWidgets.QSpinBox()
            width.setSuffix(" cm")
            width.setMaximum(150)
            form.addRow("Width", width)
            length = QtWidgets.QDoubleSpinBox()
            length.setSuffix(" m")
            length.setMaximum(3)
            length.setDecimals(2)
            form.addRow("Length", length)
        elif category == 'Sail':
            size = QtWidgets.QDoubleSpinBox()
            size.setSuffix(" m²")
            size.setMaximum(20)
            size.setDecimals(1)
            form.addRow("Size", size)
        elif category == 'Front foil':
            surface = QtWidgets.QSpinBox()
            surface.setSuffix(" cm²")
            surface.setMaximum(2000)
            form.addRow("Surface", surface)
        elif category == 'Stabilizer':
            surface = QtWidgets.QSpinBox()
            surface.setSuffix(" cm²")
            surface.setMaximum(1000)
            form.addRow("Surface", surface)
        elif category == 'Foil mast':
            length = QtWidgets.QSpinBox()
            length.setMaximum(150)
            length.setSuffix(" cm")
            form.addRow("Length", length)
        elif category == 'Fuselage':
            length = QtWidgets.QDoubleSpinBox()
            length.setSuffix(" cm")
            length.setMaximum(150)
            length.setDecimals(1)
            form.addRow("Length", length)

        # Add the buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        # display the dialog box
        if not is_new:
            item = self.ui.treeWidget_equipment.currentItem()
            if item is None:
                return
            index = item_index.row()
            data = self.se.equipment_data[self.se.equipment_names.index(category)][index]
            manufacturer.setCurrentText(data['manufacturer'])
            model.setText(data['model'])
            year.setValue(data['year'])
            comment.setPlainText(data['comment'])
            if category == 'Board':
                volume.setValue(int(data['volume']))
                width.setValue(int(data['width']*100))
                length.setValue(data['length'])
            elif category == 'Sail':
                size.setValue(data['surface'])
            elif category == 'Front foil':
                surface.setValue(int(data['surface']*1e4))
            elif category == 'Stabilizer':
                surface.setValue(int(data['surface']*1e4))
            elif category == 'Foil mast':
                length.setValue(int(data['length']*100))
            elif category == 'Fuselage':
                length.setValue(data['length']*100)

        def on_button_clicked(button):
            if button.text() == buttons.button(buttons.Ok).text():
                data = {}
                data['index'] = item_index.row() if not is_new else None
                data['manufacturer'] = manufacturer.currentText()
                data['model'] = model.text()
                data['year'] = year.value()
                data['comment'] = comment.toPlainText()
                if category == 'Board':
                    data['volume'] = volume.value()
                    data['width'] = width.value()/100
                    data['length'] = length.value()
                elif category == 'Sail':
                    data['surface'] = size.value()
                elif category == 'Front foil':
                    data['surface'] = surface.value()/1e4
                elif category == 'Stabilizer':
                    data['surface'] = surface.value()/1e4
                elif category == 'Foil mast':
                    data['length'] = length.value()/100
                elif category == 'Fuselage':
                    data['length'] = length.value()/100

                self.se.db_insert_equipment(category, data)
                self.update_ui_from_equipement()
            dialog.close()

        # connect the buttons to the function
        buttons.accepted.connect(lambda: on_button_clicked(buttons.button(buttons.Ok)))
        buttons.rejected.connect(lambda: on_button_clicked(buttons.button(buttons.Cancel)))

        # show the dialog box
        dialog.show()


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
