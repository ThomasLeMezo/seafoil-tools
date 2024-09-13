import subprocess, os
import threading

from db.seafoil_db import SeafoilDB
from device.seafoil_connexion import SeafoilConnexion
from seafoil_log_analyzer import SeafoilLogAnalyser

# class to manage the sessions
class SeafoilLog:
    def __init__(self, session_id=None, load_all_logs=True):
        self.db = SeafoilDB()
        self.logs = []
        if session_id is not None:
            self.logs = self.db.get_logs_by_session(session_id)
        elif load_all_logs:
            self.logs = self.db.get_all_logs()
        self.sc = SeafoilConnexion()

        self.opended_log = []

    def update(self):
        self.logs = self.db.get_all_logs()

    # Associate logs to the session
    def associate_logs_to_session(self, session_id):
        for log in self.logs:
            self.db.associate_log_to_session(log['id'], session_id)
        self.update()

    def add_gpx_files(self, file_paths):
        list_added = []
        for file_path in file_paths:
            is_added, db_id = self.sc.add_gpx_file(file_path)
            if db_id is not None:
                list_added.append(db_id)
        self.logs = self.db.get_all_logs()
        return list_added

    def open_log(self, db_id):
        log = self.db.get_log(db_id)

        file_path = self.sc.get_file_directory(log['id'], log['name'])
        print(file_path)

        # Create new SeafoilLogAnalyser object
        self.opended_log.append(SeafoilLogAnalyser(file_path))

    def remote_remove_log(self, db_id):
        self.sc.remove_log(db_id)
        self.logs = self.db.get_all_logs()

    def remove_log_from_list(self, index):
        if 0 <= index < len(self.logs):
            del self.logs[index]
            return True
        return False

    def add_log_to_list(self, db_id):
        new_log = self.db.get_log(db_id)
        if new_log:
            for log in self.logs:
                if log['id'] == new_log['id']   :
                    return False

            self.logs.append(new_log)
            return True
        return False