#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilWind(SeafoilData):
    def __init__(self, bag_path=None, topic_name=None, start_date=datetime.datetime(2019, 1, 1), data_folder=None):
        SeafoilData.__init__(self, bag_path, topic_name, start_date, data_folder)
        self.start_date = start_date
        
        self.velocity = np.empty([self.nb_elements], dtype='float')
        self.direction = np.empty([self.nb_elements], dtype='uint16')
        self.battery = np.empty([self.nb_elements], dtype='uint8')
        self.temperature = np.empty([self.nb_elements], dtype='uint8')
        self.roll = np.empty([self.nb_elements], dtype='int8')
        self.pitch = np.empty([self.nb_elements], dtype='int8')
        self.heading = np.empty([self.nb_elements], dtype='uint16')
        self.direction_north = np.empty([self.nb_elements], dtype='int16')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.velocity[self.k] =msg.velocity
        self.direction[self.k] =msg.direction
        self.battery[self.k] =msg.battery
        self.temperature[self.k] =msg.temperature
        self.roll[self.k] =msg.roll
        self.pitch[self.k] =msg.pitch
        self.heading[self.k] =msg.heading
        self.direction_north[self.k] =msg.direction_north
        
        return

    def resize_data_array(self):
        self.velocity = np.resize(self.velocity,self.k)
        self.direction = np.resize(self.direction,self.k)
        self.battery = np.resize(self.battery,self.k)
        self.temperature = np.resize(self.temperature,self.k)
        self.roll = np.resize(self.roll,self.k)
        self.pitch = np.resize(self.pitch,self.k)
        self.heading = np.resize(self.heading,self.k)
        self.direction_north = np.resize(self.direction_north,self.k)
        
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
                                velocity=self.velocity,
                                direction=self.direction,
                                battery=self.battery,
                                temperature=self.temperature,
                                roll=self.roll,
                                pitch=self.pitch,
                                heading=self.heading,
                                direction_north=self.direction_north,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.time = data['time']
        self.velocity = data['velocity']
        self.direction = data['direction']
        self.battery = data['battery']
        self.temperature = data['temperature']
        self.roll = data['roll']
        self.pitch = data['pitch']
        self.heading = data['heading']
        self.direction_north = data['direction_north']
    