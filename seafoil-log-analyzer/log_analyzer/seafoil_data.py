#!/bin/python3

import sqlite3
from rosidl_runtime_py.utilities import get_message
from rclpy.serialization import deserialize_message
import rosbag2_py
import numpy as np
import datetime
import os


class SeafoilData(object):
    def __init__(self, bag_path="", topic_name="", offset_date=datetime.datetime(2019, 1, 1)):
        self.bag_path = bag_path
        self.topic_name = topic_name
        self.offset_date = offset_date

        ## Determine sotrage and converter options
        self.serialization_format = 'cdr'
        self.storage_options = rosbag2_py.StorageOptions(uri=self.bag_path)  # , storage_id='sqlite3'
        self.converter_options = rosbag2_py.ConverterOptions(
            input_serialization_format=self.serialization_format,
            output_serialization_format=self.serialization_format)

        ## Count number of messages
        # test if bag_path is not a gpx
        if not bag_path.endswith(".gpx"):
            self.nb_elements = self.count_nb_message()
            self.starting_time = self.get_starting_time()
        else:
            self.nb_elements = 0
            self.starting_time = datetime.datetime(2019, 1, 1, 0, 0)

        self.time = np.empty([self.nb_elements])
        self.k = 0

        self.was_loaded_from_file = False

        ## Topic directory for save
        self.topic_name_dir = self.topic_name
        # split topic name and keep only part before last /

        self.topic_name_dir = self.bag_path+"/data/"
        if len(self.topic_name.split('/')) > 1:
            self.topic_name_dir += self.topic_name.rsplit('/', 1)[0]
        self.topic_name_file = self.topic_name.rsplit('/', 1)[-1] + ".npz"
        self.topic_full_dir = self.topic_name_dir + "/" + self.topic_name_file

    def is_empty(self):
        if (self.k == 0):
            return True
        else:
            return False

    def add_time(self, t):
        self.time[self.k] = t * 1e-9  - self.starting_time.timestamp()
        self.k = self.k + 1

    def count_nb_message(self):
        metadata = rosbag2_py.Info().read_metadata(self.storage_options.uri, self.storage_options.storage_id)
        match = [item for item in metadata.topics_with_message_count if item.topic_metadata.name == self.topic_name]
        if (len(match) > 0):
            return match[0].message_count
        else:
            return 0

    def get_starting_time(self):
        st = rosbag2_py.Info().read_metadata(self.storage_options.uri, self.storage_options.storage_id).starting_time
        # test if st is a datetime

        dt = datetime.datetime.utcfromtimestamp(st.nanoseconds*1e-9)
        return dt

    def process_message(self, msg):
        print("process_message not implemented")

    def resize_data_array(self):
        self.time = np.resize(self.time, self.k)

    def load_message_from_file(self):
        print("load_message_from_file not implemented")

    def save_data(self):
        print("save_data not implemented")

    def load_message(self):
        if self.nb_elements == 0:
            return

        # test if data directory exists (data has been already saved)
        if os.path.exists(self.topic_full_dir):
            print("Load (saved)", self.topic_name)
            self.load_message_from_file()
            self.was_loaded_from_file = True
        else:
            print("Load ", self.topic_name)
            ## Open the file
            reader = rosbag2_py.SequentialReader()
            reader.open(self.storage_options, self.converter_options)

            ## Get a map of all topics
            topic_types = reader.get_all_topics_and_types()
            type_map = {topic_types[i].name: topic_types[i].type for i in range(len(topic_types))}

            ## Filter to topic name
            filter_topic = rosbag2_py.StorageFilter(topics=[self.topic_name])
            reader.set_filter(filter_topic)

            ## Get the messages
            while reader.has_next():
                try:
                    (topic, data, t) = reader.read_next()
                    date_msg = datetime.datetime.fromtimestamp(t / 1e9)

                    try:
                        if (date_msg > self.offset_date):
                            msg_type = get_message(type_map[topic])

                            msg = deserialize_message(data, msg_type)
                            self.process_message(msg)
                            self.add_time(t)

                    except Exception as e:
                        print("Oops!  deserialization error ", e)
                        print(topic, data, t, msg_type)
                        pass
                except Exception as e:
                    print("Oops!  read_next error ", e)
                    pass