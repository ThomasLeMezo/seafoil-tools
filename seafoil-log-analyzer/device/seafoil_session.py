import subprocess, os
from db.seafoil_db import SeafoilDB

# class to manage the sessions
class SeafoilSession():
    def __init__(self):
        self.db = SeafoilDB()
        self.session_list = self.db.get_windfoil_session_all_sort_start_date()

    def remove_session(self, index):
        self.db.remove_session(self.session_list[index]['id'])
        self.session_list = self.db.get_windfoil_session_all_sort_start_date()

    def update_session_list(self):
        self.session_list = self.db.get_windfoil_session_all_sort_start_date()