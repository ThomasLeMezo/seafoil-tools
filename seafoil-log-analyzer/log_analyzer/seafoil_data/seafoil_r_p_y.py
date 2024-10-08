#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilRPY(SeafoilData):
    def __init__(self, topic_name=None, seafoil_bag=None):
        SeafoilData.__init__(self, seafoil_bag.file_path, topic_name, seafoil_bag.offset_date, seafoil_bag.data_folder)
        
        self.roll = np.empty([self.nb_elements], dtype='float')
        self.pitch = np.empty([self.nb_elements], dtype='float')
        self.yaw = np.empty([self.nb_elements], dtype='float')
        self.acceleration_x = np.empty([self.nb_elements], dtype='float')
        self.acceleration_y = np.empty([self.nb_elements], dtype='float')
        self.acceleration_z = np.empty([self.nb_elements], dtype='float')

        seafoil_bag.emit_signal_process_topic(self.topic_name)
        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.roll[self.k] =msg.roll
        self.pitch[self.k] =msg.pitch
        self.yaw[self.k] =msg.yaw
        self.acceleration_x[self.k] =msg.acceleration.x
        self.acceleration_y[self.k] =msg.acceleration.y
        self.acceleration_z[self.k] =msg.acceleration.z
        
        return

    def resize_data_array(self):
        self.roll = np.resize(self.roll,self.k)
        self.pitch = np.resize(self.pitch,self.k)
        self.yaw = np.resize(self.yaw,self.k)
        self.acceleration_x = np.resize(self.acceleration_x,self.k)
        self.acceleration_y = np.resize(self.acceleration_y,self.k)
        self.acceleration_z = np.resize(self.acceleration_z,self.k)
        
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
                                roll=self.roll,
                                pitch=self.pitch,
                                yaw=self.yaw,
                                acceleration_x=self.acceleration_x,
                                acceleration_y=self.acceleration_y,
                                acceleration_z=self.acceleration_z,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.fromtimestamp(data['time'][0])
        self.ending_time = datetime.datetime.fromtimestamp(data['time'][-1])
        self.time = data['time'] - data['time'][0]
        self.roll = data['roll']
        self.pitch = data['pitch']
        self.yaw = data['yaw']
        self.acceleration_x = data['acceleration_x']
        self.acceleration_y = data['acceleration_y']
        self.acceleration_z = data['acceleration_z']
        
    