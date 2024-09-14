import sys
import os
import datetime

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QDialog, QLabel, \
    QLineEdit, QHBoxLayout, QPushButton

from device.seafoil_configuration import SeafoilConfiguration
from device.seafoil_equipement import SeafoilEquipement
from device.seafoil_session import SeafoilSession
from device.seafoil_log import SeafoilLog
from device.seafoil_git import SeafoilGit
from ui.seafoilUiLogTableWidget import SeafoilUiLogTableWidget

def upload_gpx(object, sl):
    # Open file dialog to select one or more gpx files
    file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(object, 'Open file', '', 'GPX files (*.gpx)')
    if len(file_paths) == 0:
        return

    # Upload the gpx files
    return sl.add_gpx_files(file_paths)

def contains_mcap_file(directories):
    # if directories is not a list
    if not isinstance(directories, list):
        directories = [directories]

    directories_ok = []
    directories_nok = []

    for dir in directories:
        # List all files in the directory
        files = os.listdir(dir)

        # Check if any file ends with ".mcap"
        is_ok = False
        for file in files:
            if file.endswith(".mcap"):
                is_ok = True
                break
        if not is_ok:
            directories_nok.append(dir)
        else:
            directories_ok.append(dir)
    return directories_ok, directories_nok

def upload_seafoil_log(sl):
    dialog = QtWidgets.QFileDialog()
    dialog.setFileMode(QtWidgets.QFileDialog.Directory)
    dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
    dialog.setOption(QtWidgets.QFileDialog.ReadOnly, True)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        directories = dialog.selectedFiles()

        directories_ok, directories_nok = contains_mcap_file(directories)

        if len(directories_nok) > 0:
            # Dialog box to confirm the directory does not contain a ".mcap" file
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("The following directories does not contain a .mcap file and will not be uploaded:\n" + "\n".join(directories_nok))
            msg.setWindowTitle("Warning")
            msg.exec_()

        if len(directories_ok) > 0:
            # Upload the mcap files
            return sl.add_seafoil_log(directories_ok)
    else:
        print("No directory selected")
        return None


def new_equipment_dialog_box(ui, se, category, item_index, is_new):
    # Create the dialog box
    dialog = QtWidgets.QDialog(ui)
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
    manufacturer.addItems(se.manufacturers_list)
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
        item = ui.treeWidget_equipment.currentItem()
        if item is None:
            return
        index = item_index.row()
        data = se.equipment_data[se.equipment_names.index(category)][index]
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

            se.db_insert_equipment(category, data)
            dialog.accept()
        else:
            dialog.reject()

    # connect the buttons to the function and return the result

    buttons.accepted.connect(lambda: on_button_clicked(buttons.button(buttons.Ok)))
    buttons.rejected.connect(lambda: on_button_clicked(buttons.button(buttons.Cancel)))

    # Wait for dialog to close
    result = dialog.exec_()
    if result == QtWidgets.QDialog.Accepted:
        return True
    else:
        return False

from ui.seafoilUiNewSession import SeafoilUiNewSession
from ui.seafoilUiDownload import SeafoilUiDownload

class SeafoilUiConfiguration:

    def __init__(self, seafoil_ui, ui):
        self.seafoil_ui = seafoil_ui
        self.ui = ui

        self.configuration_ui_was_connected = False

        # connect the pushButton_send_config to function on_send_config_clicked
        self.ui.pushButton_send_config.clicked.connect(self.on_send_config_clicked)

        # connect the pushButton_remove_config to function on_remove_config_clicked
        self.ui.pushButton_remove_config.clicked.connect(self.on_remove_config_clicked)

        # connect the pushButton_start_software to function on_start_software_clicked
        self.ui.pushButton_start_software.clicked.connect(self.on_start_software_clicked)

        # connect the pushButton_identification to function on_identification_clicked
        self.ui.pushButton_identification.clicked.connect(self.on_identification_clicked)

        # Seafoil Configuration
        self.sc = SeafoilConfiguration()
        self.update_ui_from_configuration()

        self.connect_value_changed_configuration(True)

    def on_identification_clicked(self):
        name = self.sc.db.get_seafoil_box_first()
        # Open a dialog box to enter the identification
        text, ok = QtWidgets.QInputDialog.getText(self.seafoil_ui, 'Identification', 'Enter the name of the seafoil box:', QtWidgets.QLineEdit.Normal, name)

        if ok:
            if name is None:
                self.sc.db.insert_seafoil_box(text)
            else:
                self.sc.db.rename_seafoil_box_first(text)

    def on_start_software_clicked(self):
        # open a dialog box to confirm the software was started
        if self.sc.sc.seafoil_service_start():
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("The software was started.")
            msg.setWindowTitle("Information")
            msg.exec_()
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("The software was not started.")
            msg.setWindowTitle("Warning")
            msg.exec_()

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
        self.ui.spinBox_heading.setValue(self.sc.wind_heading)

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
        self.sc.wind_heading = self.ui.spinBox_heading.value()

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
        # Set the button as disabled
        self.ui.pushButton_send_config.setEnabled(False)

        # Refresh ui
        QApplication.processEvents()

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

        # Set the button as enabled
        self.ui.pushButton_send_config.setEnabled(True)

class SeafoilUiEquipement:
    def __init__(self, seafoil_ui):
        self.seafoil_ui = seafoil_ui
        self.ui = seafoil_ui.ui
        self.se = SeafoilEquipement()

        self.equipment_name_list = {}
        for names in self.se.equipment_names:
            self.equipment_name_list[names] = None

        self.update_ui_from_equipment()

        # Add a menu (add/remove) for each type of equipment
        self.ui.treeWidget_equipment.setContextMenuPolicy(3)
        self.ui.treeWidget_equipment.customContextMenuRequested.connect(self.show_context_menu)
        # Add action when double clicking on an item
        self.ui.treeWidget_equipment.itemDoubleClicked.connect(self.on_item_double_clicked)


    def on_item_double_clicked(self, item, column):
        # Case of a top level item
        if item.parent() is None:
            new_equipment_dialog_box(self.ui, self.se, item.text(0), None, True)
        else:
            new_equipment_dialog_box(self.ui, self.se, item.parent().text(0), self.ui.treeWidget_equipment.currentIndex(), False)
        self.update_ui_from_equipment()

    def show_context_menu(self, position):
        # Create the context menu
        menu = QtWidgets.QMenu(self.ui.treeWidget_equipment)

        # Get the selected item
        item = self.ui.treeWidget_equipment.currentItem()

        # if item is None, return
        if item is None:
            return

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
            add_action = menu.addAction("Add " + category)
        else:
            add_action = menu.addAction("Add " + category)

        # Execute the menu and get the selected action
        action = menu.exec_(self.ui.treeWidget_equipment.mapToGlobal(position))

        if is_child and action == remove_action:
            self.remove_selected_item(category, item_index)
        elif is_child and action == update_action:
            new_equipment_dialog_box(self.ui, self.se, category, item_index,False)
        elif action == add_action:
            new_equipment_dialog_box(self.ui, self.se, category,item_index, True)
        self.update_ui_from_equipment()

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
        self.update_ui_from_equipment()

    def update_ui_from_equipment(self):
        self.se.update()
        # Add items from equipment_name_list
        self.ui.treeWidget_equipment.clear()
        self.ui.treeWidget_equipment.setHeaderLabels(["Equipement"])
        for i, name in enumerate(self.equipment_name_list.keys()):
            item = QTreeWidgetItem([name], i)
            self.ui.treeWidget_equipment.addTopLevelItem(item)
            self.equipment_name_list[name] = item

        for i, equipments_in_type in enumerate(self.se.equipment_data):
            if equipments_in_type is not None and len(equipments_in_type)>0:
                for equipment in equipments_in_type:
                    text = self.se.get_equipment_name(equipment, self.se.equipment_names[i])
                    self.equipment_name_list[self.se.equipment_names[i]].addChild(QTreeWidgetItem([text]))
        self.ui.treeWidget_equipment.expandAll()



class SeafoilUiSession(QtWidgets.QDialog):
    def __init__(self, seafoil_ui):
        super().__init__()
        self.seafoil_ui = seafoil_ui
        self.ui = seafoil_ui.ui
        self.session = SeafoilSession()

        columns = ["Id", "Start date", "Rider", "V500", "V1850"]
        self.ui.tableWidget_sessions.setColumnCount(len(columns))
        self.ui.tableWidget_sessions.setHorizontalHeaderLabels(columns)
        self.update_ui_from_session() # Sort by "date" latest first

        self.ui.tableWidget_sessions.sortItems(1, 1)

        # On double click on a row, open the log
        self.ui.tableWidget_sessions.itemDoubleClicked.connect(self.on_item_double_clicked)

        # Add menu to remove item
        self.ui.tableWidget_sessions.setContextMenuPolicy(3)
        self.ui.tableWidget_sessions.customContextMenuRequested.connect(self.show_context_menu)

        # connect the menu/action_new_session to function on_new_session_clicked
        self.ui.pushButton_new_session.clicked.connect(self.on_new_session_clicked)

    def on_item_double_clicked(self, item):
        # Get the row of the item and retrieve the value of the id column
        row = item.row()
        session_id = self.ui.tableWidget_sessions.item(row, 0).text()

        # Logic to execute when the button is clicked
        # non-blocking dialog box
        new_session = SeafoilUiNewSession(session_id)
        # wait for the dialog to close
        new_session.show()

        # wait for the dialog to close
        new_session.exec_()

        # On close, update the ui
        self.update_ui_from_session()

    def show_context_menu(self, position):
        # Create the context menu
        menu = QtWidgets.QMenu(self.ui.tableWidget_sessions)

        # Get the selected items
        selected_items = self.ui.tableWidget_sessions.selectedItems()
        if len(selected_items) == 0:
            return
        # Remove items where column is not 0
        item = [i for i in selected_items if i.column() == 0]

        remove_action = menu.addAction(f"Remove session ({len(item)})")

        # Execute the menu and get the selected action
        action = menu.exec_(self.ui.tableWidget_sessions.mapToGlobal(position))

        if action == remove_action:
            for i in range(len(item)):
                self.session.remove_session(int(item[i].text()))

        # Update the ui
        self.update_ui_from_session()

    def on_new_session_clicked(self):
        # Logic to execute when the button is clicked
        # non-blocking dialog box
        new_session = SeafoilUiNewSession()
        new_session.exec_()
        # On close, update the ui
        self.update_ui_from_session()

    def update_ui_from_session(self):
        self.session.update_session_list()

        self.ui.tableWidget_sessions.setSortingEnabled(True)
        # clear treeWidget_sessions
        self.ui.tableWidget_sessions.clearContents()

        # Set the number of rows
        self.ui.tableWidget_sessions.setRowCount(len(self.session.session_list))

        # Add items from session_list sorted by start_date year and month
        for i, session in enumerate(self.session.session_list):
            self.ui.tableWidget_sessions.setItem(i, 0, QtWidgets.QTableWidgetItem(str(session['id'])))

            # start_date from unix timestamp in local time zone
            if session['start_date'] is not None:
                start_date = datetime.datetime.fromtimestamp(session['start_date'])
                self.ui.tableWidget_sessions.setItem(i, 1, QtWidgets.QTableWidgetItem(start_date.strftime('%Y-%m-%d %H:%M:%S')))
            else:
                self.ui.tableWidget_sessions.setItem(i, 1, QtWidgets.QTableWidgetItem("Unknown"))

            # Add rider name
            if session['rider_id'] is not None:
                rider = self.session.db.get_rider(session['rider_id'])
                if rider is not None:
                    self.ui.tableWidget_sessions.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{rider['first_name']} {rider['last_name']}"))
                else:
                    self.ui.tableWidget_sessions.setItem(i, 2, QtWidgets.QTableWidgetItem("Unknown"))

            # Add v500
            if session['v500'] is not None:
                self.ui.tableWidget_sessions.setItem(i, 3, QtWidgets.QTableWidgetItem(str(session['v500'])))
            else:
                self.ui.tableWidget_sessions.setItem(i, 3, QtWidgets.QTableWidgetItem("Unknown"))

            # Add v1850
            if session['v1850'] is not None:
                self.ui.tableWidget_sessions.setItem(i, 4, QtWidgets.QTableWidgetItem(str(session['v1850'])))
            else:
                self.ui.tableWidget_sessions.setItem(i, 4, QtWidgets.QTableWidgetItem("Unknown"))

        # Auto resize columns
        self.ui.tableWidget_sessions.setSortingEnabled(True)
        self.ui.tableWidget_sessions.resizeColumnsToContents()

class SeafoilUiLog(QtWidgets.QDialog):
    def __init__(self, seafoil_ui):
        super().__init__()
        self.seafoil_ui = seafoil_ui
        self.ui = seafoil_ui.ui
        self.sl = SeafoilLog()

        # Connect pushButton_upload_gpx to function on_upload_gpx_clicked
        self.ui.pushButton_upload_gpx.clicked.connect(self.on_upload_gpx_clicked)

        self.seafoil_log_table_widget = SeafoilUiLogTableWidget(self.ui.tableWidget_logs, self.sl, True, True)

        # Connect pushButton_upload_log to function on_upload_log_clicked
        self.ui.pushButton_upload_log.clicked.connect(self.on_upload_log_clicked)

        # Connect pushButton_import_log to function on_import_log_clicked
        self.ui.pushButton_import_log.clicked.connect(self.on_import_log_clicked)

    def on_import_log_clicked(self):
        upload_seafoil_log(self.sl)
        self.seafoil_log_table_widget.update_ui_from_logs()

    def on_upload_log_clicked(self):
        download = SeafoilUiDownload()
        download.exec_()

        # On close, update the ui
        self.seafoil_log_table_widget.update_ui_from_logs()

    def on_upload_gpx_clicked(self):
        upload_gpx(self, self.sl)
        self.seafoil_log_table_widget.update_ui_from_logs()


class SeafoilUi(QtWidgets.QMainWindow):
    def __init__(self, seafoil_directory):
        super().__init__()

        # Get directory of the current file
        self.seafoil_directory = seafoil_directory
        self.ui = uic.loadUi(self.seafoil_directory + '/ui/main_window.ui', self)
        self.sg = SeafoilGit()

        self.seafoil_ui_configuration = SeafoilUiConfiguration(self, self.ui)
        self.seafoil_ui_equipment = SeafoilUiEquipement(self)
        self.seafoil_ui_session = SeafoilUiSession(self)
        self.seafoil_ui_log = SeafoilUiLog(self)

        # connect the tabWidget change index
        self.ui.tabWidget.currentChanged.connect(self.on_tabWidget_changed)

        # connect menu action actionMise_jour to function on_actionMise_jour_triggered
        self.ui.actionMise_jour.triggered.connect(self.update_git)

    def update_git(self):
        # Get the current tag
        current_tag = self.sg.get_current_tag()
        # Get the latest tag
        latest_tag = self.sg.get_last_tag()

        # If the current tag is not the latest tag open a dialog box to update
        if current_tag != latest_tag:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText(f"Current version: {current_tag}\nLatest version: {latest_tag}")
            msg.setWindowTitle("Update")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QtWidgets.QMessageBox.Ok:
                self.sg.update_to_last_tag()
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText(f"Current version: {current_tag}\nLatest version: {latest_tag}")
            msg.setWindowTitle("Update")
            msg.exec_()

    def on_tabWidget_changed(self, index):
        if index == 0:
            self.seafoil_ui_session.update_ui_from_session()
        elif index == 1:
            self.seafoil_ui_log.seafoil_log_table_widget.update_ui_from_logs()
        elif index == 2:
            self.seafoil_ui_equipment.update_ui_from_equipment()
        elif index == 3:
            self.seafoil_ui_configuration.update_ui_from_configuration()


