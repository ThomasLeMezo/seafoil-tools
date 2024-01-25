#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
from .seafoil_dock import SeafoilDock
import numpy as np
from scipy import signal, interpolate
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QInputDialog
import datetime
import copy


class DockGnss(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget, windows):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "GNSS")
        self.win = windows

        self.add_position()
        self.add_fix()
        self.add_time()

        print("DockGnss initialized")

    def save_gpx(self):
        import gpxpy.gpx

        data_gnss = self.sfb.gps_fix
        data_height = self.sfb.height
        data_imu = copy.copy(self.sfb.rpy)

        gpx = gpxpy.gpx.GPX()
        is_fix_mode = False

        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_segments = []

        # interpolate data_height to data_gnss.time_gnss
        f_height = interpolate.interp1d(data_height.time, data_height.height, bounds_error=False, kind="zero")
        height = f_height(data_gnss.time)
        print(height)

        f_imu_roll = interpolate.interp1d(data_imu.time, data_imu.roll, bounds_error=False, kind="zero")
        roll = f_imu_roll(data_gnss.time)

        f_imu_pitch = interpolate.interp1d(data_imu.time, data_imu.pitch, bounds_error=False, kind="zero")
        pitch = f_imu_pitch(data_gnss.time)

        # remplace nan by 0
        height[np.isnan(height)] = 0

        # Set roll and pitch to 0 when they are too high, too low or nan
        roll[np.isnan(roll)] = 0
        roll[roll > 70.] = 70.
        roll[roll < -70.] = -70.

        pitch[np.isnan(pitch)] = 0
        pitch[pitch > 70.] = 70.
        pitch[pitch < -70.] = -70.

        # smooth data
        window_size = 100
        height = np.convolve(height, np.ones(window_size)/window_size, mode='same')
        roll = np.convolve(roll, np.ones(window_size)/window_size, mode='same')

        window_size = 100
        height = np.convolve(height, np.ones(window_size)/window_size, mode='same')

        print(self.sfb.seafoil_id)
        filepath = QFileDialog.getSaveFileName(self.win, "Save file",
                                               str(data_gnss.bag_path) + "_" + self.sfb.seafoil_id + ".gpx",
                                               "GPX (*.gpx)")
        print(filepath)
        if filepath[0] == '':
            return

        for i in range(len(data_gnss.latitude)):
            if data_gnss.mode[i] > 0:
                if not is_fix_mode:
                    gpx_segments.append(gpxpy.gpx.GPXTrackSegment())
                    is_fix_mode = True

                pt = gpxpy.gpx.GPXTrackPoint(latitude=data_gnss.latitude[i],
                                             longitude=data_gnss.longitude[i],
                                             elevation=height[i],
                                             time=datetime.datetime.fromtimestamp(
                                                 data_gnss.time_gnss[i]),
                                             horizontal_dilution=roll[i],
                                             vertical_dilution=pitch[i],
                                             speed=data_gnss.speed[i],
                                             comment=str(data_gnss.mode[i])
                                             )
                pt.course = data_gnss.track[i]
                gpx_segments[-1].points.append(pt)
            else:
                is_fix_mode = False

        for seg in gpx_segments:
            gpx_track.segments.append(seg)
        gpx.tracks.append(gpx_track)

        file = open(filepath[0], "w")
        file.write(gpx.to_xml(version='1.1'))
        file.close()
        print("start date", data_gnss.time_gnss[0])

    def add_position(self):
        dock_position = Dock("GNSS")
        self.addDock(dock_position, position='below')
        data = self.sfb.gps_fix

        if (not data.is_empty()):
            pg_position = pg.PlotWidget()
            mask = np.where(data.mode > 0)
            pg_position.plot(data.longitude[mask], data.latitude[mask][:-1], pen=(255, 0, 0), name="position",
                             stepMode=True, symbol='+')

            dock_position.addWidget(pg_position)

            saveBtn = QtGui.QPushButton('Export GPX')
            saveBtn.clicked.connect(self.save_gpx)
            dock_position.addWidget(saveBtn, row=1, col=0)

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
