#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilProfile(SeafoilData):
    def __init__(self, bag_path="", topic_name="", start_date=datetime.datetime(2019, 1, 1)):
        SeafoilData.__init__(self, bag_path, topic_name, start_date)
        self.start_date = start_date
        
        self.profile = np.empty([self.nb_elements, 128], dtype='ubyte')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0:
            self.save_data()

    def process_message(self, msg):
        self.profile[self.k, :] = np.array(msg.profile)
        return

    def resize_data_array(self):
        
        self.profile = np.resize(self.profile, [self.k, 128])
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
                                profile=self.profile,)

    def load_message_from_file(self):
        data = np.load(self.topic_name_dir + "/" + self.topic_name_file, allow_pickle=True)
        self.time = data['time']
        self.profile = data['profile']
        self.k = len(self.time)
    