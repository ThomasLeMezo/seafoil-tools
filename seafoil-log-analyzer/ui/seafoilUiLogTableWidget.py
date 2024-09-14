import datetime

from PyQt5 import QtWidgets
from device.seafoil_log import SeafoilLog

class SeafoilUiLogTableWidget():
    def __init__(self, tablewidget, seafoil_log, enable_open=True, enable_remove=True):
        self.tablewidget = tablewidget
        self.sl = seafoil_log

        # Set the number of columns
        columns = ["id", "date", "duration", "type", "name", "session"]
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

        # Add items from session_list sorted by start_date year and month
        for i, log in enumerate(self.sl.logs):
            # start_date from unix timestamp in local time zone
            self.tablewidget.setItem(i, 0, QtWidgets.QTableWidgetItem(str(log['id'])))
            start_date = datetime.datetime.fromtimestamp(log['starting_time'])
            self.tablewidget.setItem(i, 1, QtWidgets.QTableWidgetItem(start_date.strftime('%Y-%m-%d %H:%M:%S')))
            if log['ending_time'] is not None and log['starting_time'] is not None:
                duration = log['ending_time'] - log['starting_time']
                self.tablewidget.setItem(i, 2, QtWidgets.QTableWidgetItem(str(datetime.timedelta(seconds=duration))))
            else:
                self.tablewidget.setItem(i, 2, QtWidgets.QTableWidgetItem(''))
            self.tablewidget.setItem(i, 3, QtWidgets.QTableWidgetItem(self.sl.db.convert_log_type_from_int(log['type'])))
            self.tablewidget.setItem(i, 4, QtWidgets.QTableWidgetItem(log['name']))
            self.tablewidget.setItem(i, 5, QtWidgets.QTableWidgetItem(str(log['session'])))

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

        remove_action = menu.addAction(f"Remove log ({len(item)})")

        # Execute the menu and get the selected action
        action = menu.exec_(self.tablewidget.mapToGlobal(position))

        if action == remove_action:
            for i in range(len(item)):
                if not self.sl.remote_remove_log(int(item[i].text())):
                    # message failed to remove
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Critical)
                    msg.setText("Log protected : delete session first")
                    msg.setWindowTitle("Error")
                    msg.exec_()

        # Update the ui
        self.update_ui_from_logs()

    def get_list_of_selected_logs(self):
        selected_items = self.tablewidget.selectedItems()
        if len(selected_items) == 0:
            return []
        # Remove items where column is not 0
        item = [i for i in selected_items if i.column() == 0]
        return [int(i.text()) for i in item]