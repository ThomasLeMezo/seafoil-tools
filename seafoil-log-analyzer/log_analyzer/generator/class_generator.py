#!/bin/python3

import sys
import re
from rosidl_runtime_py import utilities
from jinja2 import Template


def generate_interface_bag_file(package_name="", msg_name=""):
    template_msg = """#!/bin/python3
# This file was generated automatically, do not edit
import sys
import numpy as np
import datetime
from seafoil_data import SeafoilData

sys.path.append('..')


class Seafoil{{ class_name }}(SeafoilData):
    def __init__(self, bag_path="", topic_name="", start_date=datetime.datetime(2019, 1, 1)):
        SeafoilData.__init__(self, bag_path, topic_name, start_date)
        self.start_date = start_date
        {% for variable in table %}
        self.{{ variable }} = np.empty([self.nb_elements], dtype='{{ table[variable][1] }}'){% endfor %}

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.was_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        {% for variable in table %}
        self.{{ variable }}[self.k] = msg.{{ table[variable][2] }}{% endfor %}
        return

    def resize_data_array(self):
        {% for variable in table %}
        self.{{ variable }} = np.resize(self.{{ variable }}, self.k){% endfor %}
        return
        
    def save_data(self):
        import os
        # Test if save directory exists
        if not os.path.exists(self.topic_name_dir) and self.k > 0:
            os.makedirs(self.topic_name_dir)
            # Save data (compressed)
        if not os.path.exists(self.topic_full_dir):
            np.savez_compressed(self.topic_full_dir,
                                time=self.time,{% for variable in table %}
                                {{ variable }}=self.{{ variable }},{% endfor %})

    def load_message_from_file(self):
        data = np.load(self.topic_name_dir + "/" + self.topic_name_file, allow_pickle=True)
        self.time = data['time']{% for variable in table %}
        self.{{ variable }} = data['{{ variable }}']{% endfor %}
        self.k = len(self.time)
    """

    interface = utilities.get_interface(package_name + "/msg/" + msg_name)

    interface_name = interface.mro()[0].__name__
    interface_name_lower = re.sub(r'(?<!^)(?=[A-Z])', '_', interface_name).lower()

    fields = interface.get_fields_and_field_types()

    if "header" in fields.keys():
        del fields["header"]

    if "linear" in fields.keys():
        del fields["linear"]
    if "angular" in fields.keys():
        del fields["angular"]

    # Rewrite fileds to take into acount tab and boolean
    new_fields = {}

    for item in fields:
        if fields[item] == "boolean":
            new_fields[item] = [item, "bool", item]
        elif \
                fields[item] == "rcl_interfaces/ParameterValue" or fields[item] == "string" or fields[
                    item] == "sequence<uint8>" or fields[item] == "builtin_interfaces/Time":
            new_fields[item] = [item, "object", item]
        elif "[" in fields[item]:
            split_result = re.split(r'[\[\]]', fields[item])
            variable_type = split_result[0]
            variable_nb = int(split_result[1])
            if variable_nb < 10:
                for i in range(variable_nb):
                    new_fields[item + str(i)] = [item + "[" + str(i) + "]", variable_type, item + "[" + str(i) + "]"]
            else:
                if variable_type == "uint8":
                    new_fields[item] = [item, "ubyte", item]
                else:
                    new_fields[item] = [item, "object", item]
        elif fields[item] == "geometry_msgs/Vector3":
            new_fields[item + "_x"] = [item + "_x", "float", item + ".x"]
            new_fields[item + "_y"] = [item + "_x", "float", item + ".y"]
            new_fields[item + "_z"] = [item + "_x", "float", item + ".z"]
        else:
            new_fields[item] = [item, fields[item], item]
    print(new_fields)

    if "time" in new_fields.keys():  # Special case for time
        data = new_fields["time"]
        del new_fields["time"]
        new_fields["time_gnss"] = [data[0], data[1], "time"]
    if "file" in new_fields.keys():  # Special case for file
        data = new_fields["file"]
        del new_fields["file"]
        new_fields["file_name"] = [data[0], data[1], "file"]

    tm = Template(template_msg)
    msg = tm.render(class_name=interface_name, table=new_fields)

    file_name = "../msg/seafoil_" + interface_name_lower + ".py"

    file_object = open(file_name, "w+")
    file_object.write(msg)
    # print("Generate " + file_name)

    print("from .msg.seafoil_" + interface_name_lower + " import " + "Seafoil" + interface_name)


if __name__ == '__main__':
    generate_interface_bag_file(sys.argv[1], sys.argv[2])
