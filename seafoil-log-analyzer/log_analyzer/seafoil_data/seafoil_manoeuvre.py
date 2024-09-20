#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilManoeuvre(SeafoilData):
    def __init__(self, topic_name=None, seafoil_bag=None):
        SeafoilData.__init__(self, seafoil_bag.file_path, topic_name, seafoil_bag.offset_date, seafoil_bag.data_folder)
        
        self.heading_max_difference = np.empty([self.nb_elements], dtype='float')
        self.state = np.empty([self.nb_elements], dtype='uint8')

        seafoil_bag.emit_signal_process_topic(self.topic_name)
        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.heading_max_difference[self.k] =msg.heading_max_difference
        self.state[self.k] =msg.state
        
        return

    def resize_data_array(self):
        self.heading_max_difference = np.resize(self.heading_max_difference,self.k)
        self.state = np.resize(self.state,self.k)
        
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
                                heading_max_difference=self.heading_max_difference,
                                state=self.state,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.fromtimestamp(data['time'][0])
        self.ending_time = datetime.datetime.fromtimestamp(data['time'][-1])
        self.time = data['time'] - data['time'][0]
        self.heading_max_difference = data['heading_max_difference']
        self.state = data['state']
        
    