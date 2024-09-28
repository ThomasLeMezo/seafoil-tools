import copy

import numpy as np
import argparse
import os
from ..seafoil_bag import SeafoilBag
import math
import pyqtgraph as pg
from skimage.morphology import opening, closing, square, area_closing, area_opening, diamond, disk, erosion, dilation, binary_dilation, binary_erosion

class SeafoilHeadingComputation:
    def __init__(self, sfb, win=None):
        self.sfb = sfb
        self.ms_to_knot = 1.94384

        self.win = win

        data_gnss = copy.copy(self.sfb.gps_fix)
        data_statistics = copy.copy(self.sfb.statistics)

        self.heading = data_gnss.track
        self.speed = self.ms_to_knot * data_statistics.speed
        self.time = data_gnss.time
        self.heading_resolution = 1.0
        self.min_sample = 10
        self.speed_min = 12.0
        self.speed_max = 42.0
        self.speed_resolution = 0.2
        self.normalize = "one"
        self.speed_hist = None
        self.speed_hist_morph = None
        self.heading_vect = None

        self.compute_histogram()
        self.apply_morphological_filter()
        self.plot_histogram()

    def compute_histogram(self):
        self.heading_vect = np.arange(0, 360, self.heading_resolution)
        self.speed_hist = np.zeros([len(self.heading_vect), int((self.speed_max-self.speed_min)/self.speed_resolution)])
        for i, heading_step in enumerate(self.heading_vect):
            idx_heading = np.where((self.heading >= heading_step) & (self.heading < (heading_step + self.heading_resolution)))
            if len(idx_heading[0]) > 0:
                speed_data = self.speed[idx_heading]

                # Get histogram of speed
                for speed_val in speed_data[np.where((speed_data >= self.speed_min) & (speed_data < self.speed_max))]:
                    idx_speed = math.floor((speed_val - self.speed_min) / (self.speed_max - self.speed_min) * len(self.speed_hist[0]))
                    if len(self.speed_hist[0]) > idx_speed >= 0:
                        self.speed_hist[i, idx_speed] += 1

                # Normalize histogram
                if self.normalize == "max":
                    max_hist = np.max(self.speed_hist[i])
                    if max_hist > 0:
                        self.speed_hist[i] = self.speed_hist[i] / max_hist
                elif self.normalize == "one":
                    self.speed_hist[i] = self.speed_hist[i] > 0


    def apply_morphological_filter(self):
        # Apply a morphological filter to the histogram
        # This is useful to remove noise from the histogram
        #self.speed_hist = opening(self.speed_hist, square(2))
        # Convert to binary image
        self.speed_hist_morph = self.speed_hist > 0
        footprint = disk(4)
        number_of_iterations = 10

        self.speed_hist_morph = binary_dilation(self.speed_hist_morph, footprint)
        for _ in range(2):
            self.speed_hist_morph = binary_erosion(self.speed_hist_morph, footprint)

        for _ in range(number_of_iterations):
            self.speed_hist_morph = binary_dilation(self.speed_hist_morph, footprint)
        for _ in range(number_of_iterations):
            self.speed_hist_morph = binary_erosion(self.speed_hist_morph, footprint)
        # self.speed_hist_morph = opening(self.speed_hist_morph, square(factor))
        # Convert back to histogram
        self.speed_hist_morph = self.speed_hist_morph.astype(int)

    def plot_histogram(self):
        # Plot the histogram using pyqtgraph

        edgecolors   = None
        antialiasing = False
        colormap = pg.ColorMap(pos=[0., 1.0],
                               color=[(0, 0, 0, 0), (0, 255, 255, 100)],
                               mapping=pg.ColorMap.CLIP)
        pcmi = pg.PColorMeshItem(edgecolors=edgecolors, antialiasing=antialiasing, colorMap=colormap)
        x_pcmi = np.outer((self.heading_vect), np.ones(int((self.speed_max-self.speed_min) / self.speed_resolution)))
        y_pcmi = np.outer(np.ones(len(self.heading_vect)), np.arange(self.speed_min, self.speed_max, self.speed_resolution))

        pcmi.setData(x_pcmi, y_pcmi, self.speed_hist[:-1,:-1])

        colormap2 = pg.ColorMap(pos=[0., 1.0],
                               color=[(0, 0, 0, 0), (255, 255, 255, 100)],
                               mapping=pg.ColorMap.CLIP)
        pcmi2 = pg.PColorMeshItem(edgecolors=edgecolors, antialiasing=antialiasing, colorMap=colormap2)
        pcmi2.setData(x_pcmi, y_pcmi, self.speed_hist_morph[:-1,:-1])

        # Add the plot to the window
        p1 = pg.PlotWidget()
        p1.addItem(pcmi)
        p1.addItem(pcmi2)
        p1.setLabel('left', "Speed", units='knots')
        p1.setLabel('bottom', "Heading", units='degrees')
        p1.showGrid(True, True)
        self.win.setCentralWidget(p1)

        # Set win size
        self.win.resize(1024, 768)