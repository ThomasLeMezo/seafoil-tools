import subprocess, os
import threading

from db.seafoil_db import SeafoilDB
from device.seafoil_connexion import SeafoilConnexion
from log_analyzer import SeafoilBag
from log_analyzer import SeafoilLogAnalyser

# class to manage the sessions
class SeafoilLog:
    def __init__(self, session_id=None, load_all_logs=True, load_only_unaffected=False):
        self.db = SeafoilDB()
        self.logs = []

        self.session_id = session_id
        self.load_all_logs = load_all_logs
        self.load_only_unaffected = load_only_unaffected
        self.update()

        self.sc = SeafoilConnexion()

        self.opended_log = []
        self.removed_logs = []

        self.starting_time = None
        self.ending_time = None
        self.log_duration = 0.0

    def is_empty(self):
        return len(self.logs) == 0

    def compute_times(self):
        for log in self.logs:
            if self.starting_time is None:
                self.starting_time = log['starting_time']
            elif log['starting_time'] is not None:
                self.starting_time = min(self.starting_time, log['starting_time'])

            if self.ending_time is None:
                self.ending_time = log['ending_time']
            elif log['ending_time'] is not None:
                self.ending_time = max(self.ending_time, log['ending_time'])

        if self.starting_time is not None and self.ending_time is not None:
            self.log_duration = self.ending_time - self.starting_time

    def update(self):
        if self.session_id is not None:
            self.logs = self.db.get_logs_by_session(self.session_id)
            self.starting_time = self.db.get_starting_time_session(self.session_id)['starting_time']
            self.ending_time = self.db.get_ending_time_session(self.session_id)['ending_time']
        elif self.load_all_logs:
            if self.load_only_unaffected:
                self.logs = self.db.get_unaffected_logs()
            else:
                self.logs = self.db.get_all_logs()

    # Associate logs to the session
    def associate_logs_to_session(self, session_id):
        for log in self.logs:
            self.db.add_session_log_link(log['id'], session_id)
        self.update()

    def desassociate_log_to_session(self, session_id):
        for log in self.removed_logs:
            self.db.remove_session_log_association(log['id'], session_id)
        self.removed_logs = []
        self.update()

    def add_gpx_files(self, file_paths):
        list_added = []
        for file_path in file_paths:
            is_added, db_id = self.sc.add_gpx_file(file_path)
            if db_id is not None:
                list_added.append(db_id)

        for db_id in list_added:
            self.process_log(db_id)

        self.logs = self.db.get_all_logs()
        return list_added

    def add_seafoil_log(self, dirs_path):
        list_added = []
        for dir_path in dirs_path:
            is_added, db_id = self.sc.import_seafoil_log(dir_path)
            if db_id is not None:
                list_added.append(db_id)

        for db_id in list_added:
            self.process_log(db_id)

        self.logs = self.db.get_all_logs()
        return list_added

    def open_log(self, db_id):
        log = self.db.get_log(db_id)

        file_path = self.sc.get_file_directory(log['id'], log['name'])
        print(file_path)

        # Create new SeafoilLogAnalyser object
        self.opended_log.append(SeafoilLogAnalyser(file_path))

    def open_log_from_index(self, index):
        if 0 <= index < len(self.logs):
            self.open_log(self.logs[index]['id'])
            return True
        return False

    def remote_remove_log(self, db_id):
        if self.db.is_log_link_to_session(db_id):
            return False
        else:
            self.sc.remove_log(db_id)
            self.logs = self.db.get_all_logs()
            return True

    def remove_log_from_list(self, index):
        if 0 <= index < len(self.logs):
            self.removed_logs.append(self.logs[index])
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

    def process_log(self, db_id):
        log = self.db.get_log(db_id)
        if log is None:
            return False
        file_path = self.sc.get_file_directory(log['id'], log['name'])
        try:
            # Process the log
            print("Processing log: " + file_path)
            sfb = SeafoilBag(file_path)

            # Update db with statistics from the log
            self.db.add_log_statistics(log['id'], sfb.get_statistics())
            return True
        except Exception as e:
            print("Error processing log: " + file_path + " " + str(e))
            return False