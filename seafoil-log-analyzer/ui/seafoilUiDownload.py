import sys
from PyQt5 import QtWidgets, uic
import os

from PyQt5.QtWidgets import QListWidgetItem, QMessageBox, QApplication
from PyQt5.QtCore import QAbstractListModel, Qt, QThread, QTimer, pyqtSignal
from PyQt5 import QtCore

from device.seafoil_connexion import SeafoilConnexion
from device.seafoil_connexion import StateConnexion
from device.seafoil_log import SeafoilLog
from device.seafoil_new_session import SeafoilNewSession

from ui.seafoilUiProcess import SeafoilUiProcess

class WorkerThread(QThread):
    # Define a signal to communicate with the main thread
    timer_signal = pyqtSignal()

    def __init__(self, interval=1000, stop_worker_thread=None):
        super().__init__()
        self.interval = interval
        # Connect the stop_worker_thread signal to the stop method
        stop_worker_thread.connect(self.stop)

    def run(self):
        # Create a QTimer within the worker thread
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_signal)  # Connect the timeout signal to a method
        self.timer.start(self.interval)  # Start the timer with the specified interval

        # Start the event loop
        self.exec_()

    def send_signal(self):
        # Emit a signal with a message each time the timer fires
        self.timer_signal.emit()

    def stop(self):
        print("Stopping the worker thread")
        # Stop the timer and thread
        self.timer.stop()
        self.quit()
        self.wait()

class SeafoilUiDownload(QtWidgets.QDialog):
    stop_worker_thread = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sns = SeafoilNewSession()
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(self.directory + '/download.ui', self)
        self.sl = SeafoilLog()

        self.loading_symbol_state = 0

        # Connect the pushButton_download
        self.ui.pushButton_download.clicked.connect(self.download_logs)

        # Connect the pushButton_delete_log
        self.ui.pushButton_delete_log.clicked.connect(self.delete_logs)

        # Connect to the signal from the SeafoilConnexion
        self.sl.sc.signal_download_log.connect(self.update_progress_bar)
        self.ui.progressBar.setFormat("%p% (%v)")

        # Create and start the worker thread
        self.worker_thread = WorkerThread(interval=250, stop_worker_thread=self.stop_worker_thread)  # Timer interval set to 1000 ms (1 second)
        self.worker_thread.timer_signal.connect(self.update_ui)  # Connect the signal to update_label method
        self.worker_thread.start()

        # Create a timer to call process_log every second
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_timer)
        self.timer.start(1000)

        # Connect button Cancel to close the window
        self.ui.buttonBox.rejected.connect(self.cancel)

        self.log_downloaded = []

    def __del__(self):
        self.timer.stop()
        self.stop_worker_thread.emit()

    # close event
    def closeEvent(self, event):
        self.timer.stop()
        self.stop_worker_thread.emit()
        event.accept()

    def cancel(self):
        self.timer.stop()
        self.stop_worker_thread.emit()
        self.close()

    def update_progress_bar(self, progress, remaining_log_to_download):
        self.ui.progressBar.setValue(progress)
        self.ui.progressBar.setFormat(f"%p% ({remaining_log_to_download})")
        # Refresh ui
        QApplication.processEvents()

    def add_loading_symbol(self):
        # Refresh ui
        QApplication.processEvents()

        self.loading_symbol_state = (self.loading_symbol_state + 1) % 4
        return '.' * self.loading_symbol_state

    def process_timer(self):
        QApplication.processEvents()
        # Call SeafoilConnexion process_log
        self.sl.sc.process_connexion()

        if self.sl.sc.connexion_state == StateConnexion.DownloadLog:
            self.update_log_list()
            # stop timer
            self.timer.stop()
            self.stop_worker_thread.emit()
            self.update_ui()

    def update_ui(self):
        # Connexion state
        if self.sl.sc.connexion_state == StateConnexion.Disconnected:
            self.ui.label_connexion.setText(f"Connexion{self.add_loading_symbol()}")
        elif self.sl.sc.connexion_state > StateConnexion.Disconnected:
            self.ui.label_connexion.setText(f"Connected")
            self.ui.label_connexion.setStyleSheet("color: green")

        # Stop software state
        if self.sl.sc.connexion_state < StateConnexion.SeafoilServiceStop:
            self.ui.label_stop_software.setText(f"Stop Software")
            self.ui.label_stop_software.setStyleSheet("color: gray")
        elif self.sl.sc.connexion_state == StateConnexion.SeafoilServiceStop:
            self.ui.label_stop_software.setText(f"Stop Software{self.add_loading_symbol()}")
            self.ui.label_stop_software.setStyleSheet("color: black")
        else:
            self.ui.label_stop_software.setText(f"Software Stopped")
            self.ui.label_stop_software.setStyleSheet("color: green")

        # Download log list state
        if self.sl.sc.connexion_state < StateConnexion.DownloadLogList:
            self.ui.label_download_log_list.setText(f"Download Log List")
            self.ui.label_download_log_list.setStyleSheet("color: gray")
        elif self.sl.sc.connexion_state == StateConnexion.DownloadLogList:
            self.ui.label_download_log_list.setText(f"Download Log List{self.add_loading_symbol()}")
            self.ui.label_download_log_list.setStyleSheet("color: black")
        else:
            self.ui.label_download_log_list.setText(f"Log List Downloaded")
            self.ui.label_download_log_list.setStyleSheet("color: green")

        # Refresh ui
        QApplication.processEvents()

    def update_log_list(self):
        self.listWidget_logs.clear()
        # Add items to the list widget with checkboxes
        for log in self.sl.sc.stored_log_list:
            item_text = str(log['id']) + ' - ' + log['name']
            if log['is_new']:
                item_text += ' [NEW]'
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Set the item as checkable
            if log['is_new']:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)  # Set the initial state to unchecked
            self.listWidget_logs.addItem(item)

        # Enable the download button
        self.ui.pushButton_download.setEnabled(True)
        # Enable the delete button
        self.ui.pushButton_delete_log.setEnabled(True)

    def download_logs(self):
        # Disable the download button
        self.ui.pushButton_download.setEnabled(False)
        # Refresh ui
        QApplication.processEvents()

        # Get the checked items
        checked_logs = []
        for index in range(self.listWidget_logs.count()):
            if self.listWidget_logs.item(index).checkState() == Qt.Checked:
                checked_logs.append(index)

        # Call SeafoilConnexion download_logs
        msg = None
        success, log_added = self.sl.sc.seafoil_download_logs(checked_logs)
        if success:
            msg = QMessageBox.information(self, 'Download Logs', f'{len(checked_logs)} logs have been downloaded (connexion can be disable), now processing', QMessageBox.Ok)

            sp = SeafoilUiProcess()
            sp.show()
            for i, log in enumerate(log_added):
                sp.update_title(i, len(log_added))
                self.sl.process_log(log, sp.update_ui)
            sp.close()

        else:
            msg = QMessageBox.warning(self, 'Download Logs', f'An error occured while downloading the logs', QMessageBox.Ok)

        # Update the log list
        self.update_log_list()

        self.ui.pushButton_download.setEnabled(True)

        # Add log_added to log_downloaded
        self.log_downloaded += log_added

    def delete_logs(self):
        # Get the checked items
        selected_logs = []
        for index in range(self.listWidget_logs.count()):
            if self.listWidget_logs.item(index).isSelected():
                selected_logs.append(index)

        # Open a Dialog to confirm the deletion
        msg = QMessageBox.question(self, 'Delete Logs', f'Are you sure you want to delete the selected {len(selected_logs)} logs?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if msg == QMessageBox.Yes:
            # Call SeafoilConnexion delete_logs
            self.sl.sc.seafoil_delete_logs(selected_logs)
            # Update the log list
            self.update_log_list()
        else:
            pass
