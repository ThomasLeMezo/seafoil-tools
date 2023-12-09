#!/bin/python3

from class_generator import generate_interface_bag_file

# generate_interface_bag_file("seafoil_pga460_driver", "Profile")
generate_interface_bag_file("gpsd_client", "GpsFix")

generate_interface_bag_file("rcl_interfaces", "Log")

