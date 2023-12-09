#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
from .seafoil_dock import SeafoilDock
import numpy as np
from scipy import signal, interpolate

class DockData(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Raw Data")

        self.add_profile()
        self.add_profile2()

        print("DockData initialized")

    def add_profile(self):
        dock_profile = Dock("Profile (default)")
        self.addDock(dock_profile, position='below')
        data = self.sfb.profile

        if not data.is_empty():

            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(1,0, 1,1, title="interactive")
            p2.addItem( i2, title='' )
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle( showValues=False )
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values = (0, 255),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits = (0, None),
                rounding=1,
                orientation = 'h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem( i2, insert_in=p2 )
            dock_profile.addWidget(pg_profile)

    def add_profile2(self):
        dock_profile = Dock("Profile (zero)")
        self.addDock(dock_profile, position='below')
        data = self.sfb.profile

        if not data.is_empty():

            # compute the mean of the first 10 profiles
            mean_profile = np.mean(data.profile[0:10,:], axis=0)
            # subtract the mean from all profiles
            data.profile = data.profile - mean_profile
            # for each profile, normalize the maximum to 255
            for i in range(data.nb_elements):
                data.profile[i,:] = data.profile[i,:] / np.max(data.profile[i,:]) * 255

            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(1,0, 1,1, title="interactive")
            p2.addItem( i2, title='' )
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle( showValues=True )
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values = (0, 255),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits = (0, None),
                rounding=1,
                orientation = 'h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem( i2, insert_in=p2 )
            dock_profile.addWidget(pg_profile)