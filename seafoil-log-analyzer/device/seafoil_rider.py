import subprocess, os
from ..db.seafoil_db import SeafoilDB

# class to manage the list of rider
class SeafoilRider():
    def __init__(self):
        self.db = SeafoilDB()

        self.rider_header = ['is_default', 'display_order', 'first_name', 'last_name', 'manual_add', "v500", "v1850", "vmax", "vjibe", "vhour"]
        self.rider_header_display = ['Défaut', 'Ordre', 'Prénom', 'Nom', 'Manuel', "V500", "V1850", "Vmax", "Vjibe", "Vheure"]

        self.rider_list = []
        self.update_lists()

    def update_lists(self):
        self.rider_list = self.db.get_rider_all_with_statistics()

    def set_default_rider(self, rider_id):
        self.db.set_default_rider(self.rider_list[rider_id]['id'])
        self.update_lists()
