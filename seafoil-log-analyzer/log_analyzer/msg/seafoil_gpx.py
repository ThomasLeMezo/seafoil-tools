# load a gpx file

import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData
import gpxpy
import gpxpy.gpx

class SeafoilGpx(SeafoilData):
    def __init__(self, gpx_file_name=""):
        SeafoilData.__init__(self, gpx_file_name)

        self.gpx_file_name = gpx_file_name
        # open gpx file
        self.gpx_file = open(self.gpx_file_name, 'r')
        # parse gpx file
        self.gpx = gpxpy.parse(self.gpx_file)

        self.nb_elements = len(self.gpx.tracks[0].segments[0].points)
        #self.start_date = self.gpx.tracks[0].segments[0].points[0].time
        self.starting_time = self.gpx.tracks[0].segments[0].points[0].time
        self.k = 0

        self.time = np.empty([self.nb_elements])
        self.latitude = np.empty([self.nb_elements], dtype='double')
        self.longitude = np.empty([self.nb_elements], dtype='double')
        self.speed = np.empty([self.nb_elements], dtype='double')
        self.track = np.empty([self.nb_elements], dtype='double')
        self.distance = np.empty([self.nb_elements], dtype='double')
        self.mode = np.empty([self.nb_elements], dtype='int16')
        self.status = np.empty([self.nb_elements], dtype='int16')
        self.time_gnss = np.empty([self.nb_elements], dtype='double')
        self.satellites_visible = np.empty([self.nb_elements], dtype='int32')

        for i, point in enumerate(self.gpx.tracks[0].segments[0].points):
            self.time[i] = (point.time - self.starting_time).total_seconds()
            self.time_gnss[i] = point.time.timestamp()
            self.latitude[i] = point.latitude
            self.longitude[i] = point.longitude
            self.mode[i] = 3
            self.status[i] = 0
            self.satellites_visible[i] = 0

            if i == 0:
                self.speed[i] = 0
                self.track[i] = 0
                self.distance[i] = 0
            else:
                # compute speed/track with previous point
                self.speed[i] = point.speed_between(self.gpx.tracks[0].segments[0].points[i-1])
                self.track[i] = self.gpx.tracks[0].segments[0].points[i-1].course_between(point)
                # compute distance from previous point
                self.distance[i] = self.distance[i-1] + self.gpx.tracks[0].segments[0].points[i-1].distance_2d(point)
            self.k += 1


        # self.start_date = start_date
        # self.latitude = np.empty([self.nb_elements], dtype='double')
        # self.longitude = np.empty([self.nb_elements], dtype='double')
        # self.speed = np.empty([self.nb_elements], dtype='double')
        # self.track = np.empty([self.nb_elements], dtype='double')