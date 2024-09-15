# load a gpx file

import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData
import gpxpy
import gpxpy.gpx
from device.seafoil_connexion import correction_of_malformed_gpx

class SeafoilGpx(SeafoilData):
    def __init__(self, gpx_file_name="", data_folder=None):
        SeafoilData.__init__(self, gpx_file_name, data_folder=data_folder)

        self.topic_name = "fix_gpx"
        self.topic_name_dir = data_folder
        self.topic_full_dir = data_folder + "/" + self.topic_name + ".npz"

        self.k = 0
        self.nb_elements = 0
        self.ending_time = 0

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

        if self.is_loaded_from_file:
            self.load_message_from_file()
        else:
            self.load_message()


    def resize_data_array(self):
        self.time = np.resize(self.time,self.k)
        self.latitude = np.resize(self.latitude, self.k)
        self.longitude = np.resize(self.longitude, self.k)
        self.speed = np.resize(self.speed, self.k)
        self.track = np.resize(self.track, self.k)
        self.distance = np.resize(self.distance, self.k)
        self.mode = np.resize(self.mode, self.k)
        self.status = np.resize(self.status, self.k)
        self.time_gnss = np.resize(self.time_gnss, self.k)
        self.satellites_visible = np.resize(self.satellites_visible, self.k)

    def load_message(self):

        # open gpx file
        gpx_file = open(self.bag_path, 'r')
        # parse gpx file
        gpx = gpxpy.parse(correction_of_malformed_gpx(gpx_file.read()))

        self.nb_elements = len(gpx.tracks[0].segments[0].points)
        #self.start_date = gpx.tracks[0].segments[0].points[0].time
        self.starting_time = gpx.tracks[0].segments[0].points[0].time
        self.ending_time = gpx.tracks[0].segments[0].points[-1].time
        self.k = len(gpx.tracks[0].segments[0].points)
        self.resize_data_array()

        for i, point in enumerate(gpx.tracks[0].segments[0].points):
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
                self.speed[i] = point.speed_between(gpx.tracks[0].segments[0].points[i-1])
                self.track[i] = gpx.tracks[0].segments[0].points[i-1].course_between(point)
                # compute distance from previous point
                self.distance[i] = self.distance[i-1] + gpx.tracks[0].segments[0].points[i-1].distance_2d(point)

    def save_data(self):
        import os
        if not os.path.exists(self.topic_name_dir) and self.k > 0:
            os.makedirs(self.topic_name_dir)
        # Save data (compressed)
        if not os.path.exists(self.topic_full_dir):
            np.savez_compressed(self.topic_full_dir,
                                time=self.time+self.starting_time.timestamp(),
                                latitude=self.latitude,
                                longitude=self.longitude,
                                speed=self.speed,
                                track=self.track,
                                distance=self.distance,
                                mode=self.mode,
                                status=self.status,
                                time_gnss=self.time_gnss,
                                satellites_visible=self.satellites_visible,
                                )

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.utcfromtimestamp(data["time"][0])
        self.time = data["time"] - data["time"][0]
        self.latitude = data["latitude"]
        self.longitude = data["longitude"]
        self.speed = data["speed"]
        self.track = data["track"]
        self.distance = data["distance"]
        self.mode = data["mode"]
        self.status = data["status"]
        self.time_gnss = data["time_gnss"]
        self.satellites_visible = data["satellites_visible"]
        self.k = len(self.time)


