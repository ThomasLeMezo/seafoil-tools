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
                        d0_idx_last = max(0, d0_idx-1)
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
    def __init__(self, seafoil_bag, tabWidget):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Analysis")

        self.speed_v500 = compute_speed_for_distance(self.sfb.distance, 500)
        self.speed_v1852 = compute_speed_for_distance(self.sfb.distance, 1852)

        self.add_height_velocity()
        self.add_heading()
        self.add_speed_for_distance()

        print("DockAnalysis initialized")


    def plot_height_velocity(self, dock):
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
            pg_profile.setLabel('left', "status")
            pg_profile.showGrid(x=True, y=True)
            dock.addWidget(pg_profile)

            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data_gnss.time, data_gnss.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.setLabel('left', "speed (kt)")
            pg_speed.showGrid(x=True, y=True)
            dock.addWidget(pg_speed)

            pg_speed.setXLink(pg_profile)

            return pg_profile, pg_speed

    def add_height_velocity(self):
        dock_height_velocity = Dock("Height velocity")
        self.addDock(dock_height_velocity, position='below')

        pg_profile, pg_speed = self.plot_height_velocity(dock_height_velocity)

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
            pg_imu.setXLink(pg_profile)

            self.add_label_time([pg_speed, pg_profile, pg_imu], data_gnss.starting_time, dock_height_velocity)

    def add_heading(self):
        dock_heading = Dock("Heading")
        self.addDock(dock_heading, position='below')
        data_gnss = copy.copy(self.sfb.gps_fix)

        pg_profile, pg_speed = self.plot_height_velocity(dock_heading)

        pg_track = pg.PlotWidget()
        self.set_plot_options(pg_track)
        pg_track.plot(data_gnss.time, data_gnss.track[:-1], pen=(255, 0, 0), name="track", stepMode=True)
        pg_track.setLabel('left', "track")
        dock_heading.addWidget(pg_track)
        pg_track.setXLink(pg_profile)

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

            speed_max = np.max(data_gnss.speed*(data_gnss.mode>=3) * 1.94384)
            speed_max_idx = np.argmax(data_gnss.speed*(data_gnss.mode>=3) * 1.94384)

            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data_gnss.time, data_gnss.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.plot([data_gnss.time[speed_max_idx]], [speed_max], pen=None, symbol='o', symbolBrush=(0, 0, 255),
                          symbolPen='w', symbolSize=10, name="max speed")
            pg_speed.setLabel('left', "speed (kt)")
            dock_height_velocity.addWidget(pg_speed)

            pg_speed_distance = pg.PlotWidget()
            self.set_plot_options(pg_speed_distance)
            pg_speed_distance.plot(data_distance.time, self.speed_v500[:-1] * 1.94384, pen=(0, 255, 0),
                                   name="speed 500m", stepMode=True)
            pg_speed_distance.plot(data_distance.time, self.speed_v1852[:-1] * 1.94384, pen=(0, 0, 255),
                                   name="speed 1852m", stepMode=True)

            # Get idx and value of max speed for v500
            idx_max_speed_v500 = np.argmax(self.speed_v500)
            max_speed_v500 = self.speed_v500[idx_max_speed_v500]
            idx_start_v500 = get_starting_index_for_distance_from_last_point(data_distance, 500, idx_max_speed_v500)
            pg_speed_distance.plot([data_distance.time[idx_max_speed_v500]], [max_speed_v500 * 1.94384], pen=None,
                                   symbol='o', symbolBrush=(255, 0, 0), symbolPen='w', symbolSize=10,
                                   name="end speed 500m")
            pg_speed_distance.plot([data_distance.time[idx_start_v500]], [self.speed_v500[idx_start_v500] * 1.94384], pen=None,
                                      symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
                                      name="start speed 500m")

            # Get idx and value of max speed for v1852
            idx_max_speed_v1852 = np.argmax(self.speed_v1852)
            max_speed_v1852 = self.speed_v1852[idx_max_speed_v1852]
            idx_start_v1852 = get_starting_index_for_distance_from_last_point(data_distance, 1852, idx_max_speed_v1852)
            pg_speed_distance.plot([data_distance.time[idx_max_speed_v1852]], [max_speed_v1852 * 1.94384], pen=None,
                                   symbol='o', symbolBrush=(255, 0, 0), symbolPen='w', symbolSize=10,
                                   name="end speed 1852m")
            pg_speed_distance.plot([data_distance.time[idx_start_v1852]], [self.speed_v1852[idx_start_v1852] * 1.94384], pen=None,
                                      symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
                                      name="start speed 1852m")

            pg_speed_distance.setLabel('left', "speed of distance (kt)")
            dock_height_velocity.addWidget(pg_speed_distance)

            pg_speed_distance.setXLink(pg_speed)

            self.add_label_time([pg_speed, pg_speed_distance], data_gnss.starting_time, dock_height_velocity)
            self.add_label_with_text(dock_height_velocity, "Max speed for 500m: " + str(round(max_speed_v500 * 1.94384, 2)) + " kt")
            self.add_label_with_text(dock_height_velocity, "Max speed for 1852m: " + str(round(max_speed_v1852 * 1.94384, 2)) + " kt")
            self.add_label_with_text(dock_height_velocity, "Max speed: " + str(round(speed_max, 2)) + " kt")
