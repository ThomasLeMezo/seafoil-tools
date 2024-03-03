#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
from seafoil_bag import SeafoilBag

from dock.dock_data import DockData
from dock.dock_log import DockLog
from dock.dock_gnss import DockGnss
from dock.dock_observer import DockDataObserver
from dock.dock_analysis import DockAnalysis
from dock.dock_fusion_analysis import DockFusionAnalysis

import datetime

if ('filename' in locals()):
    print("filename = ", filename)
else:
    if(len(sys.argv)<2):
        sys.exit(0)
    filename = sys.argv[1]

offset_date = datetime.datetime(2019, 1, 1)
if len(sys.argv)>=3:
    offset_date = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S')
    print(offset_date)

## Load ros2 bag
sfb = SeafoilBag(filename, offset_date)
## Display

app = QtWidgets.QApplication([])
win = QtWidgets.QMainWindow()
win.showMaximized()
win.setWindowTitle(sfb.seafoil_id + " log - " + sys.argv[1])

tab = QtWidgets.QTabWidget()
win.setCentralWidget(tab)

## Data
dock_data = DockData(sfb, tab)
dock_data_observer = DockDataObserver(sfb, tab)
dock_log = DockLog(sfb, tab)
data_gnss = DockGnss(sfb, tab, win)
data_analysis = DockAnalysis(sfb, tab)
data_fusion_analysis = DockFusionAnalysis(sfb, tab, data_analysis)

tab.setCurrentWidget(data_analysis)

win.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()