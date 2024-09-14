#!/bin/python3
import os

from msg.seafoil_gps_fix import SeafoilGpsFix
from msg.seafoil_profile import SeafoilProfile
from msg.seafoil_log import SeafoilLog
from msg.seafoil_height import SeafoilHeight
from msg.seafoil_height_debug import SeafoilHeightDebug
from msg.seafoil_raw_data import SeafoilRawData
from msg.seafoil_r_p_y import SeafoilRPY
from msg.seafoil_debug_fusion import SeafoilDebugFusion
from msg.seafoil_distance import SeafoilDistance
from msg.seafoil_battery import SeafoilBattery
from msg.seafoil_distance_gate import SeafoilDistanceGate
from msg.seafoil_manoeuvre import SeafoilManoeuvre
from msg.seafoil_wind import SeafoilWind
from msg.seafoil_wind_debug import SeafoilWindDebug
from gpx.seafoil_gpx import SeafoilGpx

import datetime
import numpy as np

import yaml

class SeafoilBag():
	def __init__(self, bag_path="", offset_date=datetime.datetime(2019, 1, 1, 0, 0), is_gpx=False):

		self.file_name = bag_path
		self.offset_date = offset_date

		# Driver
		if is_gpx:
			self.gps_fix = SeafoilGpx(bag_path)
		else:
			self.gps_fix = SeafoilGpsFix(bag_path, "/driver/fix", offset_date)
		self.profile = SeafoilProfile(bag_path, "/driver/profile", offset_date)
		self.raw_data = SeafoilRawData(bag_path, "/driver/raw_data", offset_date)
		self.calibrated_data = SeafoilRawData(bag_path, "/driver/calibrated_data", offset_date)
		self.rpy = SeafoilRPY(bag_path, "/driver/rpy", offset_date)
		self.rpy.yaw = (self.rpy.yaw + 180) % 360
		self.debug_fusion = SeafoilDebugFusion(bag_path, "/driver/debug_fusion", offset_date)
		self.battery = SeafoilBattery(bag_path, "/driver/battery", offset_date)
		self.wind = SeafoilWind(bag_path, "/driver/wind", offset_date)
		self.wind_debug = SeafoilWindDebug(bag_path, "/driver/wind_debug", offset_date)

		# Observer
		self.height = SeafoilHeight(bag_path, "/observer/height", offset_date)
		self.height_debug = SeafoilHeightDebug(bag_path, "/observer/height_debug", offset_date)
		if is_gpx:
			self.distance = self.gps_fix
		else:
			self.distance = SeafoilDistance(bag_path, "/observer/distance", offset_date)
		self.manoeuvre = SeafoilManoeuvre(bag_path, "/observer/manoeuvre", offset_date)
		self.distance_gate = SeafoilDistanceGate(bag_path, "/observer/distance_gate", offset_date)

		# Info
		# self.log = SeafoilLog(bag_path, "/rosout", offset_date)
		self.rosout = SeafoilLog(bag_path, "/rosout", offset_date)

		# Get seafoil name
		self.seafoil_id = ""
		# idx = np.where(self.log_parameter.param_name == "/hostname")
		# if len(idx) > 0:
		# 	if len(self.log_parameter.value[idx[0]]) > 0:
		# 		self.seafoil_id = str(self.log_parameter.value[idx[0]][0].string_value)
		print("Seafoil id: " + self.seafoil_id)

		self.configuration_file_name = os.path.dirname(bag_path) + "/configuration.yaml"
		self.configuration = {}

		if not self.load_configurations():
			# Save a default configuration file
			self.configuration = {
				"analysis": {
					"wind_heading": 0,
				}
			}
			self.save_configuration()

	def __del__(self):
		print("SeafoilBag deleted")
		self.save_configuration()

	def save_configuration(self):
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

		