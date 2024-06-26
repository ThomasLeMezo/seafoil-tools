#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilManoeuvre(SeafoilData):
    def __init__(self, bag_path="", topic_name="", start_date=datetime.datetime(2019, 1, 1)):
        SeafoilData.__init__(self, bag_path, topic_name, start_date)
        self.start_date = start_date
        
        self.heading_max_difference = np.empty([self.nb_elements], dtype='float')
        self.state = np.empty([self.nb_elements], dtype='uint8')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.was_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        
        self.heading_max_difference[self.k] = msg.heading_max_difference
        self.state[self.k] = msg.state
        return

    def resize_data_array(self):
        
        self.heading_max_difference = np.resize(self.heading_max_difference, self.k)
        self.state = np.resize(self.state, self.k)
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
                                heading_max_difference=self.heading_max_difference,
                                state=self.state,)

    def load_message_from_file(self):
        data = np.load(self.topic_name_dir + "/" + self.topic_name_file, allow_pickle=True)
        self.time = data['time']
        self.heading_max_difference = data['heading_max_difference']
        self.state = data['state']
        self.k = len(self.time)
    