import datetime
import subprocess, os
from db.seafoil_db import SeafoilDB
from device.seafoil_connexion import SeafoilConnexion
from device.seafoil_equipement import SeafoilEquipement
from device.seafoil_log import SeafoilLog

# class to manage the sessions
class SeafoilNewSession():
    def __init__(self, session_id=None):
        self.db = SeafoilDB()
        self.sc = SeafoilConnexion()
        self.se = SeafoilEquipement()
        self.sl = SeafoilLog(session_id, False)

        # Set current time in posix format
        self.rider_current_index = None

        self.session_id = session_id
        self.session = self.db.get_session(session_id)
        if self.session is None:
            self.session = {'id': None,
                            'start_date': datetime.datetime.now().timestamp(),
                            'end_date': datetime.datetime.now().timestamp(),
                            'rider_id': None,
                            'comment': None}
        else:
            self.session = dict(self.session)
            self.rider_current_index = self.session['rider_id']

        self.session_setup = self.db.get_session_setup(session_id)
        if self.session_setup is not None:
            self.session_setup = dict(self.session_setup)
            self.se.import_session_setup(self.session_setup)

        self.log_list = self.sl.logs
        self.rider_list = []
        self.equipment_current_index = [None] * len(self.se.equipment_names)

        self.update_lists()

    def save(self):
        self.session['rider_id'] = self.rider_current_index

        # Session
        self.session_id = self.db.save_session(self.session)

        # Session setup
        data_session_setup = self.se.export_session_setup(self.session_setup)
        data_session_setup['session'] = self.session_id
        data_session_setup['start_time'] = self.session['start_date']
        data_session_setup['end_time'] = self.session['end_date']
        self.db.save_session_setup(data_session_setup)

        # Associate the logs to the session
        self.sl.associate_logs_to_session(self.session_id)

        # Update the session list
        self.sl.update()

    def update_lists(self):
        self.rider_list = self.db.get_all_riders()
        self.se.update()

    def add_log_to_list(self, db_id):
        return self.sl.add_log_to_list(db_id)

    def remove_log(self, index):
        return self.sl.remove_log_from_list(index)

    def add_rider(self, first_name, last_name):
        self.db.add_rider(first_name, last_name)
        self.update_lists()