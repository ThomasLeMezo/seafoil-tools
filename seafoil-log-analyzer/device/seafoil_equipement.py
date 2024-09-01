import subprocess, os
from db.seafoil_db import SeafoilDB
import yaml
from device.seafoil_connexion import SeafoilConnexion

# class to manage the yaml configuration file of the seafoil box
class SeafoilEquipement():
    def __init__(self):
        self.db = SeafoilDB()

        self.equipment_names = ['Board', 'Sail', 'Front foil', 'Stabilizer', 'Foil mast', 'Fuselage']
        self.equipment_data = [None] * len(self.equipment_names)
        self.equipment_function_get = [self.db.get_windfoil_board_all,
                                       self.db.get_windfoil_sail_all,
                                       self.db.get_windfoil_front_foil_all,
                                       self.db.get_windfoil_back_foil_all,
                                       self.db.get_windfoil_foil_mast_all,
                                       self.db.get_windfoil_fuselage_all,
                                       ]
        self.equipment_function_remove = [self.db.remove_windfoil_board,
                                            self.db.remove_windfoil_sail,
                                            self.db.remove_windfoil_front_foil,
                                            self.db.remove_windfoil_back_foil,
                                            self.db.remove_windfoil_foil_mast,
                                            self.db.remove_windfoil_fuselage,
                                            ]
        self.equipment_function_insert = [self.db.insert_windfoil_board,
                                            self.db.insert_windfoil_sail,
                                            self.db.insert_windfoil_front_foil,
                                            self.db.insert_windfoil_back_foil,
                                            self.db.insert_windfoil_foil_mast,
                                            self.db.insert_windfoil_fuselage,
                                            ]
        self.db_get_equipment()

        # As an array of string
        self.manufacturers_list = [data['manufacturer'] for data in self.db.get_windfoil_manufacturer_all()]

    def db_get_equipment(self):
        for i in range(len(self.equipment_names)):
            self.equipment_data[i] = self.equipment_function_get[i]()

    def db_remove_equipment(self, category, index):
        # find index of category
        for i in range(len(self.equipment_names)):
            if self.equipment_names[i] == category:
                self.equipment_function_remove[i](self.equipment_data[i][index]['id'])
                self.db_get_equipment()
                return  True

    def db_insert_equipment(self, category, data):
        # find index of category
        for i in range(len(self.equipment_names)):
            if self.equipment_names[i] == category:
                if data['index'] is None:
                    data['id'] = None
                else:
                    data['id'] = self.equipment_data[i][data['index']]['id']
                self.equipment_function_insert[i](data)
                self.db_get_equipment()
                return  True
        return False
