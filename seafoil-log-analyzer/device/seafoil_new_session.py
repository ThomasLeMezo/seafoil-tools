import subprocess, os
from db.seafoil_db import SeafoilDB
from device.seafoil_connexion import SeafoilConnexion
from device.seafoil_equipement import SeafoilEquipement

# class to manage the sessions
class SeafoilNewSession():
    def __init__(self):
        self.rider_current_index = None
        self.db = SeafoilDB()
        self.sc = SeafoilConnexion()
        self.se = SeafoilEquipement()

        self.log_list = []
        self.rider_list = []
        self.equipment_current_index = [None] * len(self.se.equipment_names)

        self.update_lists()

    def update_lists(self):
        self.rider_list = self.db.get_all_riders()
        self.se.update()

    def add_log_to_list(self, db_id):
        new_log = self.db.get_log(db_id)
        if new_log:
            for log in self.log_list:
                if log['id'] == new_log['id']   :
                    return False

            self.log_list.append(new_log)
            return True
        return False

    def remove_log(self, index):
        if 0 <= index < len(self.log_list):
            del self.log_list[index]
            return True
        return False

    def add_rider(self, first_name, last_name):
        self.db.add_rider(first_name, last_name)
        self.update_rider_list()