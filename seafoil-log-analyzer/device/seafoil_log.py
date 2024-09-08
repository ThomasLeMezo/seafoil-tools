import subprocess, os
import threading

from db.seafoil_db import SeafoilDB
from device.seafoil_connexion import SeafoilConnexion
from seafoil_log_analyzer import SeafoilLogAnalyser

# class to manage the sessions
class SeafoilLog:
    def __init__(self):
        self.db = SeafoilDB()
        self.logs = self.db.get_all_logs()
        self.sc = SeafoilConnexion()

        self.opended_log = []

    def add_gpx_files(self, file_paths):
        list_added = []
        for file_path in file_paths:
            is_added, db_id = self.sc.add_gpx_file(file_path)
            if is_added:
                list_added.append(db_id)
        self.logs = self.db.get_all_logs()
        return list_added

    def open_log(self, db_id):
        log = self.db.get_log(db_id)

        file_path = self.sc.get_file_directory(log['id'], log['name'])
        print(file_path)

        # Create new SeafoilLogAnalyser object
        self.opended_log.append(SeafoilLogAnalyser(file_path))

    def remove_log(self, db_id):
        self.sc.remove_log(db_id)
        self.logs = self.db.get_all_logs()