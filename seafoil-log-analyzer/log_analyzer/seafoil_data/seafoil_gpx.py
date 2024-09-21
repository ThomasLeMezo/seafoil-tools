# load a gpx file
import re
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData
import gpxpy
import gpxpy.gpx

def correction_of_malformed_gpx(gpx_file_content):
    # remplace balise of the form *:* by *_* in the gpx file (only with letters around)
    gpx_file_content = re.sub(r'([a-zA-Z]):([a-zA-Z])', r'\1_\2', gpx_file_content)

    return gpx_file_content

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
            print("Load (saved)", self.topic_name)
            self.load_message_from_file()
        else:
            print("Load", self.topic_name)
            self.load_message()


    def resize_data_array(self):
        self.time = np.resize(self.time,self.nb_elements)
        self.latitude = np.resize(self.latitude, self.nb_elements)
        self.longitude = np.resize(self.longitude, self.nb_elements)
        self.speed = np.resize(self.speed, self.nb_elements)
        self.track = np.resize(self.track, self.nb_elements)
        self.distance = np.resize(self.distance, self.nb_elements)
        self.mode = np.resize(self.mode, self.nb_elements)
        self.status = np.resize(self.status, self.nb_elements)
        self.time_gnss = np.resize(self.time_gnss, self.nb_elements)
        self.satellites_visible = np.resize(self.satellites_visible, self.nb_elements)

    def load_message(self):

        # open gpx file
        gpx_file = open(self.bag_path, 'r')
        gpx = gpxpy.parse(correction_of_malformed_gpx(gpx_file.read()))

        # make the sum of the number of points in each segment
        self.nb_elements = 0
        for track in gpx.tracks:
            for segment in track.segments:
                self.nb_elements += len(segment.points)
        #self.start_date = gpx.tracks[0].segments[0].points[0].time
        self.starting_time = gpx.tracks[0].segments[0].points[0].time
        self.ending_time = gpx.tracks[-1].segments[-1].points[-1].time

        self.resize_data_array()

        # Loop over all points
        self.k = 0
        previous_point = None
        for i, track in enumerate(gpx.tracks):
            for j, segment in enumerate(track.segments):
                for k, point in enumerate(segment.points):
                    self.time[self.k] = (point.time - self.starting_time).total_seconds()
                    self.time_gnss[self.k] = point.time.timestamp()
                    self.latitude[self.k] = point.latitude
                    self.longitude[self.k] = point.longitude
                    self.mode[self.k] = 3
                    self.status[self.k] = 0
                    self.satellites_visible[self.k] = 0

                    if previous_point is None:
                        self.speed[self.k] = 0
                        self.track[self.k] = 0
                        self.distance[self.k] = 0
                    else:
                        # compute speed/track with previous point
                        self.speed[self.k] = point.speed_between(gpx.tracks[i].segments[j].points[k-1])
                        self.track[self.k] = gpx.tracks[i].segments[j].points[k-1].course_between(point)
                        # compute distance from previous point
                        self.distance[self.k] = self.distance[self.k-1] + previous_point.distance_2d(point)
                    self.k += 1
                    previous_point = point

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
        self.nb_elements = self.k


