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
        self.add_imu_height()
        self.add_distance()
        self.add_manoeuvre()
        self.add_distance_gate()

        print("DockDataObserver initialized")


    def plot_height_velocity(self):
        data_debug = copy.copy(self.sfb.height_debug)
        data = copy.copy(self.sfb.height)
        data_gnss = copy.copy(self.sfb.gps_fix)

        if not data.is_empty():
            # interp speed to height
            f_gnss_speed = interpolate.interp1d(data_gnss.time, data_gnss.speed, bounds_error=False, kind="zero")
            data_speed = f_gnss_speed(data.time)

            pg_profile = pg.PlotWidget()
            self.set_plot_options(pg_profile)
            pg_profile.plot(data_debug.time, data_debug.height_unfiltered[:-1], pen=(0, 255, 0),
                            name="height unfiltered", stepMode=True)
            window_size = 50
            pg_profile.plot(data.time,
                            np.convolve(data.height[:-1], np.ones(window_size) / window_size, mode='same') * (
                                    data_speed[:-1] > 4.0) + (data_speed[:-1] <= 4.0)*0.28, pen=(0, 0, 255), name="height filter (2s)",
                            stepMode=True)
            window_size = 100
            pg_profile.plot(data.time,
                            np.convolve(data.height[:-1], np.ones(window_size) / window_size, mode='same') * (
                                    data_speed[:-1] > 4.0) + (data_speed[:-1] <= 4.0)*0.28, pen=(255, 0, 255), name="height filter (4s)",
                            stepMode=True)
            #pg_profile.plot(data_gnss.time, data_gnss.altitude[:-1], pen=(255, 0, 0), name="height gnss", stepMode=True)

            pg_profile.setLabel('left', "height (m)")
            pg_profile.showGrid(x=True, y=True)
            # dock.addWidget(pg_profile)

            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data_gnss.time, data_gnss.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.setLabel('left', "speed (kt)")
            pg_speed.showGrid(x=True, y=True)
            # dock.addWidget(pg_speed)
            pg_speed.setXLink(pg_profile)

            return pg_profile, pg_speed
        else:
            return None, None

    # function to plota acceleration, gyro and velocity
    def add_imu_height(self):
        dock_imu_height = Dock("IMU/Height")
        self.addDock(dock_imu_height, position='below')
        data = self.sfb.calibrated_data

        pg_profile, pg_speed = self.plot_height_velocity()
        dock_imu_height.addWidget(pg_profile)
        dock_imu_height.addWidget(pg_speed)

        if not data.is_empty():
            pg_acceleration = pg.PlotWidget()
            self.set_plot_options(pg_acceleration)
            pg_acceleration.plot(data.time, data.accel_x, pen=(255, 0, 0), name="x")
            pg_acceleration.plot(data.time, data.accel_y, pen=(0, 255, 0), name="y")
            pg_acceleration.plot(data.time, data.accel_z, pen=(0, 0, 255), name="z")
            pg_acceleration.plot(data.time, np.sqrt(data.accel_x ** 2 + data.accel_y ** 2 + data.accel_z ** 2),
                                 pen=(255, 255, 255), name="norm")
            pg_acceleration.setLabel('left', "acceleration")
            dock_imu_height.addWidget(pg_acceleration)
            pg_acceleration.setXLink(pg_profile)

            pg_gyro = pg.PlotWidget()
            self.set_plot_options(pg_gyro)
            pg_gyro.plot(data.time, data.gyro_x, pen=(255, 0, 0), name="x")
            pg_gyro.plot(data.time, data.gyro_y, pen=(0, 255, 0), name="y")
            pg_gyro.plot(data.time, data.gyro_z, pen=(0, 0, 255), name="z")
            pg_gyro.setLabel('left', "gyro")
            dock_imu_height.addWidget(pg_gyro)
            pg_gyro.setXLink(pg_profile)

    def add_distance(self):
        dock_distance = Dock("Distance")
        self.addDock(dock_distance, position='below')
        data_distance = copy.copy(self.sfb.distance)

        pg_profile, pg_speed = self.plot_height_velocity()
        dock_distance.addWidget(pg_profile)
        dock_distance.addWidget(pg_speed)

        if not data_distance.is_empty():
            pg_distance = pg.PlotWidget()
            self.set_plot_options(pg_distance)
            pg_distance.plot(data_distance.time, data_distance.distance[:-1], pen=(255, 0, 0), name="distance", stepMode=True)
            pg_distance.setLabel('left', "distance")
            dock_distance.addWidget(pg_distance)
            pg_distance.setXLink(pg_profile)

    def add_manoeuvre(self):
        dock_manoeuvre = Dock("Manoeuvre")
        self.addDock(dock_manoeuvre, position='below')
        data_manoeuvre = copy.copy(self.sfb.manoeuvre)

        pg_profile, pg_speed = self.plot_height_velocity()
        dock_manoeuvre.addWidget(pg_speed)

        # Add track from GNSS
        data_gnss = copy.copy(self.sfb.gps_fix)
        if not data_gnss.is_empty():
            pg_track = pg.PlotWidget()
            self.set_plot_options(pg_track)
            pg_track.plot(data_gnss.time, data_gnss.track[:-1], pen=(255, 0, 0), name="track", stepMode=True)
            pg_track.setLabel('left', "track")
            dock_manoeuvre.addWidget(pg_track)
            pg_track.setXLink(pg_speed)

        if not data_manoeuvre.is_empty():
            pg_manoeuvre = pg.PlotWidget()
            self.set_plot_options(pg_manoeuvre)
            pg_manoeuvre.plot(data_manoeuvre.time, data_manoeuvre.heading_max_difference[:-1], pen=(255, 0, 0), name="manoeuvre", stepMode=True)
            pg_manoeuvre.setLabel('left', "manoeuvre")
            dock_manoeuvre.addWidget(pg_manoeuvre)
            pg_manoeuvre.setXLink(pg_speed)

            pg_state = pg.PlotWidget()
            self.set_plot_options(pg_state)
            pg_state.plot(data_manoeuvre.time, data_manoeuvre.state[:-1], pen=(255, 0, 0), name="state", stepMode=True)
            pg_state.setLabel('left', "state")
            dock_manoeuvre.addWidget(pg_state)
            pg_state.setXLink(pg_speed)

    # Add distance gate
    def add_distance_gate(self):
        dock_distance_gate = Dock("Distance Gate")
        self.addDock(dock_distance_gate, position='below')
        data_distance_gate = copy.copy(self.sfb.distance_gate)

        pg_profile, pg_speed = self.plot_height_velocity()
        dock_distance_gate.addWidget(pg_speed)

        if not data_distance_gate.is_empty():
            pg_distance_gate = pg.PlotWidget()
            self.set_plot_options(pg_distance_gate)
            pg_distance_gate.plot(data_distance_gate.time, data_distance_gate.distance_gate[:-1], pen=(255, 0, 0), name="distance gate", stepMode=True)
            pg_distance_gate.setLabel('left', "distance gate")
            dock_distance_gate.addWidget(pg_distance_gate)
            pg_distance_gate.setXLink(pg_speed)

    def add_profile(self):
        dock_profile = Dock("Profile")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.height_debug)

        if not data.is_empty():
            # pg_profile = pg.GraphicsLayoutWidget()
            pg_profile = pg.PlotWidget()

            i2 = pg.ImageItem(image=data.profile)
            pg_profile.addItem(i2, title='')

            # inserted color bar also works with labels on the right.
            # p2.showAxis('left')
            # p2.getAxis('left').setStyle( showValues=False )
            # p2.getAxis('bottom').setLabel('time')
            # p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values=(0, 1),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits=(0, None),
                rounding=0.01,
                orientation='h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80',
                interactive=False
            )
            bar.setImageItem(i2)

            temperatureKelvin = 12.0 + 273.15
            gamma = 1.4
            R = 287.0
            speedOfSound = np.sqrt(gamma * R * temperatureKelvin)
            idx_to_height = 4.096e-3 * speedOfSound / 128.0
            height_to_pixel = (np.shape(data.profile)[1])
            pixel_times = np.arange(np.size(data.height_unfiltered))

            self.set_plot_options(pg_profile)
            pg_profile.plot(pixel_times, data.height_unfiltered / idx_to_height, pen=pg.mkPen('g', width=5),
                            name="height_unfiltered")
            pg_profile.plot(pixel_times, data.height_unfiltered[:-1] / idx_to_height + (data.interval_diam[:-1] / 2.),
                            pen=(0, 0, 255), name="interval max", stepMode=True)
            pg_profile.plot(pixel_times, data.height_unfiltered[:-1] / idx_to_height - (data.interval_diam[:-1] / 2.),
                            pen=(0, 0, 255), name="interval min", stepMode=True)
            pg_profile.showGrid(x=False, y=True)
            dock_profile.addWidget(pg_profile)

    def add_profile_one(self):
        dock_profile_one = Dock("Profile one")
        self.addDock(dock_profile_one, position='below')
        data = copy.copy(self.sfb.height_debug)
        i = 10

        if not data.is_empty():
            pg_profile = pg.PlotWidget()
            pg_profile.plot(np.arange(128), data.profile[i, :-1], pen=(255, 0, 0), name="signal", stepMode=True)
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
            pg_profile.plot(data_debug.time, data_debug.height_unfiltered[:-1], pen=(0, 255, 0),
                            name="height unfiltered", stepMode=True)
            pg_profile.setLabel('left', "status")
            dock_profile_filter.addWidget(pg_profile)


