#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilHeightDebug(SeafoilData):
    def __init__(self, topic_name=None, seafoil_bag=None):
        SeafoilData.__init__(self, seafoil_bag.file_path, topic_name, seafoil_bag.offset_date, seafoil_bag.data_folder)
        
        self.profile = np.empty([self.nb_elements, 128], dtype='float')
        self.interval_center = np.empty([self.nb_elements], dtype='uint8')
        self.interval_diam = np.empty([self.nb_elements], dtype='uint8')
        self.height_unfiltered = np.empty([self.nb_elements], dtype='float')

        seafoil_bag.emit_signal_process_topic(self.topic_name)
        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.profile[self.k, :] =np.array(msg.profile, dtype='float')
        self.interval_center[self.k] =msg.interval_center
        self.interval_diam[self.k] =msg.interval_diam
        self.height_unfiltered[self.k] =msg.height_unfiltered
        
        return

    def resize_data_array(self):
        self.profile = np.resize(self.profile,[self.k, 128])
        self.interval_center = np.resize(self.interval_center,self.k)
        self.interval_diam = np.resize(self.interval_diam,self.k)
        self.height_unfiltered = np.resize(self.height_unfiltered,self.k)
        
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
                                profile=self.profile,
                                interval_center=self.interval_center,
                                interval_diam=self.interval_diam,
                                height_unfiltered=self.height_unfiltered,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.fromtimestamp(data['time'][0])
        self.ending_time = datetime.datetime.fromtimestamp(data['time'][-1])
        self.time = data['time'] - data['time'][0]
        self.profile = data['profile']
        self.interval_center = data['interval_center']
        self.interval_diam = data['interval_diam']
        self.height_unfiltered = data['height_unfiltered']
        
    