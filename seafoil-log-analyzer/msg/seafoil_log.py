#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilLog(SeafoilData):
    def __init__(self, bag_path="", topic_name="", start_date=datetime.datetime(2019, 1, 1)):
        SeafoilData.__init__(self, bag_path, topic_name, start_date)
        self.start_date = start_date
        
        self.stamp = np.empty([self.nb_elements], dtype='object')
        self.level = np.empty([self.nb_elements], dtype='uint8')
        self.name = np.empty([self.nb_elements], dtype='object')
        self.msg = np.empty([self.nb_elements], dtype='object')
        self.function = np.empty([self.nb_elements], dtype='object')
        self.line = np.empty([self.nb_elements], dtype='uint32')
        self.file_name = np.empty([self.nb_elements], dtype='object')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k>0 and not self.was_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        
        self.stamp[self.k] = msg.stamp
        self.level[self.k] = msg.level
        self.name[self.k] = msg.name
        self.msg[self.k] = msg.msg
        self.function[self.k] = msg.function
        self.line[self.k] = msg.line
        self.file_name[self.k] = msg.file
        return

    def resize_data_array(self):
        
        self.stamp = np.resize(self.stamp, self.k)
        self.level = np.resize(self.level, self.k)
        self.name = np.resize(self.name, self.k)
        self.msg = np.resize(self.msg, self.k)
        self.function = np.resize(self.function, self.k)
        self.line = np.resize(self.line, self.k)
        self.file_name = np.resize(self.file_name, self.k)
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
                                stamp=self.stamp,
                                level=self.level,
                                name=self.name,
                                msg=self.msg,
                                function=self.function,
                                line=self.line,
                                file_name=self.file_name,)

    def load_message_from_file(self):
        data = np.load(self.topic_name_dir + "/" + self.topic_name_file, allow_pickle=True)
        self.time = data['time']
        self.stamp = data['stamp']
        self.level = data['level']
        self.name = data['name']
        self.msg = data['msg']
        self.function = data['function']
        self.line = data['line']
        self.file_name = data['file_name']
        self.k = len(self.time)
    