#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilGpsFix(SeafoilData):
    def __init__(self, bag_path=None, topic_name=None, start_date=datetime.datetime(2019, 1, 1), data_folder=None):
        SeafoilData.__init__(self, bag_path, topic_name, start_date, data_folder)
        self.start_date = start_date
        
        self.mode = np.empty([self.nb_elements], dtype='int16')
        self.status = np.empty([self.nb_elements], dtype='int16')
        self.latitude = np.empty([self.nb_elements], dtype='double')
        self.longitude = np.empty([self.nb_elements], dtype='double')
        self.altitude = np.empty([self.nb_elements], dtype='double')
        self.track = np.empty([self.nb_elements], dtype='double')
        self.speed = np.empty([self.nb_elements], dtype='double')
        self.time_gnss = np.empty([self.nb_elements], dtype='double')
        self.gdop = np.empty([self.nb_elements], dtype='double')
        self.pdop = np.empty([self.nb_elements], dtype='double')
        self.hdop = np.empty([self.nb_elements], dtype='double')
        self.vdop = np.empty([self.nb_elements], dtype='double')
        self.tdop = np.empty([self.nb_elements], dtype='double')
        self.err = np.empty([self.nb_elements], dtype='double')
        self.err_horz = np.empty([self.nb_elements], dtype='double')
        self.err_vert = np.empty([self.nb_elements], dtype='double')
        self.err_track = np.empty([self.nb_elements], dtype='double')
        self.err_speed = np.empty([self.nb_elements], dtype='double')
        self.err_time = np.empty([self.nb_elements], dtype='double')
        self.satellites_visible = np.empty([self.nb_elements], dtype='int32')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.mode[self.k] =msg.mode
        self.status[self.k] =msg.status
        self.latitude[self.k] =msg.latitude
        self.longitude[self.k] =msg.longitude
        self.altitude[self.k] =msg.altitude
        self.track[self.k] =msg.track
        self.speed[self.k] =msg.speed
        self.time_gnss[self.k] =msg.time
        self.gdop[self.k] =msg.gdop
        self.pdop[self.k] =msg.pdop
        self.hdop[self.k] =msg.hdop
        self.vdop[self.k] =msg.vdop
        self.tdop[self.k] =msg.tdop
        self.err[self.k] =msg.err
        self.err_horz[self.k] =msg.err_horz
        self.err_vert[self.k] =msg.err_vert
        self.err_track[self.k] =msg.err_track
        self.err_speed[self.k] =msg.err_speed
        self.err_time[self.k] =msg.err_time
        self.satellites_visible[self.k] =msg.satellites_visible
        
        return

    def resize_data_array(self):
        self.mode = np.resize(self.mode,self.k)
        self.status = np.resize(self.status,self.k)
        self.latitude = np.resize(self.latitude,self.k)
        self.longitude = np.resize(self.longitude,self.k)
        self.altitude = np.resize(self.altitude,self.k)
        self.track = np.resize(self.track,self.k)
        self.speed = np.resize(self.speed,self.k)
        self.time_gnss = np.resize(self.time_gnss,self.k)
        self.gdop = np.resize(self.gdop,self.k)
        self.pdop = np.resize(self.pdop,self.k)
        self.hdop = np.resize(self.hdop,self.k)
        self.vdop = np.resize(self.vdop,self.k)
        self.tdop = np.resize(self.tdop,self.k)
        self.err = np.resize(self.err,self.k)
        self.err_horz = np.resize(self.err_horz,self.k)
        self.err_vert = np.resize(self.err_vert,self.k)
        self.err_track = np.resize(self.err_track,self.k)
        self.err_speed = np.resize(self.err_speed,self.k)
        self.err_time = np.resize(self.err_time,self.k)
        self.satellites_visible = np.resize(self.satellites_visible,self.k)
        
        return
        
    def save_data(self):
        import os
        # Test if save directory exists
        if not os.path.exists(self.topic_name_dir) and self.k > 0:
            os.makedirs(self.topic_name_dir)
            # Save data (compressed)
        if not os.path.exists(self.topic_full_dir):
            np.savez_compressed(self.topic_full_dir,
                                time=self.time,
                                mode=self.mode,
                                status=self.status,
                                latitude=self.latitude,
                                longitude=self.longitude,
                                altitude=self.altitude,
                                track=self.track,
                                speed=self.speed,
                                time_gnss=self.time_gnss,
                                gdop=self.gdop,
                                pdop=self.pdop,
                                hdop=self.hdop,
                                vdop=self.vdop,
                                tdop=self.tdop,
                                err=self.err,
                                err_horz=self.err_horz,
                                err_vert=self.err_vert,
                                err_track=self.err_track,
                                err_speed=self.err_speed,
                                err_time=self.err_time,
                                satellites_visible=self.satellites_visible,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.time = data['time']
        self.mode = data['mode']
        self.status = data['status']
        self.latitude = data['latitude']
        self.longitude = data['longitude']
        self.altitude = data['altitude']
        self.track = data['track']
        self.speed = data['speed']
        self.time_gnss = data['time_gnss']
        self.gdop = data['gdop']
        self.pdop = data['pdop']
        self.hdop = data['hdop']
        self.vdop = data['vdop']
        self.tdop = data['tdop']
        self.err = data['err']
        self.err_horz = data['err_horz']
        self.err_vert = data['err_vert']
        self.err_track = data['err_track']
        self.err_speed = data['err_speed']
        self.err_time = data['err_time']
        self.satellites_visible = data['satellites_visible']
    