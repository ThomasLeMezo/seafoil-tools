#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilWindDebug(SeafoilData):
    def __init__(self, topic_name=None, seafoil_bag=None):
        SeafoilData.__init__(self, seafoil_bag.file_path, topic_name, seafoil_bag.offset_date, seafoil_bag.data_folder)
        
        self.status = np.empty([self.nb_elements], dtype='uint8')
        self.rate = np.empty([self.nb_elements], dtype='uint8')
        self.sensors = np.empty([self.nb_elements], dtype='uint8')
        self.connected = np.empty([self.nb_elements], dtype='bool')
        self.rssi = np.empty([self.nb_elements], dtype='int16')

        seafoil_bag.emit_signal_process_topic(self.topic_name)
        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.status[self.k] =msg.status
        self.rate[self.k] =msg.rate
        self.sensors[self.k] =msg.sensors
        self.connected[self.k] =msg.connected
        self.rssi[self.k] =msg.rssi
        
        return

    def resize_data_array(self):
        self.status = np.resize(self.status,self.k)
        self.rate = np.resize(self.rate,self.k)
        self.sensors = np.resize(self.sensors,self.k)
        self.connected = np.resize(self.connected,self.k)
        self.rssi = np.resize(self.rssi,self.k)
        
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
                                status=self.status,
                                rate=self.rate,
                                sensors=self.sensors,
                                connected=self.connected,
                                rssi=self.rssi,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.fromtimestamp(data['time'][0])
        self.ending_time = datetime.datetime.fromtimestamp(data['time'][-1])
        self.time = data['time'] - data['time'][0]
        self.status = data['status']
        self.rate = data['rate']
        self.sensors = data['sensors']
        self.connected = data['connected']
        self.rssi = data['rssi']
        
    