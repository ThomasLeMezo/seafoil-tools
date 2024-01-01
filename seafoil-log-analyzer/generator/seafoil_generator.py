#!/bin/python3

from class_generator import generate_interface_bag_file

# generate_interface_bag_file("seafoil_pga460_driver", "Profile")
# generate_interface_bag_file("seafoil_height_filter", "Height")
# generate_interface_bag_file("seafoil_height_filter", "HeightDebug")
# generate_interface_bag_file("gpsd_client", "GpsFix")
generate_interface_bag_file("icm20948_driver", "RawData")
# generate_interface_bag_file("icm20948_driver", "RPY")
#
# generate_interface_bag_file("rcl_interfaces", "Log")

