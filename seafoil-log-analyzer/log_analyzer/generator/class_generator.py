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
from .seafoil_data import SeafoilData

sys.path.append('..')


class Seafoil{{ class_name }}(SeafoilData):
    def __init__(self, bag_path="", topic_name="", start_date=datetime.datetime(2019, 1, 1)):
        SeafoilData.__init__(self, bag_path, topic_name, start_date)
        self.start_date = start_date
        {% for variable in table %}
        self.{{ variable["python_name"] }} = np.empty([self.nb_elements{%if variable["is_tab"] == True%}, {{variable["tab_count"]}}{%endif%}], dtype='{{ variable["type"] }}'){% endfor %}

        self.load_message()
        self.resize_data_array()
        super().resize_data_array()
        if self.k > 0 and not self.was_loaded_from_file:
            self.save_data()

    def process_message(self, msg):
        {% for variable in table -%}
            self.{{ variable["python_name"] }}[self.k{%if variable["is_tab"] == True%}, :{%endif%}] = 
            {%-if variable["is_tab"] == True-%}
                np.array(msg.{{ variable["ros_name"] }}, dtype='{{ variable["type"] }}')
            {%-else-%}
                msg.{{ variable["ros_name"] }}
            {%-endif%}
        {% endfor %}
        return

    def resize_data_array(self):
        {% for variable in table -%}
            self.{{ variable["python_name"] }} = np.resize(self.{{ variable["python_name"] }}, 
        {%-if variable["is_tab"] == True-%}
            [self.k, {{ variable["tab_count"] }}]
        {%-else-%}
            self.k
        {%-endif-%})
        {% endfor %}
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
                                {{ variable["python_name"] }}=self.{{ variable["python_name"] }},{% endfor %})

    def load_message_from_file(self):
        data = np.load(self.topic_name_dir + "/" + self.topic_name_file, allow_pickle=True)
        self.time = data['time']{% for variable in table %}
        self.{{ variable["python_name"] }} = data['{{ variable["python_name"] }}']{% endfor %}
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
    table = []

    def add_table_item(item_, filed_type=None, python_name=None, ros_name=None, is_tab=False, tab_count=0):
        python_name = item_ if python_name is None else python_name
        ros_name = item_ if ros_name is None else ros_name
        filed_type = filed_type if filed_type is not None else fields[item_]
        table.append({"python_name":python_name,
                              "type":filed_type,
                              "ros_name":ros_name,
                              "is_tab":is_tab,
                              "tab_count":tab_count})

    for item in fields:
        if fields[item] == "boolean":
            add_table_item(item, "bool")
        elif \
                fields[item] == "rcl_interfaces/ParameterValue" or fields[item] == "string" or fields[
                    item] == "sequence<uint8>" or fields[item] == "builtin_interfaces/Time":
            add_table_item(item, "object")
        elif "[" in fields[item]:
            split_result = re.split(r'[\[\]]', fields[item])
            variable_type = split_result[0]
            variable_nb = int(split_result[1])
            if variable_nb < 10:
                for i in range(variable_nb):
                    add_table_item(item, filed_type=variable_type, python_name=item + str(i), ros_name=item + "[" + str(i) + "]")
            else:
                if variable_type == "uint8" or variable_type == "float":
                    add_table_item(item, filed_type=variable_type, is_tab=True, tab_count=variable_nb)
                else:
                    add_table_item(item, filed_type="object", is_tab=True, tab_count=variable_nb)
        elif fields[item] == "geometry_msgs/Vector3":
            add_table_item(item, filed_type="float", python_name=item + "_x", ros_name=item + ".x")
            add_table_item(item, filed_type="float", python_name=item + "_y", ros_name=item + ".y")
            add_table_item(item, filed_type="float", python_name=item + "_z", ros_name=item + ".z")
        else:
            add_table_item(item)
    print(table)

    # Special case for SeafoilLog
    for i, item in enumerate(table):
        if item["python_name"] == "time":
            item["python_name"] = "time_gnss"
        if item["python_name"] == "file":
            item["python_name"] = "file_name"

    tm = Template(template_msg)
    msg = tm.render(class_name=interface_name, table=table)

    file_name = "../msg/seafoil_" + interface_name_lower + ".py"

    file_object = open(file_name, "w+")
    file_object.write(msg)
    # print("Generate " + file_name)

    print("from .msg.seafoil_" + interface_name_lower + " import " + "Seafoil" + interface_name)


if __name__ == '__main__':
    generate_interface_bag_file(sys.argv[1], sys.argv[2])
