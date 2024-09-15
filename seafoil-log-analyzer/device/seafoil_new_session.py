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
                            'start_date': None,
                            'end_date': None,
                            'rider_id': None,
                            'wind_mean_heading' : None,
                            'v500' : None,
                            'v1850' : None,
                            'vmax' : None,
                            'vjibe' : None,
                            'vhour' : None,
                            'comment': ""}
        else:
            self.session = dict(self.session)

        self.session['duration'] = None

        self.session_setup = self.db.get_session_setup(session_id)
        if self.session_setup is not None:
            self.session_setup = dict(self.session_setup)
            self.se.import_session_setup(self.session_setup)

        self.rider_list = []
        self.equipment_current_index = [None] * len(self.se.equipment_names)
        self.update_lists()

    # Get rider index from rider_id
    def get_rider_index(self, rider_id):
        for i in range(len(self.rider_list)):
            if self.rider_list[i]['id'] == rider_id:
                return i
        return None

    def compute_times(self):
        self.sl.compute_times()
        self.session['start_date'] = self.sl.starting_time
        self.session['ending_date'] = self.sl.ending_time
        self.session['duration'] = self.sl.log_duration

    def update(self):
        self.sl.update()
        self.update_lists()

    def save(self):
        self.session['rider_id'] = self.rider_list[self.rider_current_index]['id']

        # Session
        self.session_id = self.db.save_session(self.session)

        # Associate the logs to the session
        self.sl.associate_logs_to_session(self.session_id)
        self.sl.desassociate_log_to_session()

        # Update the session list
        self.sl.update()

        # Session setup
        data_session_setup = self.se.export_session_setup(self.session_setup)
        data_session_setup['session'] = self.session_id
        data_session_setup['start_time'] = self.session['start_date']
        data_session_setup['end_time'] = self.session['end_date']
        self.db.save_session_setup(data_session_setup)

    def update_lists(self):
        self.rider_list = self.db.get_rider_all()
        self.se.update()
        self.rider_current_index = self.get_rider_index(self.session['rider_id'])

    def add_log_to_list(self, db_id):
        return self.sl.add_log_to_list(db_id)

    def remove_log(self, index):
        return self.sl.remove_log_from_list(index)

    def add_rider(self, first_name, last_name):
        self.db.add_rider(first_name, last_name)
        self.update_lists()