#!/bin/python3
import collections
import os
import sys
import pyqtgraph as pg
from osgeo_utils.gdal2tiles import filename
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

from ..tools.seafoil_statistics import SeafoilStatistics
from .dock_analysis import add_slope, add_line


class DockComparison(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget, windows, list_sfb_comp):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Comparison")
        self.list_sfb_comp = list_sfb_comp

        self.ms_to_kt = 1.94384

        self.win = windows

        self.list_pg_yaw = []
        self.list_pg_roll_pitch = []

        self.add_heading_parameter()

        print("DockComparison initialized")

    def add_heading_parameter(self):
        dock_heading = Dock("Speed/Heading")
        self.addDock(dock_heading, position='below')

        color_matrix_list = [(0, 0, 255, 100), (0, 255, 0, 100), (255, 0, 0, 100), (255, 255, 0, 100), (255, 0, 255, 100), (0, 255, 255, 100)]

        pg_plot = pg.PlotWidget()
        dock_heading.addWidget(pg_plot)
        self.set_plot_options(pg_plot)
        for i, sfb in enumerate(self.list_sfb_comp):
            data_gnss = copy.copy(sfb.gps_fix)
            data_statistics = copy.copy(sfb.statistics)
            if not data_gnss.is_empty():

                spinBox = self.add_plot_relationship(data_gnss.track, data_statistics.speed, data_gnss.time, data_gnss.time,
                                                                            name_x="heading", name_y="velocity",
                                                                            unit_x="°", unit_y="kt",
                                                                            x_min=0.0, x_max=360.0, x_resolution=1.0, x_unit_conversion=1.0,
                                                                            y_min=12, y_max=42, y_resolution=0.1, y_unit_conversion=self.ms_to_kt,
                                                                            min_sample=0, enable_polyfit=False, polyndegree=1, enable_plot_curves=False,
                                                                            enable_plot_trajectory=True, normalize="one", modulo_x=True,
                                                                            color_matrix=color_matrix_list[i],
                                                                            pg_plot=pg_plot,
                                                                            file_bag_name=sfb.file_name,
                                                                            file_number=i)

                dock_heading.addWidget(spinBox)

        r2b_1, text_1 = add_slope([[10, 12], [10, 20]], unit="°/kt", line_color=(255, 255, 0), text_position=[0, 40])
        r2b_2, text_2 = add_slope([[-10, 12], [-10, 20]], unit="°/kt", line_color=(0, 255, 255), text_position=[0, 38])

        pg_plot.addItem(r2b_1)
        pg_plot.addItem(text_1)
        pg_plot.addItem(r2b_2)
        pg_plot.addItem(text_2)

        line_1, text_line_1 = add_line(180, unit="°", line_color=(255, 255, 0), text_position=[0, 36])
        line_2, text_line_2 = add_line(-180, unit="°", line_color=(0, 255, 255), text_position=[0, 34])

        pg_plot.addItem(line_1)
        pg_plot.addItem(text_line_1)
        pg_plot.addItem(line_2)
        pg_plot.addItem(text_line_2)

    def add_plot_relationship(self, data_x, data_y, data_x_time, data_y_time,
                              name_x = None, name_y = None, unit_x=None, unit_y=None,
                              x_min = None, x_max = None, x_resolution = None, x_unit_conversion = 1.0,
                              y_min = None, y_max = None, y_resolution = None, y_unit_conversion = 1.0,
                              min_sample=5, enable_polyfit=False, polyndegree=1,
                              enable_plot_curves=True, enable_plot_trajectory=False,
                              normalize = "max",
                              modulo_x = False,
                              color_matrix=(0, 0, 255, 1),
                              pg_plot=None,
                              file_bag_name=None,
                              file_number=0):

        # Example : x = data_gnss.speed, y = data_height.height, name_x = "speed", name_y = "height"

        # Interpolate data_y over data_x
        # Remove duplicates in data_y_time and associated data_y
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
                               color=[(0, 0, 0, 0), color_matrix],
                               mapping=pg.ColorMap.CLIP)
        pcmi = pg.PColorMeshItem(edgecolors=edgecolors, antialiasing=antialiasing, colorMap=colormap)
        x_pcmi = np.outer((x_vect - x_resolution/2.) * x_unit_conversion, np.ones(int((y_max-y_min) / y_resolution)))
        y_pcmi = np.outer(np.ones(len(x_vect)), np.arange(y_min, y_max, y_resolution) * y_unit_conversion)
        pcmi.setData(x_pcmi, y_pcmi, y_hist[:-1,:-1])

        # Add an entry in the legend for the current plot
        #legend_item = pg_plot.plotItem.legend.addItem(pcmi, file_bag_name) #generate bug?
        # Add a text to the plot and offset with file number and color matrix
        # Convert color to hex
        color_hex = '#%02x%02x%02x' % (color_matrix[0], color_matrix[1], color_matrix[2])
        text = pg.TextItem()
        text.setHtml(f'<div style="text-align: left"><span style="color: {color_hex};">{file_bag_name}</span></div>')
        text.setPos(-100, 40 - file_number)
        pg_plot.addItem(text)

        # Plot
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


            spinbox.sigValueChanged.connect(update_x_center)
            update_x_center()

        if spinbox is not None:
            return spinbox

