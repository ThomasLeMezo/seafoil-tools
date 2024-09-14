#!/bin/python3
import sys
import os
import time
import typing

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtWidgets
from PyQt5 import QtCore
import datetime

from .seafoil_bag import SeafoilBag
from .dock.dock_data import DockData
from .dock.dock_log import DockLog
from .dock.dock_gnss import DockGnss
from .dock.dock_observer import DockDataObserver
from .dock.dock_analysis import DockAnalysis
from .dock.dock_fusion_analysis import DockFusionAnalysis


class Worker(QObject):
    data_loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sfb = None

    def __del__(self):
        # Delete the SeafoilBag object
        self.sfb.save_configuration()
        self.sfb = None

    def loading_data(self, filepath, offset_date, win):
        win.showMaximized()

        self.data_loaded.emit("Loading data")
        self.sfb = SeafoilBag(filepath, offset_date)

        tab = QtWidgets.QTabWidget()

        QApplication.processEvents()

        ## Data
        dock_data = DockData(self.sfb, tab)
        self.data_loaded.emit("Dock Data loaded")

        dock_data_observer = DockDataObserver(self.sfb, tab)
        self.data_loaded.emit("Dock Data Observer loaded")

        dock_log = DockLog(self.sfb, tab)
        self.data_loaded.emit("Dock Log loaded")

        data_gnss = DockGnss(self.sfb, tab, win)
        self.data_loaded.emit("Dock GNSS loaded")

        data_analysis = DockAnalysis(self.sfb, tab, win)
        self.data_loaded.emit("Dock Analysis loaded")

        data_fusion_analysis = DockFusionAnalysis(self.sfb, tab, data_analysis)
        self.data_loaded.emit("Dock Fusion Analysis loaded")

        tab.setCurrentWidget(data_analysis)

        win.setWindowTitle("log - " + self.sfb.file_name)
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
        self.loading_label = QtWidgets.QLabel("Start Log Analyser")
        self.loading_label.setAlignment(QtCore.Qt.AlignCenter) # Set text to be centered
        self.setCentralWidget(self.loading_label)

        # Start loading_data fuction in a new thread
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.worker.data_loaded.connect(lambda msg: self.update_text(msg))
        self.thread.started.connect(lambda: self.worker.loading_data(filepath, offset_date, self))
        self.thread.start()

    def update_text(self, text):
        current_text = self.loading_label.text()
        self.loading_label.setText(current_text + "\n" + text)
        QApplication.processEvents()

    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        # Destroy the worker
        self.worker = None
        event.accept()

