#!/bin/python3

from msg.seafoil_gps_fix import SeafoilGpsFix
from msg.seafoil_profile import SeafoilProfile
from msg.seafoil_log import SeafoilLog
from msg.seafoil_height import SeafoilHeight
from msg.seafoil_height_debug import SeafoilHeightDebug
from msg.seafoil_raw_data import SeafoilRawData
from msg.seafoil_r_p_y import SeafoilRPY
from msg.seafoil_debug_fusion import SeafoilDebugFusion

import datetime
import numpy as np

class SeafoilBag():
	def __init__(self, bag_path="", offset_date=datetime.datetime(2019, 1, 1, 0, 0)):
		self.file_name = bag_path
		self.offset_date = offset_date

		# Driver
		self.gps_fix = SeafoilGpsFix(bag_path, "/driver/fix", offset_date)
		self.profile = SeafoilProfile(bag_path, "/driver/profile", offset_date)
		self.raw_data = SeafoilRawData(bag_path, "/driver/raw_data", offset_date)
		self.calibrated_data = SeafoilRawData(bag_path, "/driver/calibrated_data", offset_date)
		self.rpy = SeafoilRPY(bag_path, "/driver/rpy", offset_date)
		self.debug_fusion = SeafoilDebugFusion(bag_path, "/driver/debug_fusion", offset_date)

		# Observer
		self.height = SeafoilHeight(bag_path, "/observer/height", offset_date)
		self.height_debug = SeafoilHeightDebug(bag_path, "/observer/height_debug", offset_date)

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
		