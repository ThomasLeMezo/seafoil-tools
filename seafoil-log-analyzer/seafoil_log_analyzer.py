#!/bin/python3
import sys
import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication

class SeafoilLogAnalyser(QMainWindow):
    def __init__(self, filepath=None, offset_date=None):
        super().__init__()

        from PyQt5 import QtCore
        from pyqtgraph.Qt import QtWidgets
        from seafoil_bag import SeafoilBag

        from dock.dock_data import DockData
        from dock.dock_log import DockLog
        from dock.dock_gnss import DockGnss
        from dock.dock_observer import DockDataObserver
        from dock.dock_analysis import DockAnalysis
        from dock.dock_fusion_analysis import DockFusionAnalysis

        import datetime

        if filepath is None:
            return

        if offset_date is None:
            offset_date = datetime.datetime(2019, 1, 1)

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

        ## Display
        win = QtWidgets.QMainWindow()
        win.showMaximized()
        # Get file name from filepath
        filename = os.path.basename(filepath)
        win.setWindowTitle(sfb.seafoil_id + " log - " + filename)

        tab = QtWidgets.QTabWidget()
        win.setCentralWidget(tab)

        ## Data
        dock_data = DockData(sfb, tab)
        dock_data_observer = DockDataObserver(sfb, tab)
        dock_log = DockLog(sfb, tab)
        data_gnss = DockGnss(sfb, tab, win)
        data_analysis = DockAnalysis(sfb, tab, win)
        data_fusion_analysis = DockFusionAnalysis(sfb, tab, data_analysis)

        tab.setCurrentWidget(data_analysis)

        win.show()

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