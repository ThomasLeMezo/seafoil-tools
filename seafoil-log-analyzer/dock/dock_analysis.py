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

from PyQt5.QtWidgets import QFileDialog, QInputDialog
import datetime
import gpxpy.gpx


def compute_speed_for_distance(data_distance, distance):
    speed_distance = None
    if not data_distance.is_empty():
        # Compute the speed for 500 m
        speed_distance = np.zeros(len(data_distance.distance))
        d0_idx_last = 0
        for d1_idx in range(1, len(data_distance.distance)):
            d1 = data_distance.distance[d1_idx]
            d0 = data_distance.distance[d0_idx_last]
            if (d1 - d0) >= distance:
                for d0_idx in range(d0_idx_last, d1_idx):
                    d0 = data_distance.distance[d0_idx]
                    if d1 - d0 <= distance:
                        dt = data_distance.time[d1_idx] - data_distance.time[d0_idx]
                        if dt > 0:
                            speed_distance[d1_idx] = (d1 - d0) / dt
                        else:
                            speed_distance[d1_idx] = 0
                        d0_idx_last = max(0, d0_idx - 1)
                        break
    return speed_distance


def get_starting_index_for_distance_from_last_point(data_distance, distance, ending_idx):
    starting_idx = 0
    d1 = data_distance.distance[ending_idx]
    for d0_idx in range(ending_idx, 0, -1):
        d0 = data_distance.distance[d0_idx]
        if d1 - d0 >= distance:
            return d0_idx
    return starting_idx


class DockAnalysis(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget, windows):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Analysis")

        self.win = windows

        self.list_pg_yaw = []
        self.list_pg_roll_pitch = []

        self.speed_v500 = compute_speed_for_distance(self.sfb.distance, 500)
        self.speed_v1852 = compute_speed_for_distance(self.sfb.distance, 1852)

        self.pg_profile, self.pg_speed = self.plot_height_velocity()

        self.add_height_velocity()
        self.add_heading()
        self.add_speed_for_distance()
        self.add_polar_heading()

        print("DockAnalysis initialized")

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
                                    data_speed[:-1] > 4.0) + (data_speed[:-1] <= 4.0) * 0.28, pen=(0, 0, 255),
                            name="height filter (2s)",
                            stepMode=True)
            window_size = 100
            pg_profile.plot(data.time,
                            np.convolve(data.height[:-1], np.ones(window_size) / window_size, mode='same') * (
                                    data_speed[:-1] > 4.0) + (data_speed[:-1] <= 4.0) * 0.28, pen=(255, 0, 255),
                            name="height filter (4s)",
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

    def add_height_velocity(self):
        dock_height_velocity = Dock("Height velocity")
        self.addDock(dock_height_velocity, position='below')

        dock_height_velocity.addWidget(self.pg_profile)
        dock_height_velocity.addWidget(self.pg_speed)

        data = copy.copy(self.sfb.height)
        data_gnss = copy.copy(self.sfb.gps_fix)
        data_imu = copy.copy(self.sfb.rpy)

        if not data.is_empty():
            pg_imu = pg.PlotWidget()
            window_size = 100
            self.set_plot_options(pg_imu)
            pg_imu.plot(data_imu.time, data_imu.roll[:-1], pen=(255, 0, 0), name="roll", stepMode=True)
            pg_imu.plot(data_imu.time, data_imu.pitch[:-1], pen=(0, 255, 0), name="pitch", stepMode=True)
            pg_imu.plot(data_imu.time, np.convolve(data_imu.roll[:-1], np.ones(window_size) / window_size, mode='same'),
                        pen=(0, 0, 255), name="roll filter (2s)", stepMode=True)
            pg_imu.plot(data_imu.time,
                        np.convolve(data_imu.pitch[:-1], np.ones(window_size) / window_size, mode='same'),
                        pen=(255, 0, 255), name="pitch filter (2s)", stepMode=True)
            pg_imu.showGrid(x=True, y=True)
            dock_height_velocity.addWidget(pg_imu)
            pg_imu.setXLink(self.pg_profile)

            self.list_pg_roll_pitch.append(pg_imu)

            self.add_label_time([self.pg_speed, self.pg_profile, pg_imu], data_gnss.starting_time, dock_height_velocity)

    def add_heading(self):
        dock_heading = Dock("Heading")
        self.addDock(dock_heading, position='below')
        data_gnss = copy.copy(self.sfb.gps_fix)
        data_imu = copy.copy(self.sfb.rpy)

        pg_profile, pg_speed = self.plot_height_velocity()
        dock_heading.addWidget(pg_profile)
        dock_heading.addWidget(pg_speed)

        pg_track = pg.PlotWidget()
        self.set_plot_options(pg_track)
        pg_track.plot(data_gnss.time, data_gnss.track[:-1], pen=(255, 0, 0), name="track (gnss)", stepMode=True)
        pg_track.plot(data_imu.time, data_imu.yaw[:-1], pen=(0, 255, 0), name="yaw (imu)", stepMode=True)
        pg_track.setLabel('left', "track")
        dock_heading.addWidget(pg_track)
        pg_track.setXLink(pg_profile)

        self.list_pg_yaw.append(pg_track)

        self.add_label_time([pg_speed, pg_profile, pg_track], data_gnss.starting_time, dock_heading)

    def add_speed_for_distance(self):
        dock_height_velocity = Dock("Speed for a distance")
        self.addDock(dock_height_velocity, position='below')
        data_debug = copy.copy(self.sfb.height_debug)
        data = copy.copy(self.sfb.height)
        data_gnss = copy.copy(self.sfb.gps_fix)
        data_imu = copy.copy(self.sfb.rpy)
        data_distance = copy.copy(self.sfb.distance)

        if not data.is_empty():

            speed_max = np.max(data_gnss.speed * (data_gnss.mode >= 3) * 1.94384)
            speed_max_idx = np.argmax(data_gnss.speed * (data_gnss.mode >= 3) * 1.94384)

            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data_gnss.time, data_gnss.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.plot([data_gnss.time[speed_max_idx]], [speed_max], pen=None, symbol='o', symbolBrush=(0, 0, 255),
                          symbolPen='w', symbolSize=10, name="max speed")
            pg_speed.setLabel('left', "speed (kt)")
            dock_height_velocity.addWidget(pg_speed)

            pg_speed_distance = pg.PlotWidget()
            self.set_plot_options(pg_speed_distance)
            if (np.size(self.speed_v500) > 5):
                pg_speed_distance.plot(data_distance.time, self.speed_v500[:-1] * 1.94384, pen=(0, 255, 0),
                                       name="speed 500m", stepMode=True)
            if (np.size(self.speed_v1852) > 5):
                pg_speed_distance.plot(data_distance.time, self.speed_v1852[:-1] * 1.94384, pen=(0, 0, 255),
                                       name="speed 1852m", stepMode=True)

            # Get idx and value of max speed for v500
            if (np.size(self.speed_v500) > 5):
                idx_max_speed_v500 = np.argmax(self.speed_v500)
                max_speed_v500 = self.speed_v500[idx_max_speed_v500]
                idx_start_v500 = get_starting_index_for_distance_from_last_point(data_distance, 500, idx_max_speed_v500)
                pg_speed_distance.plot([data_distance.time[idx_max_speed_v500]], [max_speed_v500 * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(255, 0, 0), symbolPen='w', symbolSize=10,
                                       name="end speed 500m")
                pg_speed_distance.plot([data_distance.time[idx_start_v500]],
                                       [self.speed_v500[idx_start_v500] * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
                                       name="start speed 500m")

            # Get idx and value of max speed for v1852
            if (np.size(self.speed_v1852) > 5):
                idx_max_speed_v1852 = np.argmax(self.speed_v1852)
                max_speed_v1852 = self.speed_v1852[idx_max_speed_v1852]
                idx_start_v1852 = get_starting_index_for_distance_from_last_point(data_distance, 1852,
                                                                                  idx_max_speed_v1852)
                pg_speed_distance.plot([data_distance.time[idx_max_speed_v1852]], [max_speed_v1852 * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(255, 0, 0), symbolPen='w', symbolSize=10,
                                       name="end speed 1852m")
                pg_speed_distance.plot([data_distance.time[idx_start_v1852]],
                                       [self.speed_v1852[idx_start_v1852] * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
                                       name="start speed 1852m")

            pg_speed_distance.setLabel('left', "speed of distance (kt)")
            dock_height_velocity.addWidget(pg_speed_distance)

            pg_speed_distance.setXLink(self.pg_speed)
            pg_speed.setXLink(self.pg_speed)

            self.add_label_time([pg_speed, pg_speed_distance], data_gnss.starting_time, dock_height_velocity)
            if (np.size(self.speed_v1852) > 5):
                self.add_label_with_text(dock_height_velocity,
                                         "Max speed for 500m: " + str(round(max_speed_v500 * 1.94384, 2)) + " kt")
            if (np.size(self.speed_v1852) > 5):
                self.add_label_with_text(dock_height_velocity,
                                         "Max speed for 1852m: " + str(round(max_speed_v1852 * 1.94384, 2)) + " kt")
            self.add_label_with_text(dock_height_velocity, "Max speed: " + str(round(speed_max, 2)) + " kt")

            from pyqtgraph.Qt import QtGui, QtCore
            saveBtn = QtGui.QPushButton('Export GPX (for BaseDeVitesse)')
            saveBtn.clicked.connect(self.save_gpx)
            dock_height_velocity.addWidget(saveBtn, row=dock_height_velocity.currentRow + 1, col=0)

    def save_gpx(self):

        data_gnss = self.sfb.gps_fix
        data_height = self.sfb.height
        data_imu = copy.copy(self.sfb.rpy)

        gpx = gpxpy.gpx.GPX()
        gpx.creator = "SeaFoil"
        is_fix_mode = False

        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = "Windfoil session"
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
        height = np.convolve(height, np.ones(window_size) / window_size, mode='same')
        roll = np.convolve(roll, np.ones(window_size) / window_size, mode='same')

        window_size = 100
        height = np.convolve(height, np.ones(window_size) / window_size, mode='same')

        print(self.sfb.seafoil_id)
        filepath = QFileDialog.getSaveFileName(self.win, "Save file",
                                               str(data_gnss.bag_path) + "_" + self.sfb.seafoil_id + ".gpx",
                                               "GPX (*.gpx)")
        print(filepath)
        if filepath[0] == '':
            return

        # Apply an opening to data_gnss.mode[i] by enlarging of 25 sample when mode is less than 3
        kernel_size_after = 25 * 10  # 10s after
        kernel_size_before = 25 * 2  # 2s before
        mode = data_gnss.mode
        mode_filtered = mode.copy()

        for i, mode_val in enumerate(mode):
            if mode_val < 3:
                start_index = max(0, i - kernel_size_before)
                end_index = min(len(mode), i + kernel_size_after + 1)
                mode_filtered[start_index:end_index] = 0

        for i in range(len(data_gnss.latitude)):
            if mode_filtered[i] >= 3:  # Fix mode
                if not is_fix_mode:
                    gpx_segments.append(gpxpy.gpx.GPXTrackSegment())
                    is_fix_mode = True

                pt = gpxpy.gpx.GPXTrackPoint(latitude=data_gnss.latitude[i],
                                             longitude=data_gnss.longitude[i],
                                             #elevation=height[i],
                                             time=datetime.datetime.fromtimestamp(
                                                 data_gnss.time_gnss[i]),
                                             # horizontal_dilution=roll[i],
                                             # vertical_dilution=pitch[i],
                                             speed=data_gnss.speed[i],
                                             # comment=str(data_gnss.mode[i])
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

    def add_polar_heading(self):
        dock_polar_heading = Dock("Polar heading")
        self.addDock(dock_polar_heading, position='below')

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_height = copy.copy(self.sfb.height)

        # filter by 2s data_gnss
        window_size = 100
        data_gnss.speed = np.convolve(data_gnss.speed, np.ones(window_size) / window_size, mode='same')
        data_gnss.track = np.convolve(data_gnss.track, np.ones(window_size) / window_size, mode='same')

        # filter by 2s data_height
        window_size = 100
        data_height.height = np.convolve(data_height.height, np.ones(window_size) / window_size, mode='same')

        # interpolate data_height to data_gnss.time_gnss
        f_height = interpolate.interp1d(data_height.time, data_height.height, bounds_error=False, kind="zero")
        height = f_height(data_gnss.time)

        min_sample = 10

        # For each heading, compute the mean speed, max speed
        resolution = 1
        min_velocity_kt = 12.0
        ms_to_kt = 1.94384
        min_velocity = min_velocity_kt / ms_to_kt
        heading = np.arange(0, 360, resolution)
        speed_mean = np.zeros(len(heading))  # Speed mean function of the heading
        speed_max = np.zeros(len(heading))  # Speed max function of the heading
        speed_min = np.zeros(len(heading))  # Speed min function of the heading
        for i, h in enumerate(heading):
            idx = np.where(
                (data_gnss.track >= h) & (data_gnss.track < h + resolution) & (data_gnss.speed > min_velocity))
            if len(idx[0]) > min_sample:
                speed_mean[i] = np.mean(data_gnss.speed[idx])
                speed_max[i] = np.max(data_gnss.speed[idx])
                speed_min[i] = np.min(data_gnss.speed[idx])

        # Compute the mean and max height function of heading
        height_mean = np.zeros(len(heading))
        height_max = np.zeros(len(heading))
        height_min = np.zeros(len(heading))
        for i, h in enumerate(heading):
            idx = np.where(
                (data_gnss.track >= h) & (data_gnss.track < h + resolution) & (data_gnss.speed > min_velocity))
            if len(idx[0]) > min_sample:
                height_mean[i] = np.mean(height[idx])
                height_max[i] = np.max(height[idx])
                height_min[i] = np.min(height[idx])

        # Compute the mean and max height function of speed
        resolution = 0.1
        speed_vect = np.arange(min_velocity, 23, resolution) # 23 m/s in kt = 44.6 kt
        height_mean_speed = np.zeros(len(speed_vect))
        height_max_speed = np.zeros(len(speed_vect))
        height_min_speed = np.zeros(len(speed_vect))
        for i, s in enumerate(speed_vect):
            idx = np.where((data_gnss.speed >= s) & (data_gnss.speed < s + resolution))
            if len(idx[0]) > min_sample:
                height_mean_speed[i] = np.mean(height[idx])
                height_max_speed[i] = np.max(height[idx])
                height_min_speed[i] = np.min(height[idx])

        # plot
        pg_polar_heading = pg.PlotWidget()
        self.set_plot_options(pg_polar_heading)
        pg_polar_heading.plot(heading, speed_mean[:-1]*ms_to_kt, pen=(255, 0, 0), name="speed mean", stepMode=True)
        pg_polar_heading.plot(heading, speed_max[:-1]*ms_to_kt, pen=(0, 255, 0), name="speed max", stepMode=True)
        pg_polar_heading.plot(heading, speed_min[:-1]*ms_to_kt, pen=(0, 0, 255), name="speed min", stepMode=True)
        pg_polar_heading.setLabel('left', "speed (kt)")
        dock_polar_heading.addWidget(pg_polar_heading)

        pg_polar_heading_height = pg.PlotWidget()
        self.set_plot_options(pg_polar_heading_height)
        pg_polar_heading_height.plot(heading, height_mean[:-1], pen=(255, 0, 0), name="height mean", stepMode=True)
        pg_polar_heading_height.plot(heading, height_max[:-1], pen=(0, 255, 0), name="height max", stepMode=True)
        pg_polar_heading_height.plot(heading, height_min[:-1], pen=(0, 0, 255), name="height min", stepMode=True)
        pg_polar_heading_height.setLabel('left', "height (m)")
        dock_polar_heading.addWidget(pg_polar_heading_height)
        pg_polar_heading_height.setXLink(pg_polar_heading)

        pg_polar_heading_speed = pg.PlotWidget()
        self.set_plot_options(pg_polar_heading_speed)
        pg_polar_heading_speed.plot(speed_vect * ms_to_kt, height_mean_speed[:-1], pen=(255, 0, 0), name="height mean", stepMode=True)
        pg_polar_heading_speed.plot(speed_vect * ms_to_kt, height_max_speed[:-1], pen=(0, 255, 0), name="height max", stepMode=True)
        pg_polar_heading_speed.plot(speed_vect * ms_to_kt, height_min_speed[:-1], pen=(0, 0, 255), name="height min", stepMode=True)
        pg_polar_heading_speed.setLabel('left', "height (m)")
        dock_polar_heading.addWidget(pg_polar_heading_speed)
