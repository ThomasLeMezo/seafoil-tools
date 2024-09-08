import subprocess, os
from db.seafoil_db import SeafoilDB

# class to manage the sessions
class SeafoilSession():
    def __init__(self):
        self.db = SeafoilDB()
        self.session_list = self.db.get_windfoil_session_all_sort_start_date()