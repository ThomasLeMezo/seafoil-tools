import sqlite3
import os
import time
from datetime import datetime, timedelta

class SeafoilDB:
    db_name = 'data/seafoil.db'
    sqliteConnection = None
    sqliteCursor = None

    def __init__(self):
        # Test if the databse file exist
        exists = os.path.exists(self.db_name)

        self.sqliteConnection = sqlite3.connect(self.db_name)
        self.sqliteConnection.row_factory = sqlite3.Row
        self.sqliteCursor = self.sqliteConnection.cursor()

        if not exists:
            print("Create new DB")
        self.create_db()

    # Create the db
    def create_db(self):

        # Ceate table for seafoil box
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS seafoil_box
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )''')

        # Create table for rider
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS rider
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT
        )''')

        # Create table for seafoil box configuration
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS seafoil_box_configuration
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            v500 REAL,
            v1850 REAL,
            heading_enable BOOLEAN,
            voice_interval INTEGER,
            height_too_high REAL,
            height_high REAL,
            min_speed_sound REAL
        )''')


        # Create table for session
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS session
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            start_date DATETIME DEFAULT 0,
            end_date DATETIME DEFAULT 0,
            rider_id INTEGER,
            wind_mean_heading REAL,
            FOREIGN KEY (rider_id) REFERENCES rider(id)
        )''')

        # Create table for log
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS log
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            starting_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            session INTEGER,
            is_download BOOLEAN DEFAULT 0,
            type INTEGER,
            FOREIGN KEY (session) REFERENCES session(id)
        )''')

        # Create table for windfoil equipement
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_equipment
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer TEXT,
            model TEXT,
            year INTEGER,
            comment TEXT
        )''')

        # Create table for windfoil board
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_board
        (
            id INTEGER PRIMARY KEY,
            width REAL,
            length REAL,
            volume REAL,
            FOREIGN KEY (id) REFERENCES windfoil_equipment(id)
        )''')

        # Create table for windfoil sail
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_sail
        (
            id INTEGER PRIMARY KEY,
            surface REAL,
            FOREIGN KEY (id) REFERENCES windfoil_equipment(id)
        )''')

        # Create table for windfoil front foil
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_front_foil
        (
            id INTEGER PRIMARY KEY,
            surface REAL,
            FOREIGN KEY (id) REFERENCES windfoil_equipment(id)
        )''')

        # Create table for windfoil back foil
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_back_foil
        (
            id INTEGER PRIMARY KEY,
            surface REAL,
            FOREIGN KEY (id) REFERENCES windfoil_equipment(id)
        )''')

        # Create table for windfoil foil mast
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_foil_mast
        (
            id INTEGER PRIMARY KEY,
            length REAL,
            FOREIGN KEY (id) REFERENCES windfoil_equipment(id)
        )''')

        # Create table for windfoil fuselage
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_fuselage
        (
            id INTEGER PRIMARY KEY,
            length REAL,
            FOREIGN KEY (id) REFERENCES windfoil_equipment(id)
        )''')

        # Create table for windfoil session setup
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_session_setup
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            start_time DATETIME DEFAULT 0,
            end_time DATETIME DEFAULT 0,
            board INTEGER,
            sail INTEGER,
            front_foil INTEGER,
            back_foil INTEGER,
            foil_mast INTEGER,
            session INTEGER,
            rake REAL,
            stab_shim REAL,
            mast_foot_position REAL,
            FOREIGN KEY (board) REFERENCES windfoil_board(id),
            FOREIGN KEY (sail) REFERENCES windfoil_sail(id),
            FOREIGN KEY (front_foil) REFERENCES windfoil_front_foil(id),
            FOREIGN KEY (back_foil) REFERENCES windfoil_back_foil(id),
            FOREIGN KEY (foil_mast) REFERENCES windfoil_foil_mast(id),
            FOREIGN KEY (session) REFERENCES session(id)
        )''')

    # Set configuration for a seafoil box
    def set_configuration(self, data):
        if data['id'] is not None:
            self.sqliteCursor.execute('''UPDATE seafoil_box_configuration SET name = ?, 
                                                                                    v500 = ?, 
                                                                                    v1850 = ?, 
                                                                                    heading_enable = ?, 
                                                                                    voice_interval = ?, 
                                                                                    height_too_high = ?, 
                                                                                    height_high = ?, 
                                                                                    min_speed_sound = ? 
                                                                                    WHERE id = ?''',
                                                                                    (data['name'],
                                                                                     data['v500'],
                                                                                     data['v1850'],
                                                                                     data['heading_enable'],
                                                                                     data['voice_interval'],
                                                                                     data['height_too_high'],
                                                                                     data['height_high'],
                                                                                     data['min_speed_sound'],
                                                                                     data['id']))
        else:
            print(f"Save configuration {data['name']}")
            self.sqliteCursor.execute('''INSERT INTO seafoil_box_configuration (name, 
                                                                                    v500, 
                                                                                    v1850, 
                                                                                    heading_enable, 
                                                                                    voice_interval, 
                                                                                    height_too_high, 
                                                                                    height_high, 
                                                                                    min_speed_sound) 
                                                                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                                                                     (data['name'],
                                                                                      data['v500'],
                                                                                      data['v1850'],
                                                                                      data['heading_enable'],
                                                                                      data['voice_interval'],
                                                                                      data['height_too_high'],
                                                                                      data['height_high'],
                                                                                      data['min_speed_sound']))
        self.sqliteConnection.commit()

    # Get All configurations
    def get_configuration_all(self):
        self.sqliteCursor.execute('''SELECT * FROM seafoil_box_configuration''')
        return self.sqliteCursor.fetchall()

    def get_configuration_last(self):
        self.sqliteCursor.execute('''SELECT * FROM seafoil_box_configuration ORDER BY id DESC LIMIT 1''')
        return self.sqliteCursor.fetchone()

    # Get configuration by id
    def get_configuration_by_id(self, id):
        self.sqliteCursor.execute('''SELECT * FROM seafoil_box_configuration WHERE id = ?''', (id,))
        return self.sqliteCursor.fetchone()

    # Remove configuration by id
    def remove_configuration(self, id):
        self.sqliteCursor.execute('''DELETE FROM seafoil_box_configuration WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Get all windfoil_equipment and windfoil_fuselage where id is in windfoil_fuselage (left join)
    def get_windfoil_fuselage_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_fuselage ON windfoil_equipment.id = windfoil_fuselage.id WHERE windfoil_fuselage.id IS NOT NULL''')
        return self.sqliteCursor.fetchall()

    # Get all windfoil_equipment and windfoil_board where id is in windfoil_board (left join)
    def get_windfoil_board_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_board ON windfoil_equipment.id = windfoil_board.id WHERE windfoil_board.id IS NOT NULL''')
        return self.sqliteCursor.fetchall()

    # Get all windfoil_equipment and windfoil_sail where id is in windfoil_sail (left join)
    def get_windfoil_sail_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_sail ON windfoil_equipment.id = windfoil_sail.id WHERE windfoil_sail.id IS NOT NULL''')
        return self.sqliteCursor.fetchall()

    # Get all windfoil_equipment and windfoil_front_foil where id is in windfoil_front_foil (left join)
    def get_windfoil_front_foil_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_front_foil ON windfoil_equipment.id = windfoil_front_foil.id WHERE windfoil_front_foil.id IS NOT NULL''')
        return self.sqliteCursor.fetchall()

    # Get all windfoil_equipment and windfoil_back_foil where id is in windfoil_back_foil (left join)
    def get_windfoil_back_foil_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_back_foil ON windfoil_equipment.id = windfoil_back_foil.id WHERE windfoil_back_foil.id IS NOT NULL''')
        return self.sqliteCursor.fetchall()

    # Get all windfoil_equipment and windfoil_foil_mast where id is in windfoil_foil_mast (left join)
    def get_windfoil_foil_mast_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_foil_mast ON windfoil_equipment.id = windfoil_foil_mast.id WHERE windfoil_foil_mast.id IS NOT NULL''')
        return self.sqliteCursor.fetchall()

    # Add new windfoil equipment to the database if it does not exist (data is a dict)
    def insert_windfoil_equipment(self, data):
        if data['id'] is None:
            # Add a new equipement and get the id
            self.sqliteCursor.execute('''INSERT INTO windfoil_equipment (manufacturer, model, year, comment) VALUES (?, ?, ?, ?)''', (data['manufacturer'], data['model'], data['year'], data['comment']))
            self.sqliteConnection.commit()
            return self.sqliteCursor.lastrowid
        else:
            # Update the equipement
            self.sqliteCursor.execute('''UPDATE windfoil_equipment SET manufacturer = ?, model = ?, year = ?, comment = ? WHERE id = ?''', (data['manufacturer'], data['model'], data['year'], data['comment'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Add new windfoil fuselage to the database if it does not exist (data is a dict)
    def insert_windfoil_fuselage(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the fuselage with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_fuselage (id, length) VALUES (?, ?)''', (equipment_id, data['length']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the fuselage
            self.sqliteCursor.execute('''UPDATE windfoil_fuselage SET length = ? WHERE id = ?''', (data['length'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Add new windfoil board to the database if it does not exist (data is a dict)
    def insert_windfoil_board(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the board with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_board (id, width, length, volume) VALUES (?, ?, ?, ?)''', (equipment_id, data['width'], data['length'], data['volume']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the board
            self.sqliteCursor.execute('''UPDATE windfoil_board SET width = ?, length = ?, volume = ? WHERE id = ?''', (data['width'], data['length'], data['volume'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Add new windfoil sail to the database if it does not exist (data is a dict)
    def insert_windfoil_sail(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the sail with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_sail (id, surface) VALUES (?, ?)''', (equipment_id, data['surface']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the sail
            self.sqliteCursor.execute('''UPDATE windfoil_sail SET surface = ? WHERE id = ?''', (data['surface'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Add new windfoil front foil to the database if it does not exist (data is a dict)
    def insert_windfoil_front_foil(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the front foil with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_front_foil (id, surface) VALUES (?, ?)''', (equipment_id, data['surface']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the front foil
            self.sqliteCursor.execute('''UPDATE windfoil_front_foil SET surface = ? WHERE id = ?''', (data['surface'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Add new windfoil back foil to the database if it does not exist (data is a dict)
    def insert_windfoil_back_foil(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the back foil with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_back_foil (id, surface) VALUES (?, ?)''', (equipment_id, data['surface']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the back foil
            self.sqliteCursor.execute('''UPDATE windfoil_back_foil SET surface = ? WHERE id = ?''', (data['surface'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Add new windfoil foil mast to the database if it does not exist (data is a dict)
    def insert_windfoil_foil_mast(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the foil mast with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_foil_mast (id, length) VALUES (?, ?)''', (equipment_id, data['length']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the foil mast
            self.sqliteCursor.execute('''UPDATE windfoil_foil_mast SET length = ? WHERE id = ?''', (data['length'], data['id']))
            self.sqliteConnection.commit()
            return data['id']

    # Remove windfoil equipment by id
    def remove_windfoil_equipment(self, id):
        self.sqliteCursor.execute('''DELETE FROM windfoil_equipment WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Remove windfoil board by id
    def remove_windfoil_board(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_board WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Remove windfoil sail by id
    def remove_windfoil_sail(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_sail WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Remove windfoil front foil by id
    def remove_windfoil_front_foil(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_front_foil WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Remove windfoil back foil by id
    def remove_windfoil_back_foil(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_back_foil WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Remove windfoil foil mast by id
    def remove_windfoil_foil_mast(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_foil_mast WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Remove windfoil fuselage by id
    def remove_windfoil_fuselage(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_fuselage WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Get all windfoil equipment manufacturers
    def get_windfoil_manufacturer_all(self):
        self.sqliteCursor.execute('''SELECT DISTINCT manufacturer FROM windfoil_equipment''')
        return self.sqliteCursor.fetchall()

    # Get all windfoil session
    def get_windfoil_session_all_sort_start_date(self):
        self.sqliteCursor.execute('''SELECT * FROM session ORDER BY start_date DESC''')
        return self.sqliteCursor.fetchall()

    def convert_log_type_from_str(self, log_type):
        if log_type == 'rosbag':
            return 0
        elif log_type == 'gpx':
            return 1
        return -1

    def convert_log_type_from_int(self, log_type):
        if log_type == 0:
            return 'rosbag'
        elif log_type == 1:
            return 'gpx'
        return ''

    # Add new log file to the database if it does not exist and return the id
    # type = 0 for rosbag, 1 for gpx
    def insert_log(self, name, starting_time, type='rosbag'):
        # Test if the log file is already in the database and return the id if it is
        self.sqliteCursor.execute('''SELECT * FROM log WHERE name = ?''', (name,))
        row = self.sqliteCursor.fetchone()
        if row:
            # Return is_new, row
            return row['id'], row['is_download'], False

        type_id = self.convert_log_type_from_str(type)

        self.sqliteCursor.execute('''INSERT INTO log (name, starting_time, type) VALUES (?, ?, ?)''', (name, starting_time, type_id))
        self.sqliteConnection.commit()
        # Return the if of the last inserted row, is_download = False, is_new = True
        return self.sqliteCursor.lastrowid, False, True

    # Return the log file by id
    def get_log(self, id):
        self.sqliteCursor.execute('''SELECT * FROM log WHERE id = ?''', (id,))
        return self.sqliteCursor.fetchone()

    # Remove log
    def remove_log(self, id):
        self.sqliteCursor.execute('''DELETE FROM log WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Get all logs
    def get_all_logs(self):
        self.sqliteCursor.execute('''SELECT * FROM log''')
        return self.sqliteCursor.fetchall()

    # Return True if the name and starting_time are not in the database
    def is_new_log(self, name):
        self.sqliteCursor.execute('''SELECT * FROM log WHERE name = ?''', (name,))
        return self.sqliteCursor.fetchone() is None

    # Update log folder
    def set_log_download(self, id):
        self.sqliteCursor.execute('''UPDATE log SET is_download = 1 WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Update log session id
    def update_log_session(self, id, session):
        self.sqliteCursor.execute('''UPDATE log SET session = ? WHERE id = ?''', (session, id))
        self.sqliteConnection.commit()

    # Add new seafoil_box
    def insert_seafoil_box(self, name):
        self.sqliteCursor.execute('''INSERT INTO seafoil_box (name) VALUES (?)''', (name,))
        self.sqliteConnection.commit()

    # Get all seafoil_box
    def get_seafoil_box_all(self):
        self.sqliteCursor.execute('''SELECT * FROM seafoil_box''')
        return self.sqliteCursor.fetchall()

# Test the class
if __name__ == '__main__':
    db = SeafoilDB()

    db.insert_windfoil_fuselage({'manufacturer': 'AFS', 'model': '', 'year': 2021, 'comment': '', 'length': 0.95, 'id': None})

    db.insert_windfoil_fuselage({'manufacturer': 'AFS', 'model': '', 'year': 2021, 'comment': '', 'length': 0.6, 'id': 1})




