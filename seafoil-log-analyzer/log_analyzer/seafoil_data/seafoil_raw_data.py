#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilRawData(SeafoilData):
    def __init__(self, topic_name=None, seafoil_bag=None):
        SeafoilData.__init__(self, seafoil_bag.file_path, topic_name, seafoil_bag.offset_date, seafoil_bag.data_folder)
        
        self.accel_x = np.empty([self.nb_elements], dtype='float')
        self.accel_y = np.empty([self.nb_elements], dtype='float')
        self.accel_z = np.empty([self.nb_elements], dtype='float')
        self.gyro_x = np.empty([self.nb_elements], dtype='float')
        self.gyro_y = np.empty([self.nb_elements], dtype='float')
        self.gyro_z = np.empty([self.nb_elements], dtype='float')
        self.mag_x = np.empty([self.nb_elements], dtype='float')
        self.mag_y = np.empty([self.nb_elements], dtype='float')
        self.mag_z = np.empty([self.nb_elements], dtype='float')
        self.temp = np.empty([self.nb_elements], dtype='float')

        seafoil_bag.emit_signal_process_topic(self.topic_name)
        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.accel_x[self.k] =msg.accel.x
        self.accel_y[self.k] =msg.accel.y
        self.accel_z[self.k] =msg.accel.z
        self.gyro_x[self.k] =msg.gyro.x
        self.gyro_y[self.k] =msg.gyro.y
        self.gyro_z[self.k] =msg.gyro.z
        self.mag_x[self.k] =msg.mag.x
        self.mag_y[self.k] =msg.mag.y
        self.mag_z[self.k] =msg.mag.z
        self.temp[self.k] =msg.temp
        
        return

    def resize_data_array(self):
        self.accel_x = np.resize(self.accel_x,self.k)
        self.accel_y = np.resize(self.accel_y,self.k)
        self.accel_z = np.resize(self.accel_z,self.k)
        self.gyro_x = np.resize(self.gyro_x,self.k)
        self.gyro_y = np.resize(self.gyro_y,self.k)
        self.gyro_z = np.resize(self.gyro_z,self.k)
        self.mag_x = np.resize(self.mag_x,self.k)
        self.mag_y = np.resize(self.mag_y,self.k)
        self.mag_z = np.resize(self.mag_z,self.k)
        self.temp = np.resize(self.temp,self.k)
        
        return
        
    def save_data(self):
        import os
        # Test if save directory exists
        if not os.path.exists(self.topic_name_dir) and self.k > 0:
            os.makedirs(self.topic_name_dir)
            # Save data (compressed)
        if not os.path.exists(self.topic_full_dir):
            np.savez_compressed(self.topic_full_dir,
                                time=self.time + self.starting_time.timestamp(),
                                accel_x=self.accel_x,
                                accel_y=self.accel_y,
                                accel_z=self.accel_z,
                                gyro_x=self.gyro_x,
                                gyro_y=self.gyro_y,
                                gyro_z=self.gyro_z,
                                mag_x=self.mag_x,
                                mag_y=self.mag_y,
                                mag_z=self.mag_z,
                                temp=self.temp,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.fromtimestamp(data['time'][0])
        self.ending_time = datetime.datetime.fromtimestamp(data['time'][-1])
        self.time = data['time'] - data['time'][0]
        self.accel_x = data['accel_x']
        self.accel_y = data['accel_y']
        self.accel_z = data['accel_z']
        self.gyro_x = data['gyro_x']
        self.gyro_y = data['gyro_y']
        self.gyro_z = data['gyro_z']
        self.mag_x = data['mag_x']
        self.mag_y = data['mag_y']
        self.mag_z = data['mag_z']
        self.temp = data['temp']
        
    