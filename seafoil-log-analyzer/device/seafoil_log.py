import subprocess, os
import threading

from PyQt5.QtCore import pyqtSignal

from ..db.seafoil_db import SeafoilDB
from .seafoil_connexion import SeafoilConnexion
from ..log_analyzer import SeafoilBag
from ..log_analyzer import SeafoilLogAnalyser

# class to manage the sessions
class SeafoilLog:
    def __init__(self, session_id=None, load_all_logs=True, load_only_unlinked=False):
        self.db = SeafoilDB()
        self.logs = []
        self.logs_associated = []

        self.session_id = session_id
        self.load_all_logs = load_all_logs
        self.load_only_unlinked = load_only_unlinked
        self.update()

        self.sc = SeafoilConnexion()

        self.opended_log = []
        self.removed_logs = []
        self.removed_logs_associated = []

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
            self.logs_associated = self.db.get_logs_associated_to_session(self.session_id)
            self.starting_time = self.db.get_starting_time_session(self.session_id)['starting_time']
            self.ending_time = self.db.get_ending_time_session(self.session_id)['ending_time']
        elif self.load_all_logs:
            if self.load_only_unlinked:
                self.logs = self.db.get_unaffected_logs()
            else:
                self.logs = self.db.get_all_logs()

    # Associate logs to the session
    def link_logs_to_session(self, session_id):
        for log in self.logs:
            self.db.add_session_log_link(log['id'], session_id)
        # self.update()

    def unlink_log_to_session(self, session_id):
        for log in self.removed_logs:
            self.db.remove_session_log_link(log['id'], session_id)
        self.removed_logs = []
        # self.update()

    def associate_log_to_session(self, session_id):
        for log in self.logs_associated:
            self.db.add_session_log_association(log['id'], session_id)
        # self.update()

    def unassociate_log_to_session(self, session_id):
        for log in self.removed_logs_associated:
            self.db.remove_session_log_association(log['id'], session_id)
        self.removed_logs_associated = []
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

    def add_seafoil_log(self, dirs_path, process_ui=None):
        list_added = []
        for dir_path in dirs_path:
            is_added, db_id = self.sc.import_seafoil_log(dir_path)
            if db_id is not None:
                list_added.append(db_id)

        for db_id in list_added:
            self.process_log(db_id, process_ui)

        self.logs = self.db.get_all_logs()
        return list_added

    def open_log(self, db_id):
        log = self.db.get_log(db_id)

        file_path = self.sc.get_file_directory(log['id'], log['name'])
        print(file_path)

        # Create new SeafoilLogAnalyser object
        self.opended_log.append(SeafoilLogAnalyser(file_path))

    def get_seafoil_bag(self, db_id):
        log = self.db.get_log_by_id(db_id)

        file_path = self.sc.get_file_directory(log['id'], log['name'])
        print(file_path)

        # Create new SeafoilLogAnalyser object
        return SeafoilBag(file_path), log

    def open_log_from_index(self, index, is_associated=False):
        if is_associated:
            if 0 <= index < len(self.logs_associated):
                self.open_log(self.logs_associated[index]['id'])
                return True
        else:
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

    def remove_log_from_list(self, index, is_associated=False):
        if is_associated:
            if 0 <= index < len(self.logs_associated):
                self.removed_logs_associated.append(self.logs_associated[index])
                del self.logs_associated[index]
                return True
        else:
            if 0 <= index < len(self.logs):
                self.removed_logs.append(self.logs[index])
                del self.logs[index]
                return True
        return False

    def add_log_to_list(self, db_id, is_associated=False):
        new_log = self.db.get_log(db_id)
        if new_log:
            for log in (self.logs if is_associated else self.logs_associated):
                if log['id'] == new_log['id']:
                    return False
            if is_associated:
                self.logs_associated.append(new_log)
            else:
                self.logs.append(new_log)
            return True
        return False

    def process_log(self, db_id, process_ui_function=None):
        log = self.db.get_log(db_id)
        if log is None:
            return False
        file_path = self.sc.get_file_directory(log['id'], log['name'])
        try:
            # Process the log
            print("Processing log: " + file_path)
            # Signal
            sfb = SeafoilBag(file_path)
            if process_ui_function is not None:
                sfb.signal_load_data.connect(process_ui_function)
            sfb.load_data()

            # Update db with statistics from the log
            self.db.add_log_statistics(log['id'], sfb.get_statistics())

            # if log is not a gpx file, update end time
            if not self.db.is_log_gpx(log['id']):
                self.db.update_log_time(log['id'], sfb.get_starting_time_timestamp(), sfb.get_ending_time_timestamp())

        except Exception as e:
            print("Error processing log: " + file_path + " " + str(e))
            return False
        return True

    def open_log_folder(self, db_id, data_folder=False):
        log = self.db.get_log(db_id)
        if log is not None:
            file_path = self.sc.get_file_directory(log['id'], log['name'])
            if data_folder:
                file_path += "/data"
            # If on linux, open the folder with nautilus
            if os.name == 'posix':
                subprocess.Popen((["xdg-open", file_path]))
            else:
                os.startfile(file_path)