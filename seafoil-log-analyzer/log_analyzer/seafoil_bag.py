#!/bin/python3
import os

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

import datetime
import numpy as np

import yaml

class SeafoilBag():
	def __init__(self, bag_path=None, offset_date=datetime.datetime(2019, 1, 1, 0, 0)):
		if bag_path is None:
			return
		self.is_gpx = False

		if bag_path.endswith('.gpx'):
			self.is_gpx = True
		elif os.path.isdir(bag_path):
			os.system(f"ros2 bag reindex {bag_path} -s 'mcap'")

		self.file_path = bag_path
		if self.is_gpx:
			self.file_name = os.path.basename(bag_path)
		else:
			# name of the last directory
			self.file_name = os.path.basename(os.path.normpath(bag_path))
		self.offset_date = offset_date

		self.data_folder = os.path.dirname(bag_path) + "/data/"
		self.configuration_file_name = self.data_folder + "/configuration.yaml"
		self.configuration = {}

		# Create data folder if it does not exist
		if not os.path.exists(self.data_folder):
			os.makedirs(self.data_folder, exist_ok=True)

		# Driver
		if self.is_gpx:
			self.gps_fix = SeafoilGpx(bag_path, self.data_folder)
		else:
			self.gps_fix = SeafoilGpsFix(bag_path, "/driver/fix", offset_date, self.data_folder)
		self.profile = SeafoilProfile(bag_path, "/driver/profile", offset_date, self.data_folder)
		self.raw_data = SeafoilRawData(bag_path, "/driver/raw_data", offset_date, self.data_folder)
		self.calibrated_data = SeafoilRawData(bag_path, "/driver/calibrated_data", offset_date, self.data_folder)
		self.rpy = SeafoilRPY(bag_path, "/driver/rpy", offset_date, self.data_folder)
		self.rpy.yaw = (self.rpy.yaw + 180) % 360
		self.debug_fusion = SeafoilDebugFusion(bag_path, "/driver/debug_fusion", offset_date, self.data_folder)
		self.battery = SeafoilBattery(bag_path, "/driver/battery", offset_date, self.data_folder)
		self.wind = SeafoilWind(bag_path, "/driver/wind", offset_date, self.data_folder)
		self.wind_debug = SeafoilWindDebug(bag_path, "/driver/wind_debug", offset_date, self.data_folder)

		# Observer
		self.height = SeafoilHeight(bag_path, "/observer/height", offset_date, self.data_folder)
		self.height_debug = SeafoilHeightDebug(bag_path, "/observer/height_debug", offset_date, self.data_folder)
		if self.is_gpx:
			self.distance = self.gps_fix
		else:
			self.distance = SeafoilDistance(bag_path, "/observer/distance", offset_date, self.data_folder)
		self.manoeuvre = SeafoilManoeuvre(bag_path, "/observer/manoeuvre", offset_date, self.data_folder)
		self.distance_gate = SeafoilDistanceGate(bag_path, "/observer/distance_gate", offset_date, self.data_folder)

		# Info
		# self.log = SeafoilLog(bag_path, "/rosout", offset_date, self.data_folder)
		self.rosout = SeafoilLog(bag_path, "/rosout", offset_date, self.data_folder)

		# Get seafoil name
		self.seafoil_id = ""
		# idx = np.where(self.log_parameter.param_name == "/hostname")
		# if len(idx) > 0:
		# 	if len(self.log_parameter.value[idx[0]]) > 0:
		# 		self.seafoil_id = str(self.log_parameter.value[idx[0]][0].string_value)
		# print("Seafoil id: " + self.seafoil_id)

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