#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from .seafoil_data import SeafoilData

sys.path.append('..')


class SeafoilBattery(SeafoilData):
    def __init__(self, topic_name=None, seafoil_bag=None):
        SeafoilData.__init__(self, seafoil_bag.file_path, topic_name, seafoil_bag.offset_date, seafoil_bag.data_folder)
        
        self.temperature = np.empty([self.nb_elements], dtype='float')
        self.voltage = np.empty([self.nb_elements], dtype='float')
        self.flags = np.empty([self.nb_elements], dtype='uint16')
        self.nominal_available_capacity = np.empty([self.nb_elements], dtype='uint16')
        self.full_available_capacity = np.empty([self.nb_elements], dtype='uint16')
        self.remaining_capacity = np.empty([self.nb_elements], dtype='uint16')
        self.full_charge_capacity = np.empty([self.nb_elements], dtype='uint16')
        self.average_current = np.empty([self.nb_elements], dtype='int16')
        self.standby_current = np.empty([self.nb_elements], dtype='int16')
        self.max_load_current = np.empty([self.nb_elements], dtype='int16')
        self.average_power = np.empty([self.nb_elements], dtype='int16')
        self.state_of_charge = np.empty([self.nb_elements], dtype='uint16')
        self.internal_temperature = np.empty([self.nb_elements], dtype='float')
        self.state_of_health = np.empty([self.nb_elements], dtype='uint16')

        seafoil_bag.emit_signal_process_topic(self.topic_name)
        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.is_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        self.temperature[self.k] =msg.temperature
        self.voltage[self.k] =msg.voltage
        self.flags[self.k] =msg.flags
        self.nominal_available_capacity[self.k] =msg.nominal_available_capacity
        self.full_available_capacity[self.k] =msg.full_available_capacity
        self.remaining_capacity[self.k] =msg.remaining_capacity
        self.full_charge_capacity[self.k] =msg.full_charge_capacity
        self.average_current[self.k] =msg.average_current
        self.standby_current[self.k] =msg.standby_current
        self.max_load_current[self.k] =msg.max_load_current
        self.average_power[self.k] =msg.average_power
        self.state_of_charge[self.k] =msg.state_of_charge
        self.internal_temperature[self.k] =msg.internal_temperature
        self.state_of_health[self.k] =msg.state_of_health
        
        return

    def resize_data_array(self):
        self.temperature = np.resize(self.temperature,self.k)
        self.voltage = np.resize(self.voltage,self.k)
        self.flags = np.resize(self.flags,self.k)
        self.nominal_available_capacity = np.resize(self.nominal_available_capacity,self.k)
        self.full_available_capacity = np.resize(self.full_available_capacity,self.k)
        self.remaining_capacity = np.resize(self.remaining_capacity,self.k)
        self.full_charge_capacity = np.resize(self.full_charge_capacity,self.k)
        self.average_current = np.resize(self.average_current,self.k)
        self.standby_current = np.resize(self.standby_current,self.k)
        self.max_load_current = np.resize(self.max_load_current,self.k)
        self.average_power = np.resize(self.average_power,self.k)
        self.state_of_charge = np.resize(self.state_of_charge,self.k)
        self.internal_temperature = np.resize(self.internal_temperature,self.k)
        self.state_of_health = np.resize(self.state_of_health,self.k)
        
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
                                temperature=self.temperature,
                                voltage=self.voltage,
                                flags=self.flags,
                                nominal_available_capacity=self.nominal_available_capacity,
                                full_available_capacity=self.full_available_capacity,
                                remaining_capacity=self.remaining_capacity,
                                full_charge_capacity=self.full_charge_capacity,
                                average_current=self.average_current,
                                standby_current=self.standby_current,
                                max_load_current=self.max_load_current,
                                average_power=self.average_power,
                                state_of_charge=self.state_of_charge,
                                internal_temperature=self.internal_temperature,
                                state_of_health=self.state_of_health,)

    def load_message_from_file(self):
        data = np.load(self.topic_full_dir, allow_pickle=True)
        self.starting_time = datetime.datetime.fromtimestamp(data['time'][0])
        self.ending_time = datetime.datetime.fromtimestamp(data['time'][-1])
        self.time = data['time'] - data['time'][0]
        self.temperature = data['temperature']
        self.voltage = data['voltage']
        self.flags = data['flags']
        self.nominal_available_capacity = data['nominal_available_capacity']
        self.full_available_capacity = data['full_available_capacity']
        self.remaining_capacity = data['remaining_capacity']
        self.full_charge_capacity = data['full_charge_capacity']
        self.average_current = data['average_current']
        self.standby_current = data['standby_current']
        self.max_load_current = data['max_load_current']
        self.average_power = data['average_power']
        self.state_of_charge = data['state_of_charge']
        self.internal_temperature = data['internal_temperature']
        self.state_of_health = data['state_of_health']
        
    