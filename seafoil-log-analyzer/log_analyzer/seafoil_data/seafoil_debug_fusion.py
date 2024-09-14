#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilDebugFusion(SeafoilData):
    def __init__(self, bag_path=None, topic_name=None, start_date=datetime.datetime(2019, 1, 1), data_folder=None):
        SeafoilData.__init__(self, bag_path, topic_name, start_date, data_folder)
        self.start_date = start_date
        
        self.acceleration_error = np.empty([self.nb_elements], dtype='float')
        self.accelerometer_ignored = np.empty([self.nb_elements], dtype='bool')
        self.acceleration_recovery_trigger = np.empty([self.nb_elements], dtype='float')
        self.magnetic_error = np.empty([self.nb_elements], dtype='float')
        self.magnetometer_ignored = np.empty([self.nb_elements], dtype='bool')
        self.magnetic_recovery_trigger = np.empty([self.nb_elements], dtype='float')
        self.initialising = np.empty([self.nb_elements], dtype='bool')
        self.angular_rate_recovery = np.empty([self.nb_elements], dtype='bool')
        self.acceleration_recovery = np.empty([self.nb_elements], dtype='bool')
        self.magnetic_recovery = np.empty([self.nb_elements], dtype='bool')
        self.magnetometer_limit_reached = np.empty([self.nb_elements], dtype='bool')
        self.magnetometer_data_skipped = np.empty([self.nb_elements], dtype='bool')
        self.magnetometer_data_is_ready = np.empty([self.nb_elements], dtype='bool')

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.acceleration_error[self.k] =msg.acceleration_error
        self.accelerometer_ignored[self.k] =msg.accelerometer_ignored
        self.acceleration_recovery_trigger[self.k] =msg.acceleration_recovery_trigger
        self.magnetic_error[self.k] =msg.magnetic_error
        self.magnetometer_ignored[self.k] =msg.magnetometer_ignored
        self.magnetic_recovery_trigger[self.k] =msg.magnetic_recovery_trigger
        self.initialising[self.k] =msg.initialising
        self.angular_rate_recovery[self.k] =msg.angular_rate_recovery
        self.acceleration_recovery[self.k] =msg.acceleration_recovery
        self.magnetic_recovery[self.k] =msg.magnetic_recovery
        self.magnetometer_limit_reached[self.k] =msg.magnetometer_limit_reached
        self.magnetometer_data_skipped[self.k] =msg.magnetometer_data_skipped
        self.magnetometer_data_is_ready[self.k] =msg.magnetometer_data_is_ready
        
        return

    def resize_data_array(self):
        self.acceleration_error = np.resize(self.acceleration_error,self.k)
        self.accelerometer_ignored = np.resize(self.accelerometer_ignored,self.k)
        self.acceleration_recovery_trigger = np.resize(self.acceleration_recovery_trigger,self.k)
        self.magnetic_error = np.resize(self.magnetic_error,self.k)
        self.magnetometer_ignored = np.resize(self.magnetometer_ignored,self.k)
        self.magnetic_recovery_trigger = np.resize(self.magnetic_recovery_trigger,self.k)
        self.initialising = np.resize(self.initialising,self.k)
        self.angular_rate_recovery = np.resize(self.angular_rate_recovery,self.k)
        self.acceleration_recovery = np.resize(self.acceleration_recovery,self.k)
        self.magnetic_recovery = np.resize(self.magnetic_recovery,self.k)
        self.magnetometer_limit_reached = np.resize(self.magnetometer_limit_reached,self.k)
        self.magnetometer_data_skipped = np.resize(self.magnetometer_data_skipped,self.k)
        self.magnetometer_data_is_ready = np.resize(self.magnetometer_data_is_ready,self.k)
        
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
                                acceleration_error=self.acceleration_error,
                                accelerometer_ignored=self.accelerometer_ignored,
                                acceleration_recovery_trigger=self.acceleration_recovery_trigger,
                                magnetic_error=self.magnetic_error,
                                magnetometer_ignored=self.magnetometer_ignored,
                                magnetic_recovery_trigger=self.magnetic_recovery_trigger,
                                initialising=self.initialising,
                                angular_rate_recovery=self.angular_rate_recovery,
                                acceleration_recovery=self.acceleration_recovery,
                                magnetic_recovery=self.magnetic_recovery,
                                magnetometer_limit_reached=self.magnetometer_limit_reached,
                                magnetometer_data_skipped=self.magnetometer_data_skipped,
                                magnetometer_data_is_ready=self.magnetometer_data_is_ready,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.time = data['time']
        self.acceleration_error = data['acceleration_error']
        self.accelerometer_ignored = data['accelerometer_ignored']
        self.acceleration_recovery_trigger = data['acceleration_recovery_trigger']
        self.magnetic_error = data['magnetic_error']
        self.magnetometer_ignored = data['magnetometer_ignored']
        self.magnetic_recovery_trigger = data['magnetic_recovery_trigger']
        self.initialising = data['initialising']
        self.angular_rate_recovery = data['angular_rate_recovery']
        self.acceleration_recovery = data['acceleration_recovery']
        self.magnetic_recovery = data['magnetic_recovery']
        self.magnetometer_limit_reached = data['magnetometer_limit_reached']
        self.magnetometer_data_skipped = data['magnetometer_data_skipped']
        self.magnetometer_data_is_ready = data['magnetometer_data_is_ready']
    