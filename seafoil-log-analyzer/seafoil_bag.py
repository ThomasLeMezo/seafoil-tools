#!/bin/python3

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
		