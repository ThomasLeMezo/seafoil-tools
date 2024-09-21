import subprocess, os
from ..db.seafoil_db import SeafoilDB

# class to manage the yaml configuration file of the seafoil box
class SeafoilEquipement():
    def __init__(self):
        self.db = SeafoilDB()

        self.equipment_names = ['Board', 'Sail', 'Front foil', 'Stabilizer', 'Foil mast', 'Fuselage']
        self.equipment_session_names = ['board', 'sail', 'front_foil', 'stabilizer', 'foil_mast', 'fuselage']
        self.equipment_data = [None] * len(self.equipment_names)
        self.equipment_current_index = [None] * len(self.equipment_names)
        self.equipment_function_get = [self.db.get_windfoil_board_all,
                                       self.db.get_windfoil_sail_all,
                                       self.db.get_windfoil_front_foil_all,
                                       self.db.get_windfoil_stabilizer_all,
                                       self.db.get_windfoil_foil_mast_all,
                                       self.db.get_windfoil_fuselage_all,
                                       ]
        self.equipment_function_remove = [self.db.remove_windfoil_board,
                                            self.db.remove_windfoil_sail,
                                            self.db.remove_windfoil_front_foil,
                                            self.db.remove_windfoil_stabilizer,
                                            self.db.remove_windfoil_foil_mast,
                                            self.db.remove_windfoil_fuselage,
                                            ]
        self.equipment_function_insert = [self.db.insert_windfoil_board,
                                            self.db.insert_windfoil_sail,
                                            self.db.insert_windfoil_front_foil,
                                            self.db.insert_windfoil_stabilizer,
                                            self.db.insert_windfoil_foil_mast,
                                            self.db.insert_windfoil_fuselage,
                                            ]
        self.db_get_equipment()

        self.rake = 0.
        self.stab_shim = 0.
        self.mast_foot_position = 0.

        # As an array of string
        self.manufacturers_list = [data['manufacturer'] for data in self.db.get_windfoil_manufacturer_all()]

    def update(self):
        self.db_get_equipment()

    def export_session_setup(self, data=None):
        if data is None:
            data = {}
        for i in range(len(self.equipment_names)):
            # Test if the index is not None and if the key exists
            if self.equipment_current_index[i] is not None:
                data[self.equipment_session_names[i]] = self.equipment_data[i][self.equipment_current_index[i]]['id']
            else:
                data[self.equipment_session_names[i]] = None
        data['rake'] = self.rake
        data['stab_shim'] = self.stab_shim
        data['mast_foot_position'] = self.mast_foot_position
        return data

    def import_session_setup(self, data):
        for i in range(len(self.equipment_names)):
            for j in range(len(self.equipment_data[i])):
                if self.equipment_data[i][j]['id'] == data[self.equipment_session_names[i]]:
                    self.equipment_current_index[i] = j
                    break
        self.rake = data['rake']
        self.stab_shim = data['stab_shim']
        self.mast_foot_position = data['mast_foot_position']

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

    def get_equipment_name(self, data, category):
        return self.equipment_text(data) + self.equipment_text_postfix(data, category)

    def equipment_text(self, data):
        return f"{data['manufacturer']} {data['model']}, {data['year']}"
    def equipment_text_postfix(self, data, category):
        if category == 'Board':
            return f" [{data['volume']:.0f} L, {data['width']*100:.0f} cm, {data['length']:.0f} m]"
        elif category == 'Sail':
            return f" [{data['surface']:.1f} m²]"
        elif category == 'Front foil':
            return f" [{data['surface']*1e4:.0f} cm²]"
        elif category == 'Stabilizer':
            return f" [{data['surface']*1e4:.0f} cm²]"
        elif category == 'Foil mast':
            return f" [{data['length']*100:.0f} cm]"
        elif category == 'Fuselage':
            return f" [{data['length']*100:.0f} cm]"
        else:
            return ""
