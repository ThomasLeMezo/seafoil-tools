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

    def add_gpx_files(self, file_paths):
        for file_path in file_paths:
            self.sc.add_gpx_file(file_path)
        self.logs = self.db.get_all_logs()

    def open_log(self, db_id):
        log = self.db.get_log(db_id)

        file_path = self.sc.get_file_directory(log['id'], log['type'], log['name'])
        print(file_path)

        # Call open_log(file_path) in new process
        sla = SeafoilLogAnalyser(file_path)

        return True