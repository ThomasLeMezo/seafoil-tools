#!/bin/python3
import sys
import os
import time

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtWidgets
from PyQt5 import QtCore
import datetime

from seafoil_bag import SeafoilBag
from dock.dock_data import DockData
from dock.dock_log import DockLog
from dock.dock_gnss import DockGnss
from dock.dock_observer import DockDataObserver
from dock.dock_analysis import DockAnalysis
from dock.dock_fusion_analysis import DockFusionAnalysis

class Worker(QObject):
    data_loaded = pyqtSignal(str)

    def loading_data(self, filepath, offset_date, win):
        self.data_loaded.emit("Loading data...")
        sfb = None
        # test if file is a .gpx
        if filepath.endswith('.gpx'):
            sfb = SeafoilBag(filepath, offset_date, is_gpx=True)
        # test if file is a directory
        elif os.path.isdir(filepath):
            # Call reindex on the directory (ros2 bag reindex $DIRECTORY/$entry -s 'mcap')
            os.system(f"ros2 bag reindex {filepath} -s 'mcap'")
            ## Load ros2 bag
            sfb = SeafoilBag(filepath, offset_date)

        # Get file name from filepath
        filename = os.path.basename(filepath)

        tab = QtWidgets.QTabWidget()

        ## Data
        dock_data = DockData(sfb, tab)
        self.data_loaded.emit("Dock Data loaded")

        dock_data_observer = DockDataObserver(sfb, tab)
        self.data_loaded.emit("Dock Data Observer loaded")

        dock_log = DockLog(sfb, tab)
        self.data_loaded.emit("Dock Log loaded")

        data_gnss = DockGnss(sfb, tab, win)
        self.data_loaded.emit("Dock GNSS loaded")

        data_analysis = DockAnalysis(sfb, tab, win)
        self.data_loaded.emit("Dock Analysis loaded")

        data_fusion_analysis = DockFusionAnalysis(sfb, tab, data_analysis)
        self.data_loaded.emit("Dock Fusion Analysis loaded")

        tab.setCurrentWidget(data_analysis)

        win.setWindowTitle("log - " + filename)
        win.setCentralWidget(tab)

class SeafoilLogAnalyser(QMainWindow):

    def __init__(self, filepath=None, offset_date=None):
        super().__init__()

        self.worker = Worker()

        if filepath is None:
            return

        if offset_date is None:
            offset_date = datetime.datetime(2019, 1, 1)

        # Add a loading label
        loading_label = QtWidgets.QLabel("Loading...")
        loading_label.setAlignment(QtCore.Qt.AlignCenter) # Set text to be centered

        self.setCentralWidget(loading_label)

        # Start loading_data fuction in a new thread
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.worker.data_loaded.connect(lambda msg: loading_label.setText(msg))
        self.thread.started.connect(lambda: self.worker.loading_data(filepath, offset_date, self))
        self.thread.start()

        self.showMaximized()

    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        event.accept()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv)>1:
        filename = sys.argv[1]
        offset_date = None

        if len(sys.argv)>2:
            import datetime
            offset_date = datetime.datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%S")

        sla = SeafoilLogAnalyser(filename, offset_date)

        sys.exit(app.exec_())
    else:
        print("Usage: seafoil_log <folderpath/filename> [offset_date]")
        print("  filename: path to the rosbag folder or the .gpx file")
        print("  offset_date: optional, offset date to start the log")
        print("  example: seafoil_log /path/to/rosbag 2021-01-01T00:00:00")