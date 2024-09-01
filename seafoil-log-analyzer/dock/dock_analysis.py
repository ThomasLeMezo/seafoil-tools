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
import math


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

def compute_diff_yaw(data_yaw, data_time, window_size):
    # Create vector with the same size as data_imu.yaw
    yaw = np.zeros(len(data_yaw))

    # Cumulative sum of the difference between two consecutive values of data_yaw with modulo 360
    for i in range(1, len(data_yaw)):
        diff = (data_yaw[i] - data_yaw[i - 1])
        yaw[i] = yaw[i - 1] + min(diff%360, 360 - diff%360)*np.sign(diff)

    yaw = np.convolve(yaw, np.ones(window_size) / window_size, mode='same')
    data_time = np.convolve(data_time, np.ones(3) / 3, mode='same')
    time_diff = np.diff(data_time)
    yaw_diff = np.diff(yaw) / time_diff

    return yaw, yaw_diff

def add_line(position_init=0, unit="", line_color = (255, 255, 255), text_position = [0, 40]):
    # Add an infinit movable vertical line
    r2b = pg.InfiniteLine(pos=position_init, angle=90, movable=True, pen=pg.mkPen(color=line_color, width=2))

    # Add a legend to the plot
    text = pg.TextItem()
    # convert color to string
    color = '#%02x%02x%02x' % line_color
    # set the html text with the color (span)
    heading = position_init
    marge = min(abs(180 - position_init), abs(position_init + 180))
    text.setHtml("<div style='text-align: center'><span style='color: " + color + ";'>heading: " + f"{heading:.1f}" + unit + "(" + f"{marge:.1f}" + unit + ")" + "</span></div>")

    text.setPos(text_position[0], text_position[1])

    def update():
        heading = r2b.value()
        marge = min(abs(180 - heading), abs(heading + 180))
        text.setHtml("<div style='text-align: center'><span style='color: " + color + ";'>heading: " + f"{heading:.1f}" + unit + "(" + f"{marge:.1f}" + unit + ")" + "</span></div>")

    r2b.sigPositionChanged.connect(update)

    return r2b, text


def add_slope(position_init, unit="", line_color = (255, 255, 255), text_position = [0, 40]):
    r2b = pg.LineSegmentROI(position_init, pen=pg.mkPen(color=line_color, width=2))

    # Add a legend to the plot
    text = pg.TextItem()
    # convert color to string
    color = '#%02x%02x%02x' % line_color
    # set the html text with the color (span)
    text.setHtml("<div style='text-align: center'><span style='color: " + color + ";'>slope: 0 " + unit + "</span></div>")
    text.setPos(text_position[0], text_position[1])

    def update_line():
        h1, h2 = r2b.getLocalHandlePositions()
        # x => heading, y => velocity
        p1 = [h1[-1].x(), h1[-1].y()]
        p2 = [h2[-1].x(), h2[-1].y()]
        # compute the slope
        slope_heading = 0.0
        if p2[0] - p1[0] != 0:
            slope_heading = (p2[0] - p1[0]) / (p2[1] - p1[1])

        # change the text of the legend with the slope and add a background color
        text.setHtml("<div style='text-align: center'><span style='color: " + color + ";'>slope: " + str(round(slope_heading, 2)) + " " + unit + "</span></div>")
        # Set the position of the text to the middle of the line

    r2b.sigRegionChanged.connect(update_line)
    r2b.sigRegionChangeFinished.connect(update_line)

    return r2b, text

class DockAnalysis(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget, windows):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Analysis")

        self.ms_to_kt = 1.94384

        self.win = windows

        self.list_pg_yaw = []
        self.list_pg_roll_pitch = []

        self.speed_v500 = compute_speed_for_distance(self.sfb.distance, 500)
        self.speed_v1852 = compute_speed_for_distance(self.sfb.distance, 1852)

        self.yaw = None
        self.yaw_diff = None
        data_gnss = copy.copy(self.sfb.gps_fix)
        if not data_gnss.is_empty():
            self.yaw, self.yaw_diff = compute_diff_yaw(data_gnss.track, data_gnss.time, 25*3)


        self.pg_profile, self.pg_speed = self.plot_height_velocity()

        self.add_height_velocity()
        self.add_heading()
        self.add_speed_for_distance()
        self.add_polar_heading()
        self.add_velocity()
        self.add_heading_parameter()

        # self.add_heading_velocity()

        # self.add_jibe_speed()

        print("DockAnalysis initialized")

    def plot_height_velocity(self):
        data_debug = copy.copy(self.sfb.height_debug)
        data = copy.copy(self.sfb.height)
        data_gnss = copy.copy(self.sfb.gps_fix)

        if not data.is_empty() and not data_gnss.is_empty():
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


        dock_height_velocity.addWidget(self.pg_profile)
        dock_height_velocity.addWidget(self.pg_speed)

        data = copy.copy(self.sfb.height)
        data_gnss = copy.copy(self.sfb.gps_fix)
        data_imu = copy.copy(self.sfb.rpy)

        if not data.is_empty() and not data_imu.is_empty() and not data_gnss.is_empty():
            self.addDock(dock_height_velocity, position='below')

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
        data_gnss = copy.copy(self.sfb.gps_fix)
        data_imu = copy.copy(self.sfb.rpy)

        if not data_gnss.is_empty() and not data_imu.is_empty():
            self.addDock(dock_heading, position='below')

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

            # plot the yaw_diff
            # if self.yaw is not None and self.yaw_diff is not None:
            #     pg_yaw_diff = pg.PlotWidget()
            #     self.set_plot_options(pg_yaw_diff)
            #     pg_yaw_diff.plot(data_gnss.time, self.yaw_diff, pen=(255, 0, 0), name="yaw diff", stepMode=True)
            #     pg_yaw_diff.setLabel('left', "yaw diff")
            #     dock_heading.addWidget(pg_yaw_diff)
            #     pg_yaw_diff.setXLink(pg_profile)
            #
            #     # plot yaw
            #     pg_yaw = pg.PlotWidget()
            #     self.set_plot_options(pg_yaw)
            #     pg_yaw.plot(data_gnss.time, self.yaw[:-1], pen=(255, 0, 0), name="yaw", stepMode=True)
            #     pg_yaw.setLabel('left', "yaw")
            #     dock_heading.addWidget(pg_yaw)
            #     pg_yaw.setXLink(pg_profile)

            self.add_label_time([pg_speed, pg_profile, pg_track], data_gnss.starting_time, dock_heading)

    def add_heading_velocity(self):
        dock_heading_velocity = Dock("Heading velocity")

        data_gnss = copy.copy(self.sfb.gps_fix)

        if not data_gnss.is_empty() :
            self.addDock(dock_heading_velocity, position='below')

            pg_yaw_diff_velocity = self.add_plot_relationship(data_gnss.speed, self.yaw_diff, data_gnss.time, data_gnss.time[:-1],
                                                            name_x="speed", name_y="yaw diff",
                                                            unit_x="kt", unit_y="°/s",
                                                            x_min=12.0, x_max=42.0, x_resolution=0.1, x_unit_conversion=self.ms_to_kt,
                                                            y_min=-30, y_max=30, y_resolution=1, y_unit_conversion=1.0,
                                                            min_sample=10, enable_polyfit=False, polyndegree=1)
            dock_heading_velocity.addWidget(pg_yaw_diff_velocity)



    def add_speed_for_distance(self):
        dock_height_velocity = Dock("Speed for a distance")

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_distance = copy.copy(self.sfb.distance)

        if not data_gnss.is_empty() and not data_distance.is_empty():
            self.addDock(dock_height_velocity, position='below')

            speed_max = np.max(data_gnss.speed * (data_gnss.mode >= 3) * 1.94384)
            speed_max_idx = np.argmax(data_gnss.speed * (data_gnss.mode >= 3) * 1.94384)

            # Plot speed
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
                                       symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
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
                                       symbol='o', symbolBrush=(0, 0, 255), symbolPen='w', symbolSize=10,
                                       name="end speed 1852m")
                pg_speed_distance.plot([data_distance.time[idx_start_v1852]],
                                       [self.speed_v1852[idx_start_v1852] * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 0, 255), symbolPen='w', symbolSize=10,
                                       name="start speed 1852m")

            pg_speed_distance.setLabel('left', "speed of distance (kt)")
            dock_height_velocity.addWidget(pg_speed_distance)

            pg_speed_distance.setXLink(self.pg_speed)
            pg_speed_distance.setXLink(pg_speed)

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
        data_wind = copy.copy(self.sfb.wind)

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

        # interpolate data_wind to data_gnss.time_gnss
        # f_wind_velocity = interpolate.interp1d(data_wind.time, data_wind.velocity, bounds_error=False, kind="zero")
        # wind_velocity = f_wind_velocity(data_gnss.time)

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
                                             # elevation=height[i],
                                             #elevation=wind_velocity[i],
                                             time=datetime.datetime.fromtimestamp(
                                                 data_gnss.time_gnss[i], datetime.timezone.utc),
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

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_height = copy.copy(self.sfb.height)

        if not data_gnss.is_empty() and not data_height.is_empty():
            self.addDock(dock_polar_heading, position='below')

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

            min_sample = 20

            # For each heading, compute the mean speed, max speed
            resolution = 1
            min_velocity_kt = 12.0

            min_velocity = min_velocity_kt / self.ms_to_kt
            heading = np.arange(0, 360, resolution)
            speed_mean = np.zeros(len(heading))  # Speed mean function of the heading
            speed_max = np.zeros(len(heading))  # Speed max function of the heading
            speed_min = np.zeros(len(heading))  # Speed min function of the heading
            for i, h in enumerate(heading):
                idx = np.where(
                    (data_gnss.track >= h) & (data_gnss.track < h + resolution) & (data_gnss.speed > min_velocity))
                if len(idx[0]) > min_sample:
                    speed_data = np.sort(copy.copy(data_gnss.speed[idx]))
                    speed_mean[i] = np.mean(speed_data)
                    speed_max[i] = np.mean(speed_data[int(len(speed_data) * 0.9):])
                    speed_min[i] = np.mean(speed_data[:int(len(speed_data) * 0.1)])

            # Compute the mean and max height function of heading
            height_mean = np.zeros(len(heading))
            height_max = np.zeros(len(heading))
            height_min = np.zeros(len(heading))
            for i, h in enumerate(heading):
                idx = np.where(
                    (data_gnss.track >= h) & (data_gnss.track < h + resolution) & (data_gnss.speed > min_velocity))
                if len(idx[0]) > min_sample:
                    height_data = np.sort(copy.copy(height[idx]))
                    height_mean[i] = np.mean(height_data)
                    height_max[i] = np.mean(height_data[int(len(height_data) * 0.9):])
                    height_min[i] = np.mean(height_data[:int(len(height_data) * 0.1)])

            ## ToDo : implement wind direction to replot the polar

            # plot
            pg_polar_heading = pg.PlotWidget()
            self.set_plot_options(pg_polar_heading)
            pg_polar_heading.plot(heading, speed_mean[:-1]*self.ms_to_kt, pen=(255, 0, 0), name="speed mean", stepMode=True)
            pg_polar_heading.plot(heading, speed_max[:-1]*self.ms_to_kt, pen=(0, 255, 0), name="speed max (10%)", stepMode=True)
            pg_polar_heading.plot(heading, speed_min[:-1]*self.ms_to_kt, pen=(0, 0, 255), name="speed min (10%)", stepMode=True)
            pg_polar_heading.setLabel('left', "speed (kt)")
            dock_polar_heading.addWidget(pg_polar_heading)

            pg_polar_heading_height = pg.PlotWidget()
            self.set_plot_options(pg_polar_heading_height)
            pg_polar_heading_height.plot(heading, height_mean[:-1], pen=(255, 0, 0), name="height mean", stepMode=True)
            pg_polar_heading_height.plot(heading, height_max[:-1], pen=(0, 255, 0), name="height max (10%)", stepMode=True)
            pg_polar_heading_height.plot(heading, height_min[:-1], pen=(0, 0, 255), name="height min (10%)", stepMode=True)
            pg_polar_heading_height.setLabel('left', "height (m)")
            dock_polar_heading.addWidget(pg_polar_heading_height)
            pg_polar_heading_height.setXLink(pg_polar_heading)


    def add_plot_relationship(self, data_x, data_y, data_x_time, data_y_time,
                              name_x = None, name_y = None, unit_x=None, unit_y=None,
                              x_min = None, x_max = None, x_resolution = None, x_unit_conversion = 1.0,
                              y_min = None, y_max = None, y_resolution = None, y_unit_conversion = 1.0,
                              min_sample=5, enable_polyfit=False, polyndegree=1,
                              enable_plot_curves=True, enable_plot_trajectory=False,
                              normalize = "max",
                              modulo_x = False):

        # Example : x = data_gnss.speed, y = data_height.height, name_x = "speed", name_y = "height"

        # Interpolate data_y over data_x
        f_y = interpolate.interp1d(data_y_time, data_y, bounds_error=False, kind="zero")
        y = f_y(data_x_time)

        x_min /= x_unit_conversion
        x_max /= x_unit_conversion
        x_resolution /= x_unit_conversion

        y_min /= y_unit_conversion
        y_max /= y_unit_conversion
        y_resolution /= y_unit_conversion

        x_vect = np.arange(x_min, x_max, x_resolution)

        # y stats
        y_stat_mean = np.zeros(len(x_vect))
        y_stat_max = np.zeros(len(x_vect))
        y_stat_min = np.zeros(len(x_vect))
        y_hist = np.zeros([len(x_vect), int((y_max - y_min) / y_resolution)])
        for i, x in enumerate(x_vect):
            idx = np.where((data_x.equipment_data >= x) & (data_x.equipment_data < (x + x_resolution)))
            if len(idx[0]) > min_sample:
                y_data = np.sort(y[idx])
                y_stat_mean[i] = np.mean(y_data)
                y_stat_max[i] = np.mean(y_data[int(len(y_data) * 0.9):])
                y_stat_min[i] = np.mean(y_data[:int(len(y_data) * 0.1)])

                # Get histogram of y
                for y_val in y_data[np.where((y_data >= y_min) & (y_data < y_max))]:
                    idx_y = math.floor((y_val - y_min) / (y_max - y_min) * len(y_hist[0]))
                    if len(y_hist[0]) > idx_y >= 0:
                        y_hist[i, idx_y] += 1

                # Normalize histogram
                if normalize == "max":
                    max_hist = np.max(y_hist[i])
                    if max_hist > 0:
                        y_hist[i] = y_hist[i] / max_hist
                elif normalize == "one":
                    y_hist[i] = y_hist[i] > 0

        # Add a polynomial fit to y_mean
        x_vect_fit = None
        x_polyfit = None
        if enable_polyfit:
            try:
                last_idx = np.where(y_stat_mean > 0)[0][-1]
                x_vect_fit = x_vect[:last_idx]
                z = np.polyfit(x_vect_fit, y_stat_mean[:last_idx], polyndegree)
                x_polyfit = np.poly1d(z)
            except Exception as e:
                print("Oops!  error ", e)
                enable_polyfit = False
                pass

        ##############################
        # Display 2D matrix of y with color

        edgecolors   = None
        antialiasing = False
        colormap = pg.ColorMap(pos=[0., 1.0],
                                color=[(0, 0, 255, 100), (255, 255, 0, 100)],
                                mapping=pg.ColorMap.CLIP)
        pcmi = pg.PColorMeshItem(edgecolors=edgecolors, antialiasing=antialiasing, colorMap=colormap)
        x_pcmi = np.outer((x_vect - x_resolution/2.) * x_unit_conversion, np.ones(int((y_max-y_min) / y_resolution)))
        y_pcmi = np.outer(np.ones(len(x_vect)), np.arange(y_min, y_max, y_resolution) * y_unit_conversion)
        pcmi.setData(x_pcmi, y_pcmi, y_hist[:-1,:-1])

        # Plot
        pg_plot = pg.PlotWidget()
        self.set_plot_options(pg_plot)
        if enable_plot_curves:
            if enable_polyfit:
                pg_plot.plot(x_vect_fit * x_unit_conversion, x_polyfit(x_vect_fit)[:-1] * y_unit_conversion, pen=(0, 255, 255), name="polyfit", stepMode=True)
            pg_plot.plot(x_vect * x_unit_conversion, y_stat_mean[:-1] * y_unit_conversion, pen=pg.mkPen((255, 0, 0), width=5), name=name_y + " mean", stepMode=True)
            pg_plot.plot(x_vect * x_unit_conversion, y_stat_max[:-1] * y_unit_conversion, pen=(0, 255, 0), name=name_y + " max (10%)", stepMode=True)
            pg_plot.plot(x_vect * x_unit_conversion, y_stat_min[:-1] * y_unit_conversion, pen=(0, 0, 255), name=name_y + " min (10%)", stepMode=True)
        pg_plot.addItem(pcmi)
        pg_plot.setLabel('left', name_y + " (" + unit_y + ")")

        plot_taj = None
        if enable_plot_trajectory:
            # Select index where the speed is greater than x_min
            idx = np.where(data_x > x_min)

            # Smooth the trajectory with a window of 4s
            # window_size = 4 * 25
            # y = np.convolve(y, np.ones(window_size) / window_size, mode='same')
            # data_x = np.convolve(data_x, np.ones(window_size) / window_size, mode='same')

            plot_taj = pg_plot.plot(data_x[idx]*x_unit_conversion, y[idx]*y_unit_conversion, pen=(255, 0, 0), name=name_y + " (filter 4s)", stepMode=False)
            # set the plot as invisible
            plot_taj.setVisible(False)

        spinbox = None
        if modulo_x:
            # Add a spin box to change the center value of the x axis
            spinbox = pg.SpinBox(value=x_min*x_unit_conversion, bounds=[x_min*x_unit_conversion, x_max*x_unit_conversion], step=x_resolution*x_unit_conversion)
            def update_x_center():
                half_range = (x_max - x_min)/2
                x_center = ((spinbox.value()/x_unit_conversion+(x_max - x_min)/2.)%(x_max - x_min))

                # find first index where x_vect_local > (x_max-x_min)/2.
                idx = np.where(x_vect > x_center)[0][0]

                # put the subarray of y_hist in the right order
                y_hist_local = np.concatenate((y_hist[idx:], y_hist[:idx]), axis=0)
                x_vect_local = np.arange(-half_range, half_range, x_resolution)

                x_pcmi = np.outer((x_vect_local + x_resolution) * x_unit_conversion, np.ones(int((y_max-y_min) / y_resolution)))
                y_pcmi = np.outer(np.ones(len(x_vect_local)), np.arange(y_min, y_max, y_resolution) * y_unit_conversion)
                pcmi.setData(x_pcmi, y_pcmi, y_hist_local[:-1,:-1])

                #
                # Apply modulo to x_vect
                data_x_copy = (data_x - x_center) % (x_max - x_min) - (x_max - x_min)/2.
                plot_taj.setData(data_x_copy*x_unit_conversion, y*y_unit_conversion)

            spinbox.sigValueChanged.connect(update_x_center)
            update_x_center()

        if spinbox is not None:
            return pg_plot, spinbox
        else:
            return pg_plot

    def add_velocity(self):
        dock_velocity = Dock("Velocity")

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_height = copy.copy(self.sfb.height)
        data_imu = copy.copy(self.sfb.rpy)

        if not data_gnss.is_empty() and not data_height.is_empty() and not data_imu.is_empty():
            self.addDock(dock_velocity, position='below')

            pg_height_velocity = self.add_plot_relationship(data_gnss.speed, data_height.height, data_gnss.time, data_height.time,
                                                                name_x="speed", name_y="height",
                                                                unit_x="kt", unit_y="m",
                                                                x_min=12.0, x_max=42.0, x_resolution=0.1, x_unit_conversion=self.ms_to_kt,
                                                                y_min=0.25, y_max=1.0, y_resolution=0.025, y_unit_conversion=1.0,
                                                                min_sample=10, enable_polyfit=True, polyndegree=1)
            dock_velocity.addWidget(pg_height_velocity)

            pg_roll_velocity = self.add_plot_relationship(data_gnss.speed, abs(data_imu.roll), data_gnss.time, data_imu.time,
                                                                name_x="speed", name_y="roll",
                                                                unit_x="kt", unit_y="°",
                                                                x_min=12.0, x_max=42.0, x_resolution=0.1, x_unit_conversion=self.ms_to_kt,
                                                                y_min=0, y_max=40, y_resolution=1, y_unit_conversion=1.0,
                                                                min_sample=10, enable_polyfit=False, polyndegree=1)
            dock_velocity.addWidget(pg_roll_velocity)
            pg_roll_velocity.setXLink(pg_height_velocity)

            pg_pitch_velocity = self.add_plot_relationship(data_gnss.speed, abs(data_imu.pitch), data_gnss.time, data_imu.time,
                                                                name_x="speed", name_y="pitch",
                                                                unit_x="kt", unit_y="°",
                                                                x_min=12.0, x_max=42.0, x_resolution=0.1, x_unit_conversion=self.ms_to_kt,
                                                                y_min=-20, y_max=20, y_resolution=1, y_unit_conversion=1.0,
                                                                min_sample=10, enable_polyfit=False, polyndegree=1)
            dock_velocity.addWidget(pg_pitch_velocity)
            pg_pitch_velocity.setXLink(pg_height_velocity)

    def add_heading_parameter(self):
        dock_heading = Dock("Heading2")
        self.addDock(dock_heading, position='below')

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_imu = copy.copy(self.sfb.rpy)

        if not data_gnss.is_empty():


            [pg_heading_velocity, spinBox] = self.add_plot_relationship(data_gnss.track, data_gnss.speed, data_gnss.time, data_gnss.time,
                                                             name_x="heading", name_y="velocity",
                                                             unit_x="°", unit_y="kt",
                                                             x_min=0.0, x_max=360.0, x_resolution=1.0, x_unit_conversion=1.0,
                                                             y_min=12, y_max=42, y_resolution=0.1, y_unit_conversion=self.ms_to_kt,
                                                             min_sample=0, enable_polyfit=False, polyndegree=1, enable_plot_curves=False,
                                                             enable_plot_trajectory=True, normalize="one", modulo_x=True)
            dock_heading.addWidget(pg_heading_velocity)
            dock_heading.addWidget(spinBox)


            r2b_1, text_1 = add_slope([[10, 12], [10, 20]], unit="°/kt", line_color=(255, 255, 0), text_position=[0, 40])
            r2b_2, text_2 = add_slope([[-10, 12], [-10, 20]], unit="°/kt", line_color=(0, 255, 255), text_position=[0, 38])

            pg_heading_velocity.addItem(r2b_1)
            pg_heading_velocity.addItem(text_1)
            pg_heading_velocity.addItem(r2b_2)
            pg_heading_velocity.addItem(text_2)

            line_1, text_line_1 = add_line(180, unit="°", line_color=(255, 255, 0), text_position=[0, 36])
            line_2, text_line_2 = add_line(-180, unit="°", line_color=(0, 255, 255), text_position=[0, 34])

            pg_heading_velocity.addItem(line_1)
            pg_heading_velocity.addItem(text_line_1)
            pg_heading_velocity.addItem(line_2)
            pg_heading_velocity.addItem(text_line_2)

        # if not data_imu.is_empty():
        #     pg_heading_roll = self.add_plot_relationship(data_gnss.track, abs(data_imu.roll), data_gnss.time, data_imu.time,
        #                                                  name_x="heading", name_y="roll",
        #                                                  unit_x="°", unit_y="°",
        #                                                  x_min=0.0, x_max=360.0, x_resolution=1, x_unit_conversion=1,
        #                                                  y_min=0, y_max=40, y_resolution=0.5, y_unit_conversion=1.0,
        #                                                  min_sample=10, enable_polyfit=False, polyndegree=1 )
        #     dock_heading.addWidget(pg_heading_roll)

            # pg_heading_roll.setXLink(pg_heading_velocity)

    # def add_jibe_speed(self):
    #     dock_jibe = Dock("Jibe speed")
    #     self.addDock(dock_jibe, position='below')
    #
    #     # For each value of heading find the index before such that the absolute variation of heading is greater than 180
    #     # And the difference of index is inferior to 20*25 (20s).
    #     max_window_size = 20 * 25
    #     jibe_angle = 150
    #
    #     data_gnss = copy.copy(self.sfb.gps_fix)
    #
    #     # Compute the heading variation
    #     heading_variation = data_gnss.track[:-1] - data_gnss.track[1:]
    #     # remove the value greater than 180
    #     heading_variation = np.where(heading_variation > 180, heading_variation - 360, heading_variation)
    #     heading_variation = np.where(heading_variation < -180, heading_variation + 360, heading_variation)
    #
    #     heading_accumulated = np.cumsum(heading_variation)
    #
    #     # For each accumulated heading find the index before such that the absolute variation of heading is greater than 180
    #     # And the difference of index is inferior to 20*25 (20s).
    #     jibe = np.zeros(len(heading_accumulated))
    #
    #     for i in range(len(heading_accumulated)):
    #         if i > max_window_size:
    #             for j in range(10*25, max_window_size+1):
    #                 if abs(heading_accumulated[i]-heading_accumulated[i-j]) >= 150:
    #                     # Compute the mean speed between i and j
    #                     jibe[i] = np.mean(data_gnss.speed[j:i])
    #                     break
    #
    #     # plot (speed, heading, jibe)
    #     pg_speed = pg.PlotWidget()
    #     self.set_plot_options(pg_speed)
    #     pg_speed.plot(data_gnss.time, (data_gnss.speed*self.ms_to_kt)[:-1], pen=(255, 0, 0), name="speed", stepMode=True)
    #     pg_speed.setLabel('left', "speed (m/s)")
    #     dock_jibe.addWidget(pg_speed)
    #
    #     pg_heading = pg.PlotWidget()
    #     self.set_plot_options(pg_heading)
    #     pg_heading.plot(data_gnss.time, data_gnss.track[:-1], pen=(255, 0, 0), name="heading", stepMode=True)
    #     pg_heading.setLabel('left', "heading (°)")
    #     dock_jibe.addWidget(pg_heading)
    #     pg_heading.setXLink(pg_speed)
    #
    #     pg_jibe = pg.PlotWidget()
    #     self.set_plot_options(pg_jibe)
    #     pg_jibe.plot(data_gnss.time, jibe*self.ms_to_kt, pen=(255, 0, 0), name="jibe speed", stepMode=True)
    #     pg_jibe.setLabel('left', "speed (kt)")
    #     dock_jibe.addWidget(pg_jibe)
    #     pg_jibe.setXLink(pg_speed)
    #
    #     pg_heading_acc = pg.PlotWidget()
    #     self.set_plot_options(pg_heading_acc)
    #     pg_heading_acc.plot(data_gnss.time, heading_accumulated, pen=(255, 0, 0), name="heading variation", stepMode=True)
    #     pg_heading_acc.setLabel('left', "heading variation (°)")
    #     dock_jibe.addWidget(pg_heading_acc)
    #     pg_heading_acc.setXLink(pg_speed)