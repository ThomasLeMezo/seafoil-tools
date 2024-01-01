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
        self.add_profile_filter()

        print("DockDataObserver initialized")

    def add_profile(self):
        dock_profile = Dock("Profile")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.height_debug)

        if not data.is_empty():

            #pg_profile = pg.GraphicsLayoutWidget()
            pg_profile = pg.PlotWidget()

            i2 = pg.ImageItem(image=data.profile)
            pg_profile.addItem( i2, title='' )

            # inserted color bar also works with labels on the right.
            # p2.showAxis('left')
            # p2.getAxis('left').setStyle( showValues=False )
            # p2.getAxis('bottom').setLabel('time')
            # p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values = (0, 1),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits = (0, None),
                rounding=0.01,
                orientation = 'h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80',
                interactive = False
            )
            bar.setImageItem( i2 )

            temperatureKelvin = 12.0 + 273.15
            gamma = 1.4
            R = 287.0
            speedOfSound = np.sqrt(gamma * R * temperatureKelvin)
            idx_to_height = 4.096e-3*speedOfSound/128.0
            height_to_pixel = (np.shape(data.profile)[1])
            pixel_times = np.arange(np.size(data.height_unfiltered))

            self.set_plot_options(pg_profile)
            pg_profile.plot(pixel_times, data.height_unfiltered/idx_to_height, pen=pg.mkPen('g', width=5), name="height_unfiltered")
            pg_profile.plot(pixel_times, data.height_unfiltered[:-1]/idx_to_height+(data.interval_diam[:-1]/2.), pen=(0, 0, 255), name="interval max", stepMode=True)
            pg_profile.plot(pixel_times, data.height_unfiltered[:-1]/idx_to_height-(data.interval_diam[:-1]/2.), pen=(0, 0, 255), name="interval min", stepMode=True)
            pg_profile.showGrid(x=False, y=True)
            dock_profile.addWidget(pg_profile)

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

    def add_profile_filter(self):
        dock_profile_filter = Dock("Height")
        self.addDock(dock_profile_filter, position='below')
        data_debug = copy.copy(self.sfb.height_debug)
        data = copy.copy(self.sfb.height)

        if not data.is_empty():
            pg_profile = pg.PlotWidget()
            self.set_plot_options(pg_profile)
            pg_profile.plot(data.time, data.height[:-1], pen=(255, 0, 0), name="height", stepMode=True)
            pg_profile.plot(data_debug.time, data_debug.height_unfiltered[:-1], pen=(0, 255, 0), name="height unfiltered", stepMode=True)
            pg_profile.setLabel('left', "status")
            dock_profile_filter.addWidget(pg_profile)