#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilWindDebug(SeafoilData):
    def __init__(self, bag_path="", topic_name="", start_date=datetime.datetime(2019, 1, 1)):
        SeafoilData.__init__(self, bag_path, topic_name, start_date)
        self.start_date = start_date
        
        self.status = np.empty([self.nb_elements], dtype='uint8')
        self.rate = np.empty([self.nb_elements], dtype='uint8')
        self.sensors = np.empty([self.nb_elements], dtype='uint8')
        self.connected = np.empty([self.nb_elements], dtype='bool')
        self.rssi = np.empty([self.nb_elements], dtype='int16')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.was_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        
        self.status[self.k] = msg.status
        self.rate[self.k] = msg.rate
        self.sensors[self.k] = msg.sensors
        self.connected[self.k] = msg.connected
        self.rssi[self.k] = msg.rssi
        return

    def resize_data_array(self):
        
        self.status = np.resize(self.status, self.k)
        self.rate = np.resize(self.rate, self.k)
        self.sensors = np.resize(self.sensors, self.k)
        self.connected = np.resize(self.connected, self.k)
        self.rssi = np.resize(self.rssi, self.k)
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
                                status=self.status,
                                rate=self.rate,
                                sensors=self.sensors,
                                connected=self.connected,
                                rssi=self.rssi,)

    def load_message_from_file(self):
        data = np.load(self.topic_name_dir + "/" + self.topic_name_file, allow_pickle=True)
        try:
            self.time = data['time']
            self.status = data['status']
            self.rate = data['rate']
            self.sensors = data['sensors']
            self.connected = data['connected']
            self.rssi = data['rssi']
            self.k = len(self.time)
        except Exception as e:
            pass

    