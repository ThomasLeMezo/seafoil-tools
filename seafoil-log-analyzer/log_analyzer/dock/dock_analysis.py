#!/bin/python3
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from pyqtgraph.dockarea import *
import numpy as np
from scipy import interpolate
import copy
import math

from .seafoil_dock import SeafoilDock
from ..tools.seafoil_relationship_plot import SeafoilRelationshipPlot

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

        self.spinbox_list = []
        self.timer_play = QtCore.QTimer()

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
        self.add_speed_heading()
        self.add_speed_heading_time()
        self.sandbox()

        # self.add_heading_velocity()

        # self.add_jibe_speed()

        print("DockAnalysis initialized")

    def __del__(self):
        self.timer_play.stop()

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


            speed_max, time_speed_max = self.sfb.statistics.get_max_speed_kt() #np.max(data_gnss.speed * (data_gnss.mode >= 3) * 1.94384)

            # Plot speed
            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data_gnss.time, data_gnss.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.plot([time_speed_max], [speed_max], pen=None, symbol='o', symbolBrush=(0, 0, 255),
                          symbolPen='w', symbolSize=10, name="max speed")
            pg_speed.setLabel('left', "speed (kt)")
            dock_height_velocity.addWidget(pg_speed)

            pg_speed_distance = pg.PlotWidget()
            self.set_plot_options(pg_speed_distance)
            if (np.size(self.sfb.statistics.speed_v500) > 5):
                pg_speed_distance.plot(data_distance.time, self.sfb.statistics.speed_v500[:-1] * 1.94384, pen=(0, 255, 0),
                                       name="speed 500m", stepMode=True)
            if (np.size(self.sfb.statistics.speed_v1852) > 5):
                pg_speed_distance.plot(data_distance.time, self.sfb.statistics.speed_v1852[:-1] * 1.94384, pen=(0, 0, 255),
                                       name="speed 1852m", stepMode=True)

            # Get idx and value of max speed for v500
            if (np.size(self.sfb.statistics.speed_v500) > 5):
                idx_max_speed_v500 = np.argmax(self.sfb.statistics.speed_v500)
                max_speed_v500 = self.sfb.statistics.speed_v500[idx_max_speed_v500]
                idx_start_v500 = self.sfb.statistics.get_starting_index_for_distance_from_last_point(data_distance, 500, idx_max_speed_v500)
                pg_speed_distance.plot([data_distance.time[idx_max_speed_v500]], [max_speed_v500 * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
                                       name="end speed 500m")
                pg_speed_distance.plot([data_distance.time[idx_start_v500]],
                                       [self.sfb.statistics.speed_v500[idx_start_v500] * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 255, 0), symbolPen='w', symbolSize=10,
                                       name="start speed 500m")

            # Get idx and value of max speed for v1852
            if (np.size(self.sfb.statistics.speed_v1852) > 5):
                idx_max_speed_v1852 = np.argmax(self.sfb.statistics.speed_v1852)
                max_speed_v1852 = self.sfb.statistics.speed_v1852[idx_max_speed_v1852]
                idx_start_v1852 = self.sfb.statistics.get_starting_index_for_distance_from_last_point(data_distance, 1852,
                                                                                  idx_max_speed_v1852)
                pg_speed_distance.plot([data_distance.time[idx_max_speed_v1852]], [max_speed_v1852 * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 0, 255), symbolPen='w', symbolSize=10,
                                       name="end speed 1852m")
                pg_speed_distance.plot([data_distance.time[idx_start_v1852]],
                                       [self.sfb.statistics.speed_v1852[idx_start_v1852] * 1.94384], pen=None,
                                       symbol='o', symbolBrush=(0, 0, 255), symbolPen='w', symbolSize=10,
                                       name="start speed 1852m")

            pg_speed_distance.setLabel('left', "speed of distance (kt)")
            dock_height_velocity.addWidget(pg_speed_distance)

            pg_speed_distance.setXLink(self.pg_speed)
            pg_speed_distance.setXLink(pg_speed)

            self.add_label_time([pg_speed, pg_speed_distance], data_gnss.starting_time, dock_height_velocity)
            if (np.size(self.sfb.statistics.speed_v1852) > 5):
                self.add_label_with_text(dock_height_velocity,
                                         "Max speed for 500m: " + str(round(max_speed_v500 * 1.94384, 2)) + " kt")
            if (np.size(self.sfb.statistics.speed_v1852) > 5):
                self.add_label_with_text(dock_height_velocity,
                                         "Max speed for 1852m: " + str(round(max_speed_v1852 * 1.94384, 2)) + " kt")
            self.add_label_with_text(dock_height_velocity, "Max speed: " + str(round(speed_max, 2)) + " kt")

            # from pyqtgraph.Qt import QtGui, QtCore
            # saveBtn = QtGui.QPushButton('Export GPX (for BaseDeVitesse)')
            # saveBtn.clicked.connect(self.save_gpx)
            # dock_height_velocity.addWidget(saveBtn, row=dock_height_velocity.currentRow + 1, col=0)


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


    def update_spinbox_value(self, value, spinbox_calling):
        for spinbox in self.spinbox_list:
            if spinbox != spinbox_calling:
                print("update spinbox value" + str(value) + spinbox.objectName())
                spinbox.setValue(value)

    def add_plot_relationship(self, data_x, data_y, data_x_time, data_y_time,
                              name_x = None, name_y = None, unit_x=None, unit_y=None,
                              x_min = None, x_max = None, x_resolution = None, x_unit_conversion = 1.0,
                              y_min = None, y_max = None, y_resolution = None, y_unit_conversion = 1.0,
                              min_sample=5, enable_polyfit=False, polyndegree=1,
                              enable_plot_curves=True, enable_plot_trajectory=False,
                              normalize = "max",
                              modulo_x = False):

        # Example : x = data_gnss.speed, y = data_height.height, name_x = "speed", name_y = "height"
        # Example : x = data_gnss.track, y = data_gnss.speed, name_x = "track", name_y = "speed"

        # Interpolate data_y over data_x
        data_y_time, idx = np.unique(data_y_time, return_index=True)
        data_y = data_y[idx]
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
            idx = np.where((data_x.data >= x) & (data_x.data < (x + x_resolution)))
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
                                color=[(0, 0, 255, 0), (255, 255, 0, 100)],
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
            spinbox.setValue(int(self.sfb.configuration["analysis"]["wind_heading"]))
            # Set wrap to True to allow the value to wrap around the limits
            spinbox.setWrapping(True)
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

                # Find the max value of the histogram
                # Find the indices of all '1's in the matrix (transposed)
                # Get the first last of '1' by row, which is closest to the top ([-1])
                # Get the column ([1])
                try:
                    max_hist_positive = (np.argwhere(np.transpose(y_hist_local[x_vect_local >= 0]))[-1][1]+1)*x_resolution
                    max_hist_negative = 180 - (np.argwhere(np.transpose(y_hist_local[x_vect_local < 0]))[-1][1]+1)*x_resolution

                    max_hist_positive_value = (np.argwhere(np.transpose(y_hist_local[x_vect_local >= 0]))[-1][0])*y_resolution + y_min
                    max_hist_negative_value = (np.argwhere(np.transpose(y_hist_local[x_vect_local < 0]))[-1][0])*y_resolution + y_min

                    # Add in the legend the max value of the histogram (round to 2 decimals
                    pg_plot.setTitle(f"Max left: {max_hist_negative*x_unit_conversion} [{max_hist_negative_value*y_unit_conversion:.2f} kt] "
                                     f"Max right: {max_hist_positive*x_unit_conversion} [{max_hist_positive_value*y_unit_conversion:.2f} kt]")
                except:
                    pg_plot.setTitle("Max left: (error) Max right: (error)")

                self.sfb.configuration["analysis"]["wind_heading"] = float(spinbox.value())
                # print("Wind heading", spinbox.value(), self.sfb.configuration["analysis"]["wind_heading"])

                self.update_spinbox_value(spinbox.value(), spinbox)


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

    def add_speed_heading(self):
        dock_heading = Dock("Speed/Heading")
        self.addDock(dock_heading, position='below')

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_statistics = copy.copy(self.sfb.statistics)

        if not data_gnss.is_empty():

            [pg_heading_velocity, spinBox] = self.add_plot_relationship(data_gnss.track, data_statistics.speed, data_gnss.time, data_gnss.time,
                                                             name_x="heading", name_y="velocity",
                                                             unit_x="°", unit_y="kt",
                                                             x_min=0.0, x_max=360.0, x_resolution=1.0, x_unit_conversion=1.0,
                                                             y_min=12, y_max=42, y_resolution=0.1, y_unit_conversion=self.ms_to_kt,
                                                             min_sample=0, enable_polyfit=False, polyndegree=1, enable_plot_curves=False,
                                                             enable_plot_trajectory=True, normalize="one", modulo_x=True)
            dock_heading.addWidget(pg_heading_velocity)
            dock_heading.addWidget(spinBox)
            self.spinbox_list.append(spinBox)


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

    def add_speed_heading_time(self):
        dock_heading_time = Dock("Speed/Heading - Time")
        self.addDock(dock_heading_time, position='below')

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_statistics = copy.copy(self.sfb.statistics)

        if not data_gnss.is_empty():
            srp = SeafoilRelationshipPlot(data_gnss.track, data_statistics.speed, data_gnss.time, data_gnss.time, self.sfb, enable_interpolation=False)
            srp.set_x_parameters("heading", "°", 0.0, 360.0, 1.0, 1.0)
            srp.set_y_parameters("velocity", "kt", 12, 42, 0.1, self.ms_to_kt)
            srp.set_min_sample(0, normalize="one")
            srp.plot_options(enable_plot_stat_curves=False, enable_plot_trajectory=True, modulo_x=True)

            [pg_heading_velocity, spinBox, pushButton] = srp.generate_plot_relationship()

            dock_heading_time.addWidget(pg_heading_velocity)
            dock_heading_time.addWidget(spinBox)
            self.spinbox_list.append(spinBox)

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

            # Add a graphics with speed
            pg_speed = pg.PlotWidget()
            self.set_plot_options(pg_speed)
            pg_speed.plot(data_gnss.time, data_gnss.speed[:-1] * 1.94384, pen=(255, 0, 0), name="speed", stepMode=True)
            pg_speed.setLabel('left', "speed (kt)")
            dock_heading_time.addWidget(pg_speed)

            # Add a Region of Interest
            roi = pg.LinearRegionItem([data_gnss.time[0], data_gnss.time[-1]])
            pg_speed.addItem(roi, ignoreBounds=True)
            roi.sigRegionChanged.connect(lambda: srp.update_time(roi.getRegion()))
            # roi.setClipItem(pg_speed)

            dock_heading_time.addWidget(pushButton)

            def move_region_of_interest(roi, time_step=1.0):
                region = roi.getRegion()
                roi.setRegion([region[0]+time_step, region[1]+time_step])

            # Create a Qt Timer
            self.timer_play.timeout.connect(lambda: move_region_of_interest(roi, self.timer_play.interval()*1e-3))

            # Create a push button to move the region of interest
            push_button_play = QtWidgets.QPushButton('Start playing')

            def push_button_play_action():
                if not self.timer_play.isActive():
                    self.timer_play.start(500)
                    # Set text to stop
                    push_button_play.setText("Stop playing")
                else:
                    self.timer_play.stop()
                    # Set text to start
                    push_button_play.setText("Start playing")

            # First click start, second click stop
            push_button_play.clicked.connect(push_button_play_action)
            dock_heading_time.addWidget(push_button_play)

    def sandbox(self):
        dock_sandbox = Dock("WindDirection")
        self.addDock(dock_sandbox, position='below')

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_statistics = copy.copy(self.sfb.statistics)
        srp = SeafoilRelationshipPlot(data_gnss.track, data_statistics.speed, data_gnss.time, data_gnss.time, self.sfb, enable_interpolation=False)
        srp.set_x_parameters("heading", "°", 0.0, 360.0, 1.0, 1.0)
        y_resolution = 0.5
        srp.set_y_parameters("velocity", "kt", 12, 42, y_resolution, self.ms_to_kt)
        srp.set_min_sample(0, normalize="one")
        srp.plot_options(enable_plot_stat_curves=False, enable_plot_trajectory=True, modulo_x=True)
        srp.preprocess_data()
        srp.compute_histogram()
        # copy the y_hist
        y_hist = srp.y_hist
        # delete srp
        del srp

        heading = np.arange(0, 360, 1)
        score_heading = np.zeros(len(heading))

        def compute_fold(heading_index, use_xor = True):
            # Cut the histogram y_hist in two parts (left and right)
            y_hist_modulo = np.concatenate((y_hist[heading_index:], y_hist[:heading_index]), axis=0)
            # threshold the first part with the mirrored second part
            if use_xor:
                # y_fold = np.logical_xor(y_hist_modulo[:180], np.flip(y_hist_modulo[180:], axis=0))
                y_fold = np.logical_or(y_hist_modulo[:180], np.flip(y_hist_modulo[180:], axis=0))
            else:
                y_fold = np.maximum(y_hist_modulo[:180], np.flip(y_hist_modulo[180:], axis=0))
            # Create a 2D matrix with a gradient from 0 to 1 in the x direction
            x = np.arange(0, len(y_fold[0]))
            y = np.arange(0, len(y_fold))
            xx, yy = np.meshgrid(x, y)
            y_fold = (2 + 1.0/(1+(yy/len(y_fold[0]))**2)) * y_fold
            return y_fold

        for i, h in enumerate(heading):
            # Sum the result
            score_heading[i] = np.sum(compute_fold(h))

        # Get the index of the minimum score
        heading_score_min = heading[np.argmin(score_heading)]
        print("Minimum score at heading", heading_score_min, "with a score of", np.min(score_heading))

        # Plot
        pg_plot = pg.PlotWidget()
        self.set_plot_options(pg_plot)
        pg_plot.plot(heading, score_heading[:-1], pen=(255, 0, 0), name="score", stepMode=True)
        pg_plot.setLabel('left', "score")
        dock_sandbox.addWidget(pg_plot)

        # Create a pyqtgraph line at the minimum score
        line = pg.InfiniteLine(pos=heading_score_min, angle=90, movable=False, pen=(0, 255, 0))
        pg_plot.addItem(line)

        # Add a label with the heading of the minimum score
        label = pg.TextItem(html=f"<div style='text-align: center'><span style='color: #FF0'>Heading: {heading_score_min}°</span></div>")
        pg_plot.addItem(label)

        # Plot the pcmi with the minimum score
        edgecolors = None
        antialiasing = False
        colormap = pg.ColorMap(pos=[0., 1.0],
                               color=[(0, 0, 255, 0), (255, 255, 0, 100)],
                               mapping=pg.ColorMap.CLIP)
        pcmi = pg.PColorMeshItem(edgecolors=edgecolors, antialiasing=antialiasing, colorMap=colormap)

        y_fold_pcmi = compute_fold(heading_score_min, False)
        x = np.arange(0, len(y_fold_pcmi))
        y = np.arange(12, 42, y_resolution)
        x_pcmi = np.outer((x - 0.5) * 1.0, np.ones(len(y)))
        y_pcmi = np.outer(np.ones(len(x)), np.arange(12, 42, y_resolution) * 1.0)
        pcmi.setData(x_pcmi, y_pcmi, y_fold_pcmi[:-1, :-1])

        # Create a new plot and add the pcmi
        pg_plot_pcmi = pg.PlotWidget()
        self.set_plot_options(pg_plot_pcmi)
        pg_plot_pcmi.addItem(pcmi)
        dock_sandbox.addWidget(pg_plot_pcmi)


