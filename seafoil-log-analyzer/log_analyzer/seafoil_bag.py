#!/bin/python3
import os

from PyQt5.QtCore import pyqtSignal, QObject

from .seafoil_data.seafoil_gps_fix import SeafoilGpsFix
from .seafoil_data.seafoil_profile import SeafoilProfile
from .seafoil_data.seafoil_log import SeafoilLog
from .seafoil_data.seafoil_height import SeafoilHeight
from .seafoil_data.seafoil_height_debug import SeafoilHeightDebug
from .seafoil_data.seafoil_raw_data import SeafoilRawData
from .seafoil_data.seafoil_r_p_y import SeafoilRPY
from .seafoil_data.seafoil_debug_fusion import SeafoilDebugFusion
from .seafoil_data.seafoil_distance import SeafoilDistance
from .seafoil_data.seafoil_battery import SeafoilBattery
from .seafoil_data.seafoil_distance_gate import SeafoilDistanceGate
from .seafoil_data.seafoil_manoeuvre import SeafoilManoeuvre
from .seafoil_data.seafoil_wind import SeafoilWind
from .seafoil_data.seafoil_wind_debug import SeafoilWindDebug
from .seafoil_data.seafoil_gpx import SeafoilGpx
from .tools.seafoil_statistics import SeafoilStatistics

# import rosbag2_py

import datetime
import numpy as np

import yaml

class SeafoilBag(QObject):
	signal_load_data = pyqtSignal(int, str)

	def __init__(self, bag_path=None,
				 	   offset_date=datetime.datetime(2019, 1, 1, 0, 0)):
		super().__init__()

		self.gps_fix = None
		self.profile = None
		self.raw_data = None
		self.calibrated_data = None
		self.rpy = None
		self.debug_fusion = None
		self.battery = None
		self.wind = None
		self.wind_debug = None
		self.height = None
		self.height_debug = None
		self.distance = None
		self.manoeuvre = None
		self.distance_gate = None
		self.rosout = None
		self.seafoil_id = None
		self.statistics = None

		if bag_path is None:
			print("No bag path")
			return
		self.is_gpx = False

		if bag_path.endswith('.gpx'):
			self.is_gpx = True
		elif os.path.isdir(bag_path):
			os.system(f"ros2 bag reindex {bag_path} -s 'mcap'")

		self.file_path = bag_path
		self.nb_topics_processed = 0

		if self.is_gpx:
			self.file_name = os.path.basename(bag_path)
			self.nb_topics = 1
		else:
			# name of the last directory
			self.file_name = os.path.basename(os.path.normpath(bag_path))
			self.nb_topics = 15
		self.offset_date = offset_date

		self.data_folder = os.path.dirname(bag_path) + "/data/"
		self.configuration_file_name = self.data_folder + "/configuration.yaml"
		self.configuration = {}

		# Create data folder if it does not exist
		if not os.path.exists(self.data_folder):
			os.makedirs(self.data_folder, exist_ok=True)

	def load_data(self):
		############## Load data ##############
		self.nb_topics_processed = 0

		# Driver
		if self.is_gpx:
			self.gps_fix = SeafoilGpx(self.file_path, self.data_folder)
		else:
			self.gps_fix = SeafoilGpsFix("/driver/fix", self)
		self.profile = SeafoilProfile("/driver/profile", self)
		self.raw_data = SeafoilRawData("/driver/raw_data", self)
		self.calibrated_data = SeafoilRawData("/driver/calibrated_data", self)
		self.rpy = SeafoilRPY("/driver/rpy", self)
		self.rpy.yaw = (self.rpy.yaw + 180) % 360
		self.debug_fusion = SeafoilDebugFusion("/driver/debug_fusion", self)
		self.battery = SeafoilBattery("/driver/battery", self)
		self.wind = SeafoilWind("/driver/wind", self)
		self.wind_debug = SeafoilWindDebug("/driver/wind_debug", self)

		# Observer
		self.height = SeafoilHeight("/observer/height", self)
		self.height_debug = SeafoilHeightDebug("/observer/height_debug", self)
		if self.is_gpx:
			self.distance = self.gps_fix
		else:
			self.distance = SeafoilDistance("/observer/distance", self)
		self.manoeuvre = SeafoilManoeuvre("/observer/manoeuvre", self)
		self.distance_gate = SeafoilDistanceGate("/observer/distance_gate", self)

		# Info
		# self.log = SeafoilLog("/rosout", self)
		self.rosout = SeafoilLog("/rosout", self)

		# Get seafoil name
		self.seafoil_id = ""

		if not self.load_configurations():
			# Save a default configuration file
			self.configuration = {
				"analysis": {
					"wind_heading": 0,
				}
			}
			self.save_configuration()

		# Statistics
		self.statistics = SeafoilStatistics(self)

		print("Data loaded")

	def __del__(self):
		self.save_configuration()

	def save_configuration(self):
		# Create data folder if it does not exist
		if not os.path.exists(self.data_folder):
			os.makedirs(self.data_folder, exist_ok=True)
		with open(self.configuration_file_name, 'w') as file:
			yaml.dump(self.configuration, file)

	def load_configurations(self):
		# Test if file exists
		if os.path.exists(self.configuration_file_name):
			with open(self.configuration_file_name, 'r') as file:
				self.configuration = yaml.load(file, Loader=yaml.FullLoader)

				# Test if key "analysis" exists
				if "analysis" not in self.configuration:
					# Create the key "analysis"
					self.configuration["analysis"] = {"wind_heading": 0}
			return True
		else:
			return False

	def get_statistics(self):
		stat = {"v500": self.statistics.max_v500,
				"v1850": self.statistics.max_v1852,
                "vmax": self.statistics.max_speed,
				"vjibe": None,
				"vhour": None,
                "starting_time": self.gps_fix.starting_time.timestamp(),
				"ending_time": self.gps_fix.ending_time.timestamp(),
                "is_processed": True,}
		print(stat)
		return stat

	def get_starting_time(self):
		return self.gps_fix.starting_time

	def get_ending_time(self):
		return self.gps_fix.ending_time

	def get_starting_time_timestamp(self):
		return self.gps_fix.starting_time.timestamp()

	def get_ending_time_timestamp(self):
		return self.gps_fix.ending_time.timestamp()

	def emit_signal_process_topic(self, topic_name):
		self.nb_topics_processed += 1
		pourcentage = int(100 * self.nb_topics_processed / self.nb_topics)
		self.signal_load_data.emit(pourcentage, "Loading " + topic_name)

	# def get_number_of_topics_in_bag(self):
	# 	# Initialize rosbag2 Reader
	# 	serialization_format = 'cdr'
	# 	storage_options = rosbag2_py.StorageOptions(uri=self.file_path)  # , storage_id='sqlite3'
	# 	converter_options = rosbag2_py.ConverterOptions(
	# 		input_serialization_format=serialization_format,
	# 		output_serialization_format=serialization_format)
	#
	# 	reader = rosbag2_py.SequentialReader()
	# 	reader.open(storage_options, converter_options)
	#
	# 	# Get the list of topics and types in the bag
	# 	topics_info = reader.get_all_topics_and_types()
	#
	# 	# Get the number of unique topics
	# 	number_of_topics = len(topics_info)
	#
	# 	return number_of_topics