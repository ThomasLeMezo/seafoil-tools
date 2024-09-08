import subprocess, os
from db.seafoil_db import SeafoilDB
from device.seafoil_connexion import SeafoilConnexion

# class to manage the sessions
class SeafoilNewSession():
    def __init__(self):
        self.db = SeafoilDB()
        self.sc = SeafoilConnexion()

        self.log_list = []


    def import_gpx(self, file_path):
        # If a file is selected
        if file_path:

            is_success, log_db_id = self.sc.add_gpx_file(file_path)
            if not is_success:
                return False

            # Add the gpx file in the list if it is not already in the list
            return self.add_log_to_list(log_db_id)
        return False

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