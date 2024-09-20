import datetime

from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QApplication

from device.seafoil_log import SeafoilLog
from ui.seafoilUiProcess import SeafoilUiProcess
from ui.ui_utils import TwoFieldInputDialog


class SeafoilUiLogTableWidget():
    def __init__(self, tablewidget, seafoil_log, enable_open=True, enable_remove=True):
        self.tablewidget = tablewidget
        self.sl = seafoil_log

        # Set the number of columns
        columns = ["id", "date", "duration", "rider", "session", "support","v500", "v1850", "vmax", "log type", "name"]
        self.tablewidget.setColumnCount(len(columns))
        # Set headers
        self.tablewidget.setHorizontalHeaderLabels(columns)

        # Sort by "date" latest first
        self.update_ui_from_logs()

        self.tablewidget.sortItems(1, 1)

        if enable_open:
            # On double click on a row, open the log
            self.tablewidget.itemDoubleClicked.connect(self.on_item_double_clicked)

        if enable_remove:
            # Add menu to remove item
            self.tablewidget.setContextMenuPolicy(3)
            self.tablewidget.customContextMenuRequested.connect(self.show_context_menu)

    def update_ui_from_logs(self):
        self.sl.update()
        # clear treeWidget_sessions
        self.tablewidget.clearContents()
        self.tablewidget.setSortingEnabled(False)

        # Set the number of rows
        self.tablewidget.setRowCount(len(self.sl.logs))

        current_row = 0
        current_column = 0
        def add_item(row, text):
            nonlocal current_row, current_column
            if row != current_row:
                current_row = row
                current_column = 0
            self.tablewidget.setItem(row, current_column, QtWidgets.QTableWidgetItem(text))
            current_column += 1

        # Add items from session_list sorted by start_date year and month
        for i, log in enumerate(self.sl.logs):
            # "id", "date", "duration", "session", "v500", "v1850", "vmax", "type", "name"

            # start_date from unix timestamp in local time zone
            add_item(i, str(log['id']))

            start_date = datetime.datetime.fromtimestamp(log['starting_time'])
            add_item(i, start_date.strftime('%Y-%m-%d %H:%M:%S'))

            if log['ending_time'] is not None and log['starting_time'] is not None:
                duration = round(log['ending_time'] - log['starting_time'])
                add_item(i, str(datetime.timedelta(seconds=duration)))
            else:
                add_item(i, '')

            ms_to_kt = 1.94384

            add_item(i, f"{log['rider_first_name']} {log['rider_last_name']}" if log['rider_last_name'] is not None else '')
            add_item(i, f"{log['session']}" if log['session'] is not None else '')
            add_item(i, f"{log['water_sport']}" if log['water_sport'] is not None else '')
            add_item(i, f"{log['v500']*ms_to_kt:.2f}" if log['v500'] is not None else '')
            add_item(i, f"{log['v1850']*ms_to_kt:.2f}" if log['v1850'] is not None else '')
            add_item(i, f"{log['vmax']*ms_to_kt:.2f}" if log['vmax'] is not None else '')
            add_item(i, self.sl.db.convert_log_type_from_int(log['type']))
            add_item(i, log['name'])


        # Auto resize columns
        self.tablewidget.resizeColumnsToContents()
        self.tablewidget.setSortingEnabled(True)

    def on_item_double_clicked(self, item):
        # Get the row of the item and retrieve the value of the id column
        row = item.row()
        id = self.tablewidget.item(row, 0).text()
        self.sl.open_log(int(id))

    def show_context_menu(self, position):
        # Create the context menu
        menu = QtWidgets.QMenu(self.tablewidget)

        # Get the selected items
        selected_items = self.tablewidget.selectedItems()
        if len(selected_items) == 0:
            return
        # Remove items where column is not 0
        item = [i for i in selected_items if i.column() == 0]

        # Add a Section to the menu
        menu.addSection(f"Selection of ({len(item)}) logs")

        # Process action
        process_action = menu.addAction(f"Reprocess log")

        # Change sport type action
        change_sport_type_action = QtWidgets.QMenu(f"Change sport type")
        sports = self.sl.db.get_water_sport_type_all()
        for sport in sports:
            change_sport_type_action.addAction(sport['name'])
        menu.addMenu(change_sport_type_action)

        # Change rider action
        change_rider_action = QtWidgets.QMenu(f"Change rider")
        riders = self.sl.db.get_rider_all()
        for rider in riders:
            change_rider_action.addAction(f"{rider['first_name']} {rider['last_name']}")

        italic_font = QFont()
        italic_font.setItalic(True)
        new_rider_action = change_rider_action.addAction("New rider")
        new_rider_action.setFont(italic_font)
        menu.addMenu(change_rider_action)

        # Edit rider name action
        edit_rider_name_action = None
        if len(item) == 1:
            edit_rider_name_action = menu.addAction("Edit rider name")

        # Open in folder action
        open_in_folder_action = None
        if len(item) == 1:
            open_in_folder_action = menu.addAction(f"Open in folder")

        # If the log is not a gpx file, add the export to gpx action
        export_to_gpx_action = None
        if len(item) == 1:
            export_to_gpx_action = menu.addAction(f"Export to gpx")

        # Remove action
        remove_action = menu.addAction(f"Remove log")

        ######################################################################################
        # Execute the menu and get the selected action
        action = menu.exec_(self.tablewidget.mapToGlobal(position))

        if action is None:
            return
        if action == remove_action:
            for i in range(len(item)):
                if not self.sl.remote_remove_log(int(item[i].text())):
                    # message failed to remove
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Critical)
                    msg.setText("Log protected : delete session first")
                    msg.setWindowTitle("Error")
                    msg.exec_()
        elif action == open_in_folder_action:
            self.sl.open_log_folder(int(item[0].text()))
        elif action == export_to_gpx_action:
            self.sl.open_log_folder(int(item[0].text()), True)
        elif action == process_action:
            sp = SeafoilUiProcess()
            sp.show()
            for i in range(len(item)):
                sp.update_title(i, len(item))
                self.sl.process_log(int(item[i].text()), sp.update_ui)
            sp.close()
        elif action == edit_rider_name_action:
            # Open a dialog to edit the rider name
            log = self.sl.db.get_log(int(item[0].text()))
            if log['rider_id'] is None:
                # Message to select a rider
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("No rider associated with this log")
                msg.setWindowTitle("Error")
                msg.exec_()
                return
            rider = self.sl.db.get_rider(log['rider_id'])
            dialog = TwoFieldInputDialog("Edit Rider", "First Name", "Last Name", rider['first_name'], rider['last_name'])
            if dialog.exec_() == QDialog.Accepted:
                first_name, last_name = dialog.get_inputs()
                self.sl.db.update_rider(log['rider_id'], first_name, last_name)
                self.update_ui_from_logs()
        else:
            # Find the sport type id
            sport_id = None
            for i in range(len(sports)):
                if sports[i]['name'] == action.text():
                    sport_id = sports[i]['id']
                    break
            if sport_id is not None:
                for i in range(len(item)):
                    self.sl.db.update_log_sport_type(int(item[i].text()), sport_id)

            # Find the rider id
            rider_id = None
            if action.text() == "New rider":
                # Open a dialog to add a new rider (First name, Last name)
                dialog = TwoFieldInputDialog("New Rider", "First Name", "Last Name")
                if dialog.exec_() == QDialog.Accepted:
                    first_name, last_name = dialog.get_inputs()
                    rider_id = self.sl.db.add_rider(first_name, last_name, manual_add=True)
                    print(rider_id)
                    for i in range(len(item)):
                        self.sl.db.update_log_rider(int(item[i].text()), rider_id)

            for i in range(len(riders)):
                if f"{riders[i]['first_name']} {riders[i]['last_name']}" == action.text():
                    rider_id = riders[i]['id']
                    break
            if rider_id is not None:
                for i in range(len(item)):
                    self.sl.db.update_log_rider(int(item[i].text()), rider_id)

        # Update the ui
        self.update_ui_from_logs()

    def get_list_of_selected_logs(self):
        selected_items = self.tablewidget.selectedItems()
        if len(selected_items) == 0:
            return []
        # Remove items where column is not 0
        item = [i for i in selected_items if i.column() == 0]
        return [int(i.text()) for i in item]