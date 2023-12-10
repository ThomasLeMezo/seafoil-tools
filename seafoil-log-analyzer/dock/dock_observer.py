#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
from .seafoil_dock import SeafoilDock
import numpy as np
from scipy import signal, interpolate
import copy

class DockDataObserver(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Observer")

        self.add_profile()
        self.add_profile_one()

        print("DockDataObserver initialized")

    def add_profile(self):
        dock_profile = Dock("Profile")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.height_debug)

        if not data.is_empty():

            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(0,0, title="interactive")
            p2.addItem( i2, title='' )
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle( showValues=False )
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values = (0, 1),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits = (0, None),
                rounding=0.01,
                orientation = 'h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem( i2, insert_in=p2 )
            dock_profile.addWidget(pg_profile)

            temperatureKelvin = 12.0 + 273.15
            gamma = 1.4
            R = 287.0
            speedOfSound = np.sqrt(gamma * R * temperatureKelvin)
            idx_to_height = 4.096e-3*speedOfSound/128.0

            pg_height_unfiltered = pg.PlotWidget()
            pg_height_unfiltered.plot(data.time, data.height_unfiltered[:-1], pen=(255, 0, 0), name="height_unfiltered", stepMode=True)
            pg_height_unfiltered.plot(data.time, data.height_unfiltered[:-1]+(data.interval_diam[:-1]/2.)*idx_to_height, pen=(0, 255, 0), name="status", stepMode=True)
            pg_height_unfiltered.plot(data.time, data.height_unfiltered[:-1]-(data.interval_diam[:-1]/2.)*idx_to_height, pen=(0, 255, 0), name="status", stepMode=True)
            pg_height_unfiltered.setLabel('left', "status")
            dock_profile.addWidget(pg_height_unfiltered)

    def add_profile_one(self):
        dock_profile_one = Dock("Profile one")
        self.addDock(dock_profile_one, position='below')
        data = copy.copy(self.sfb.height_debug)
        i = 10

        if not data.is_empty():
            pg_profile = pg.PlotWidget()
            pg_profile.plot(np.arange(128), data.profile[i,:-1], pen=(255, 0, 0), name="signal", stepMode=True)
            pg_profile.setLabel('left', "status")
            dock_profile_one.addWidget(pg_profile)