#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilDistance(SeafoilData):
    def __init__(self, bag_path=None, topic_name=None, start_date=datetime.datetime(2019, 1, 1), data_folder=None):
        SeafoilData.__init__(self, bag_path, topic_name, start_date, data_folder)
        self.start_date = start_date
        
        self.distance = np.empty([self.nb_elements], dtype='float')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.distance[self.k] =msg.distance
        
        return

    def resize_data_array(self):
        self.distance = np.resize(self.distance,self.k)
        
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
                                distance=self.distance,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.time = data['time']
        self.distance = data['distance']
    