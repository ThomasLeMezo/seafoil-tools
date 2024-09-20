#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
from .seafoil_dock import SeafoilDock
import numpy as np
from scipy import interpolate
from pyqtgraph.Qt import QtGui, QtCore
import copy


class DockGnss(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget, windows):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "GNSS")
        self.win = windows

        self.add_position()
        self.add_fix()
        self.add_time()
        self.add_gnss_debug()
        self.add_gnss_filter()

        print("DockGnss initialized")

    def add_position(self):
        dock_position = Dock("GNSS")
        self.addDock(dock_position, position='below')
        data = self.sfb.gps_fix

        if (not data.is_empty()):
            pg_position = pg.PlotWidget()
            mask = np.where(data.mode > 0)
            pg_position.plot(data.longitude[mask], data.latitude[mask], pen=(255, 0, 0), name="position", symbol='+')

            dock_position.addWidget(pg_position)

    def add_fix(self):
        dock_fix = Dock("Fix")
        self.addDock(dock_fix, position='below')
        data = self.sfb.gps_fix

        if (not data.is_empty()):
            # pg_status = pg.PlotWidget()
            # pg_status.plot(data.time, data.status[:-1], pen=(255, 0, 0), name="status", stepMode=True)
            # pg_status.setLabel('left', "status")
            # dock_fix.addWidget(pg_status)

            pg_mode = pg.PlotWidget()
            self.set_plot_options(pg_mode)
            pg_mode.plot(data.time, data.mode[:-1], pen=(255, 0, 0), name="mode", stepMode=True)
            pg_mode.plot(data.time, data.status[:-1], pen=(0, 255, 0), name="status", stepMode=True)
            pg_mode.setLabel('left', "mode & status")
            dock_fix.addWidget(pg_mode)
            # pg_mode.setXLink(pg_status)

            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data.time, data.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.setLabel('left', "speed (kt)")
            dock_fix.addWidget(pg_speed)
            pg_speed.setXLink(pg_mode)

            pg_track = pg.PlotWidget()
            self.set_plot_options(pg_track)
            pg_track.plot(data.time, data.track[:-1], pen=(255, 0, 0), name="track", stepMode=True)
            pg_track.setLabel('left', "track")
            dock_fix.addWidget(pg_track)
            pg_track.setXLink(pg_mode)

            # pg_nb_sat = pg.PlotWidget()
            # pg_nb_sat.plot(data.time, data.satellites_visible[:-1], pen=(255, 0, 0), name="satellites_visible",
            #                stepMode=True)
            # pg_nb_sat.setLabel('left', "satellites visible")
            # dock_fix.addWidget(pg_nb_sat)
            # pg_nb_sat.setXLink(pg_mode)

    def add_time(self):
        dock_time = Dock("Time")
        self.addDock(dock_time, position='below')
        data = self.sfb.gps_fix

        if (not data.is_empty()):
            pg_time = pg.PlotWidget()
            pg_time.plot(data.time, ((data.starting_time.timestamp() + data.time) - data.time_gnss)[:-1],
                         pen=(255, 0, 0), name="time offset", stepMode=True)
            pg_time.setLabel('left', "time error with GNSS")
            dock_time.addWidget(pg_time)

    def add_gnss_debug(self):
        dock_gnss_debug = Dock("debug")
        self.addDock(dock_gnss_debug, position='below')
        data = self.sfb.gps_fix

        if (not data.is_empty()):
            pg_mode = pg.PlotWidget()
            self.set_plot_options(pg_mode)
            pg_mode.plot(data.time, data.mode[:-1], pen=(255, 0, 0), name="mode", stepMode=True)
            pg_mode.plot(data.time, data.status[:-1], pen=(0, 255, 0), name="status", stepMode=True)
            pg_mode.setLabel('left', "mode & status")
            dock_gnss_debug.addWidget(pg_mode)

            pg_gnss_debug = pg.PlotWidget()
            pg_gnss_debug.plot(data.time, data.satellites_visible[:-1], pen=(255, 0, 0), name="satellites_visible",
                               stepMode=True)
            pg_gnss_debug.setLabel('left', "satellites visible")
            dock_gnss_debug.addWidget(pg_gnss_debug)
            pg_gnss_debug.setXLink(pg_mode)

    def add_gnss_filter(self):
        dock_gnss_filter = Dock("gnss filter")
        self.addDock(dock_gnss_filter, position='below')
        data = self.sfb.gps_fix

        if (not data.is_empty()):
            time_interp = np.arange(data.time[0], data.time[-1], 1)
            # interpolate with mean
            f_speed = interpolate.interp1d(data.time, data.speed, bounds_error=False, kind="linear")
            speed = f_speed(time_interp)

            ms_to_knot = 1.94384
            # Filter the speed by max acceleration allowed
            acceleration = np.diff(speed) / np.diff(time_interp)
            acceleration = np.append(acceleration, 0)
            # Create a mask where absolute acceleration is less than 3 knots/s^2
            mask = np.abs(acceleration) > (3.0 / ms_to_knot)
            # Apply a convolution to all True values
            mask = np.convolve(mask, np.ones(5), mode='same')
            # opposite mask
            mask = np.logical_not(mask)

            # interpolate mask on the original time
            f_mask = interpolate.interp1d(time_interp, mask, bounds_error=False, kind="zero")
            mask_interp = f_mask(data.time)
            max_speed = max(data.speed*mask_interp)

            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(time_interp, (speed*mask*ms_to_knot)[:-1], pen=(255, 0, 0), name="speed (filter)", stepMode=True)
            pg_speed.plot(time_interp, (speed*ms_to_knot)[:-1], pen=(0, 0, 255), name="speed (interp)", stepMode=True)
            pg_speed.plot(data.time, (data.speed*ms_to_knot)[:-1], pen=(0, 255, 0), name="speed", stepMode=True)
            pg_speed.plot(data.time, (mask_interp*data.speed*ms_to_knot)[:-1], pen=(0, 255, 255), name="speed (mask)", stepMode=True)
            pg_speed.setLabel('left', "speed (kt)")
            dock_gnss_filter.addWidget(pg_speed)

            pg_acceleration = pg.PlotWidget()
            self.set_plot_options(pg_acceleration)
            pg_acceleration.plot(time_interp, (acceleration*ms_to_knot)[:-1], pen=(255, 0, 0), name="acceleration", stepMode=True)
            # Add line at 3 knots/s^2
            pg_acceleration.addLine(y=3, pen=pg.mkPen('g', width=2))
            pg_acceleration.setLabel('left', "acceleration")
            dock_gnss_filter.addWidget(pg_acceleration)
            pg_acceleration.setXLink(pg_speed)

            pg_mask = pg.PlotWidget()
            self.set_plot_options(pg_mask)
            pg_mask.plot(data.time, mask_interp[:-1], pen=(255, 0, 0), name="mask", stepMode=True)
            pg_mask.setLabel('left', "mask")
            dock_gnss_filter.addWidget(pg_mask)
            pg_mask.setXLink(pg_speed)
