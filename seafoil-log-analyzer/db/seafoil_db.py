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
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS seafoil_box_identification
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )''')

        # Create table for rider
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS rider
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            manual_add BOOLEAN DEFAULT TRUE,
            display_order INTEGER,
            is_default BOOLEAN DEFAULT 0
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

        # Create table for statistics
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS statistics
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            v500 REAL,
            v1850 REAL,
            vmax REAL,
            vjibe REAL,
            vhour REAL
        )''')

        # Create table for session
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS session
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            start_date DATETIME DEFAULT 0,
            end_date DATETIME DEFAULT 0,
            rider_id INTEGER,
            wind_mean_heading REAL,
            comment TEXT,
            statistics_id INTEGER,
            FOREIGN KEY (rider_id) REFERENCES rider(id),
            FOREIGN KEY (statistics_id) REFERENCES statistics(id)
        )''')

        # Create table for water sport type
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS water_sport_type
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )''')
        # if the table is empty, add the default values
        self.sqliteCursor.execute('''SELECT * FROM water_sport_type''')
        if not self.sqliteCursor.fetchall():
            self.sqliteCursor.execute('''INSERT INTO water_sport_type (name) VALUES ('Windfoil')''')
            self.sqliteCursor.execute('''INSERT INTO water_sport_type (name) VALUES ('Kitefoil')''')
            self.sqliteCursor.execute('''INSERT INTO water_sport_type (name) VALUES ('Windsurf')''')
            self.sqliteCursor.execute('''INSERT INTO water_sport_type (name) VALUES ('Wingfoil')''')
            self.sqliteConnection.commit()

        # Create table for log
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS log
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            starting_time DATETIME DEFAULT 0,
            ending_time DATETIME DEFAULT 0,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_processed BOOLEAN DEFAULT 0,
            name TEXT NOT NULL,
            is_download BOOLEAN DEFAULT 0,
            type INTEGER,
            statistics_id INTEGER,
            water_sport_type INTEGER,
            rider_id INTEGER,
            FOREIGN KEY (rider_id) REFERENCES rider(id),
            FOREIGN KEY (water_sport_type) REFERENCES water_sport_type(id),
            FOREIGN KEY (statistics_id) REFERENCES statistics(id)
        )''')



        # Create table for session to log link
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS session_log
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session INTEGER,
            log INTEGER,
            FOREIGN KEY (session) REFERENCES session(id),
            FOREIGN KEY (log) REFERENCES log(id)
        )''')

        # Create table for session to log association
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS session_log_association
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session INTEGER,
            log INTEGER,
            FOREIGN KEY (session) REFERENCES session(id),   
            FOREIGN KEY (log) REFERENCES log(id)
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
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_stabilizer
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
            stabilizer INTEGER,
            foil_mast INTEGER,
            fuselage INTEGER,
            session INTEGER,
            rake REAL,
            stab_shim REAL,
            mast_foot_position REAL,
            FOREIGN KEY (board) REFERENCES windfoil_board(id),
            FOREIGN KEY (sail) REFERENCES windfoil_sail(id),
            FOREIGN KEY (front_foil) REFERENCES windfoil_front_foil(id),
            FOREIGN KEY (stabilizer) REFERENCES windfoil_stabilizer(id),
            FOREIGN KEY (foil_mast) REFERENCES windfoil_foil_mast(id),
            FOREIGN KEY (fuselage) REFERENCES windfoil_fuselage(id),
            FOREIGN KEY (session) REFERENCES session(id)
        )''')

        # Create table for "base de vitesse" identification
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS base_de_vitesse_identification
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            web_id INTEGER,
            name TEXT
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

    # Get all windfoil_equipment and windfoil_stabilizer where id is in windfoil_stabilizer (left join)
    def get_windfoil_stabilizer_all(self):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_equipment LEFT JOIN windfoil_stabilizer ON windfoil_equipment.id = windfoil_stabilizer.id WHERE windfoil_stabilizer.id IS NOT NULL''')
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
    def insert_windfoil_stabilizer(self, data):
        equipment_id = self.insert_windfoil_equipment(data)
        if data['id'] is None: # Add the back foil with the id of the last inserted row
            self.sqliteCursor.execute('''INSERT INTO windfoil_stabilizer (id, surface) VALUES (?, ?)''', (equipment_id, data['surface']))
            self.sqliteConnection.commit()
            return equipment_id
        else: # Update the back foil
            self.sqliteCursor.execute('''UPDATE windfoil_stabilizer SET surface = ? WHERE id = ?''', (data['surface'], data['id']))
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
    def remove_windfoil_stabilizer(self, id):
        self.remove_windfoil_equipment(id)
        self.sqliteCursor.execute('''DELETE FROM windfoil_stabilizer WHERE id = ?''', (id,))
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

    # Get all windfoil session (add statistics and rider)
    def get_windfoil_session_all_sort_start_date(self):
        self.sqliteCursor.execute('''SELECT session.*,
                                            statistics.*,
                                            rider.first_name as rider_first_name,
                                            rider.last_name as rider_last_name
                                            FROM session
                                            LEFT JOIN statistics ON session.statistics_id = statistics.id
                                            LEFT JOIN rider ON session.rider_id = rider.id
                                            ORDER BY start_date DESC''')
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
    def insert_log(self, name, starting_time, ending_time=None, type='rosbag'):
        # Test if the log file is already in the database and return the id if it is
        self.sqliteCursor.execute('''SELECT * FROM log WHERE name = ?''', (name,))
        row = self.sqliteCursor.fetchone()
        if row:
            # Return is_new, row
            return row['id'], row['is_download'], False

        type_id = self.convert_log_type_from_str(type)

        self.sqliteCursor.execute('''INSERT INTO log (name, starting_time, ending_time, type) VALUES (?, ?, ?, ?)''', (name, starting_time, ending_time, type_id))
        self.sqliteConnection.commit()
        # Return the if of the last inserted row, is_download = False, is_new = True
        return self.sqliteCursor.lastrowid, False, True

    # Return the log file by id
    def get_log(self, id):
        self.sqliteCursor.execute('''SELECT * FROM log WHERE id = ?''', (id,))
        return self.sqliteCursor.fetchone()

    def get_log_type(self, id):
        self.sqliteCursor.execute('''SELECT type FROM log WHERE id = ?''', (id,))
        return self.convert_log_type_from_int(self.sqliteCursor.fetchone()['type'])

    def is_log_gpx(self, id):
        self.sqliteCursor.execute('''SELECT type FROM log WHERE id = ?''', (id,))
        return self.sqliteCursor.fetchone()['type'] == 1

    # Test if a log has a session linked (in session_log)
    def is_log_link_to_session(self, id):
        self.sqliteCursor.execute('''SELECT * FROM session_log_link WHERE log = ?''', (id,))
        return self.sqliteCursor.fetchone() is not None

    # Remove log
    def remove_log(self, id):
        # Delete links to session
        self.sqliteCursor.execute('''DELETE FROM session_log_link WHERE log = ?''', (id,))
        # Delete links to session association
        self.sqliteCursor.execute('''DELETE FROM session_log_association WHERE log = ?''', (id,))
        # Delete log
        self.sqliteCursor.execute('''DELETE FROM log WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Get all logs downloaded add sport type (as water_sport) and rider and statistics and the id of the first session in session_log_link if it exists
    def get_all_logs(self):
        self.sqliteCursor.execute('''SELECT log.*,
                                            statistics.*,
                                            water_sport_type.name as water_sport,
                                            rider.first_name as rider_first_name,
                                            rider.last_name as rider_last_name,
                                            session_log_link.session as session
                                            FROM log
                                            LEFT JOIN water_sport_type ON log.water_sport_type = water_sport_type.id
                                            LEFT JOIN rider ON log.rider_id = rider.id
                                            LEFT JOIN statistics ON log.statistics_id = statistics.id
                                            LEFT JOIN session_log_link ON log.id = session_log_link.log''')
        return self.sqliteCursor.fetchall()

    # Get all logs which are not in session_log table and add sport type (as water_sport) and rider and statistics and the id of the first session in session_log_link if it exists
    def get_unaffected_logs(self):
        self.sqliteCursor.execute('''SELECT log.*,
                                            statistics.*,
                                            water_sport_type.name as water_sport,
                                            rider.first_name as rider_first_name,
                                            rider.last_name as rider_last_name,
                                            session_log_link.session as session
                                            FROM log
                                            LEFT JOIN water_sport_type ON log.water_sport_type = water_sport_type.id
                                            LEFT JOIN rider ON log.rider_id = rider.id
                                            LEFT JOIN statistics ON log.statistics_id = statistics.id
                                            LEFT JOIN session_log_link ON log.id = session_log_link.log
                                            WHERE session IS NULL''')
        return self.sqliteCursor.fetchall()

    # Get all logs associated with a session and add sport type (as water_sport) and rider and statistics
    def get_logs_by_session(self, session_id):
        self.sqliteCursor.execute('''SELECT log.*,
                                            statistics.*,
                                            water_sport_type.name as water_sport,
                                            rider.first_name as rider_first_name,
                                            rider.last_name as rider_last_name
                                            FROM log
                                            LEFT JOIN water_sport_type ON log.water_sport_type = water_sport_type.id
                                            LEFT JOIN rider ON log.rider_id = rider.id
                                            LEFT JOIN statistics ON log.statistics_id = statistics.id
                                            WHERE log.id IN (SELECT log FROM session_log_link WHERE session = ?)''', (session_id,))
        return self.sqliteCursor.fetchall()

    def get_logs_associated_to_session(self, session_id):
        self.sqliteCursor.execute('''SELECT log.*,
                                            statistics.*,
                                            water_sport_type.name as water_sport,
                                            rider.first_name as rider_first_name,
                                            rider.last_name as rider_last_name
                                            FROM log
                                            LEFT JOIN water_sport_type ON log.water_sport_type = water_sport_type.id
                                            LEFT JOIN rider ON log.rider_id = rider.id
                                            LEFT JOIN statistics ON log.statistics_id = statistics.id
                                            WHERE log.id IN (SELECT log FROM session_log_association WHERE session = ?)''', (session_id,))
        return self.sqliteCursor.fetchall()

    # Get starting_time of a session (older log found in session_log table)
    def get_starting_time_session(self, session_id):
        self.sqliteCursor.execute('''SELECT MIN(starting_time) as starting_time FROM log 
                                            WHERE id IN (SELECT log FROM session_log_link WHERE session = ?)''', (session_id,))
        return self.sqliteCursor.fetchone()

    # Get ending_time of a session (newer log found in session_log table)
    def get_ending_time_session(self, session_id):
        self.sqliteCursor.execute('''SELECT MAX(ending_time) as ending_time FROM log
                                            WHERE id IN (SELECT log FROM session_log_link WHERE session = ?)''', (session_id,))
        return self.sqliteCursor.fetchone()

    # Return True if the name and starting_time are not in the database or the file is not downloaded
    def is_new_log(self, name):
        self.sqliteCursor.execute('''SELECT * FROM log WHERE name = ? AND is_download = 1''', (name,))
        return self.sqliteCursor.fetchone() is None

    # Update log folder
    def set_log_download(self, id):
        self.sqliteCursor.execute('''UPDATE log SET is_download = 1 WHERE id = ?''', (id,))
        self.sqliteConnection.commit()

    # Add a link between a session and a log if it does not exist already
    def add_session_log_link(self, log_id, session_id):
        # Test if the association already exist
        self.sqliteCursor.execute('''SELECT * FROM session_log_link WHERE log = ? AND session = ?''', (log_id, session_id))
        if self.sqliteCursor.fetchone() is None:
            self.sqliteCursor.execute('''INSERT INTO session_log_link (log, session) VALUES (?, ?)''', (log_id, session_id))
            self.sqliteConnection.commit()

    # Add an association between a session and a log if it does not exist already
    def add_session_log_association(self, log_id, session_id):
        # Test if the association already exist
        self.sqliteCursor.execute('''SELECT * FROM session_log_association WHERE log = ? AND session = ?''', (log_id, session_id))
        if self.sqliteCursor.fetchone() is None:
            self.sqliteCursor.execute('''INSERT INTO session_log_association (log, session) VALUES (?, ?)''', (log_id, session_id))
            self.sqliteConnection.commit()

    # Remove an association between a session and a log
    def remove_session_log_association(self, log_id, session_id):
        self.sqliteCursor.execute('''DELETE FROM session_log_association WHERE log = ? AND session = ?''', (log_id, session_id))
        self.sqliteConnection.commit()

    # Remove a link between a session and a log
    def remove_session_log_link(self, log_id, session_id):
        self.sqliteCursor.execute('''DELETE FROM session_log_link WHERE log = ? AND session = ?''', (log_id, session_id))
        self.sqliteConnection.commit()

    # Get all log details associated to a session in session_log_association table
    def get_logs_associated_by_session(self, session_id):
        self.sqliteCursor.execute('''SELECT log.*,
                                            statistics.*,
                                            water_sport_type.name as water_sport,
                                            rider.first_name as rider_first_name,
                                            rider.last_name as rider_last_name
                                            FROM log
                                            LEFT JOIN water_sport_type ON log.water_sport_type = water_sport_type.id
                                            LEFT JOIN rider ON log.rider_id = rider.id
                                            LEFT JOIN statistics ON log.statistics_id = statistics.id
                                            WHERE log.id IN (SELECT log FROM session_log_association WHERE session = ?)''', (session_id,))
        return self.sqliteCursor.fetchall()

    # Add new seafoil_box
    def insert_seafoil_box(self, name):
        self.sqliteCursor.execute('''INSERT INTO seafoil_box_identification (name) VALUES (?)''', (name,))
        self.sqliteConnection.commit()

    # Get all seafoil_box
    def get_seafoil_box_all(self):
        self.sqliteCursor.execute('''SELECT * FROM seafoil_box_identification''')
        return self.sqliteCursor.fetchall()

    def get_seafoil_box_first(self):
        self.sqliteCursor.execute('''SELECT * FROM seafoil_box_identification LIMIT 1''')
        return self.sqliteCursor.fetchone()

    # Rename seafoil_box first
    def rename_seafoil_box_first(self, name):
        self.sqliteCursor.execute('''UPDATE seafoil_box_identification SET name = ? WHERE id = (SELECT id FROM seafoil_box_identification LIMIT 1)''', (name,))
        self.sqliteConnection.commit()

    # Get all riders order by display order and then by first name, default rider first
    def get_rider_all(self):
        self.sqliteCursor.execute('''SELECT * FROM rider ORDER BY is_default DESC, display_order, first_name''')
        return self.sqliteCursor.fetchall()

    # Get all riders order by display order and then by first name but with default rider first
    # Join with the max statistics for each rider
    def get_rider_all_with_statistics(self):
        self.sqliteCursor.execute('''SELECT rider.*,
                                            MAX(statistics.v500) as v500,
                                            MAX(statistics.v1850) as v1850,
                                            MAX(statistics.vmax) as vmax,
                                            MAX(statistics.vjibe) as vjibe,
                                            MAX(statistics.vhour) as vhour
                                            FROM rider
                                            LEFT JOIN log ON rider.id = log.rider_id
                                            LEFT JOIN statistics ON log.statistics_id = statistics.id
                                            GROUP BY rider.id
                                            ORDER BY rider.is_default DESC, rider.display_order, rider.first_name''')
        return self.sqliteCursor.fetchall()

    # Add new rider
    def add_rider(self, first_name, last_name, manual_add=False, display_order=None):
        # if display_order is not set, get the last display order and add 1
        if display_order is None:
            self.sqliteCursor.execute('''SELECT MAX(display_order) as display_order FROM rider''')
            row = self.sqliteCursor.fetchone()
            display_order = row['display_order'] + 1 if row['display_order'] is not None else 0
        self.sqliteCursor.execute('''INSERT INTO rider (first_name, last_name, manual_add, display_order) VALUES (?, ?, ?, ?)''', (first_name, last_name, manual_add, display_order))
        self.sqliteConnection.commit()
        return self.sqliteCursor.lastrowid

    # Get rider by id
    def get_rider(self, rider_id):
        self.sqliteCursor.execute('''SELECT * FROM rider WHERE id = ?''', (rider_id,))
        return self.sqliteCursor.fetchone()

    # Merge two riders
    def merge_riders(self, rider_id_keep, rider_id_remove):
        # Update all log with the rider to remove
        self.sqliteCursor.execute('''UPDATE log SET rider_id = ? WHERE rider_id = ?''', (rider_id_keep, rider_id_remove))
        # Update all session with the rider to remove
        self.sqliteCursor.execute('''UPDATE session SET rider_id = ? WHERE rider_id = ?''', (rider_id_keep, rider_id_remove))
        # Remove the rider to remove
        self.sqliteCursor.execute('''DELETE FROM rider WHERE id = ?''', (rider_id_remove,))
        self.sqliteConnection.commit()

    # Get rider of a session
    def get_session(self, session_id):
        self.sqliteCursor.execute('''SELECT * FROM session WHERE id = ?''', (session_id,))
        return self.sqliteCursor.fetchone()

    # Get session setup by session id
    def get_session_setup(self, session_id):
        self.sqliteCursor.execute('''SELECT * FROM windfoil_session_setup WHERE session = ?''', (session_id,))
        return self.sqliteCursor.fetchone()

    # Remove session and associated setup
    def remove_session(self, session_id):
        self.sqliteCursor.execute('''DELETE FROM session WHERE id = ?''', (session_id,))
        self.sqliteCursor.execute('''DELETE FROM windfoil_session_setup WHERE session = ?''', (session_id,))
        # Remove link and association
        self.sqliteCursor.execute('''DELETE FROM session_log_link WHERE session = ?''', (session_id,))
        self.sqliteCursor.execute('''DELETE FROM session_log_association WHERE session = ?''', (session_id,))
        self.sqliteConnection.commit()

    # Update session or create a new one
    def save_session(self, session):
        # If the session does not exist, create a new one
        if 'id' not in session or session['id'] is None:
            self.sqliteCursor.execute('''INSERT INTO session (start_date, end_date, rider_id, wind_mean_heading, comment) VALUES (?, ?, ?, ?, ?)''', (session['start_date'], session['end_date'], session['rider_id'], session['wind_mean_heading'], session['comment']))
            self.sqliteConnection.commit()
            return self.sqliteCursor.lastrowid
        # If the session exist, update it
        else:
            self.sqliteCursor.execute('''UPDATE session SET start_date = ?, end_date = ?, rider_id = ?, wind_mean_heading = ?, comment = ? WHERE id = ?''', (session['start_date'], session['end_date'], session['rider_id'], session['wind_mean_heading'], session['comment'], session['id']))
            self.sqliteConnection.commit()
            return session['id']

    def save_session_setup(self, session_setup):
        # If the key session_id does not exist, create a new one
        if 'id' not in session_setup or session_setup['id'] is None:
            self.sqliteCursor.execute('''INSERT INTO windfoil_session_setup (start_time, end_time, board, sail, front_foil, stabilizer, foil_mast, session, rake, stab_shim, mast_foot_position) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (session_setup['start_time'], session_setup['end_time'], session_setup['board'], session_setup['sail'], session_setup['front_foil'], session_setup['stabilizer'], session_setup['foil_mast'], session_setup['session'], session_setup['rake'], session_setup['stab_shim'], session_setup['mast_foot_position']))
            self.sqliteConnection.commit()
            return self.sqliteCursor.lastrowid
        # If the session setup exist, update it
        else:
            self.sqliteCursor.execute('''UPDATE windfoil_session_setup SET start_time = ?, end_time = ?, board = ?, sail = ?, front_foil = ?, stabilizer = ?, foil_mast = ?, session = ?, rake = ?, stab_shim = ?, mast_foot_position = ? WHERE id = ?''', (session_setup['start_time'], session_setup['end_time'], session_setup['board'], session_setup['sail'], session_setup['front_foil'], session_setup['stabilizer'], session_setup['foil_mast'], session_setup['session'], session_setup['rake'], session_setup['stab_shim'], session_setup['mast_foot_position'], session_setup['id']))
            self.sqliteConnection.commit()
            return session_setup['id']

    def add_log_statistics(self, log_id, statistics):
        print(f"Add statistics to log {log_id}")
        # Test if the log already has statistics
        self.sqliteCursor.execute('''SELECT * FROM log WHERE id = ? AND statistics_id IS NOT NULL''', (log_id,))
        if self.sqliteCursor.fetchone():
            # Update the statistics
            self.sqliteCursor.execute('''UPDATE statistics SET v500 = ?, v1850 = ?, vmax = ?, vjibe = ?, vhour = ? WHERE id = ?''', (statistics['v500'], statistics['v1850'], statistics['vmax'], statistics['vjibe'], statistics['vhour'], log_id))
            self.sqliteConnection.commit()
        else:
            # Create a new entry in the statistics table
            self.sqliteCursor.execute('''INSERT INTO statistics (v500, v1850, vmax, vjibe, vhour) VALUES (?, ?, ?, ?, ?)''', (statistics['v500'], statistics['v1850'], statistics['vmax'], statistics['vjibe'], statistics['vhour']))
            self.sqliteConnection.commit()
            # Get the id of the last inserted row
            statistics_id = self.sqliteCursor.lastrowid

            # Update the log with the statistics id
            self.sqliteCursor.execute('''UPDATE log SET statistics_id = ? WHERE id = ?''', (statistics_id, log_id))
            self.sqliteConnection.commit()

    def get_water_sport_type_all(self):
        self.sqliteCursor.execute('''SELECT * FROM water_sport_type''')
        return self.sqliteCursor.fetchall()

    def update_log_sport_type(self, log_id, sport_type_id):
        self.sqliteCursor.execute('''UPDATE log SET water_sport_type = ? WHERE id = ?''', (sport_type_id, log_id))
        self.sqliteConnection.commit()

    def update_log_rider(self, log_id, rider_id):
        self.sqliteCursor.execute('''UPDATE log SET rider_id = ? WHERE id = ?''', (rider_id, log_id))
        self.sqliteConnection.commit()

    def update_rider(self, rider_id, first_name, last_name):
        self.sqliteCursor.execute('''UPDATE rider SET first_name = ?, last_name = ? WHERE id = ?''', (first_name, last_name, rider_id))
        self.sqliteConnection.commit()

    # Find if a rider is in the database with the first and last name, remove accent and lower case
    def find_rider(self, first_name, last_name):
        first_name = first_name.lower()
        last_name = last_name.lower()
        self.sqliteCursor.execute('''SELECT * FROM rider WHERE lower(first_name) = ? AND lower(last_name) = ?''', (first_name, last_name))
        return self.sqliteCursor.fetchone()

    def find_water_sport_type(self, name):
        self.sqliteCursor.execute('''SELECT * FROM water_sport_type WHERE name = ?''', (name,))
        return self.sqliteCursor.fetchone()

    def add_water_sport_type(self, name):
        self.sqliteCursor.execute('''INSERT INTO water_sport_type (name) VALUES (?)''', (name,))
        self.sqliteConnection.commit()
        return self.sqliteCursor.lastrowid

    def update_log_time(self, log_id, starting_time, ending_time):
        self.sqliteCursor.execute('''UPDATE log SET starting_time = ?, ending_time = ? WHERE id = ?''', (starting_time, ending_time, log_id))
        self.sqliteConnection.commit()

    # Get the statistics of a session from the statistics table
    def get_session_statistics(self, session_id):
        self.sqliteCursor.execute('''SELECT * FROM statistics WHERE id = (SELECT statistics_id FROM session WHERE id = ?)''', (session_id,))
        return self.sqliteCursor.fetchone()

    # Get the maximum of statistics from the statistics logs associated with a session
    def update_session_max_score(self, session_id):
        self.sqliteCursor.execute('''SELECT MAX(v500) as v500, 
                                                 MAX(v1850) as v1850, 
                                                 MAX(vmax) as vmax, 
                                                 MAX(vjibe) as vjibe, 
                                                 MAX(vhour) as vhour 
                                                 FROM statistics 
                                                 WHERE id IN (SELECT statistics_id FROM log 
                                                 WHERE id IN (SELECT log FROM session_log_link 
                                                 WHERE session = ?))''', (session_id,))
        row = self.sqliteCursor.fetchone()
        # Update statistics of the session in the statistics table and create a new entry if it does not exist
        # Test if existing statistics
        self.sqliteCursor.execute('''SELECT * FROM statistics WHERE id = (SELECT statistics_id FROM session WHERE id = ?)''', (session_id,))
        if self.sqliteCursor.fetchone() is None:
            # Create a new entry in the statistics table
            self.sqliteCursor.execute('''INSERT INTO statistics (v500, v1850, vmax, vjibe, vhour) VALUES (?, ?, ?, ?, ?)''', (row['v500'], row['v1850'], row['vmax'], row['vjibe'], row['vhour']))
            self.sqliteConnection.commit()
            # Get the id of the last inserted row
            statistics_id = self.sqliteCursor.lastrowid
            # Update the session with the statistics id
            self.sqliteCursor.execute('''UPDATE session SET statistics_id = ? WHERE id = ?''', (statistics_id, session_id))
            self.sqliteConnection.commit()
        else:
            # Update the statistics
            self.sqliteCursor.execute('''UPDATE statistics SET v500 = ?, v1850 = ?, vmax = ?, vjibe = ?, vhour = ? 
                                                        WHERE id = (SELECT statistics_id FROM session WHERE id = ?)''',
                                      (row['v500'], row['v1850'], row['vmax'], row['vjibe'], row['vhour'], session_id))
            self.sqliteConnection.commit()
        return row

    # Add identification of a base de vitesse
    def update_base_name(self, web_id, name):
        # if it already exist, update the name
        self.sqliteCursor.execute('''SELECT * FROM base_de_vitesse_identification WHERE web_id = ?''', (web_id,))
        row = self.sqliteCursor.fetchone()
        if row:
            self.sqliteCursor.execute('''UPDATE base_de_vitesse_identification SET name = ? WHERE web_id = ?''', (name, web_id))
            self.sqliteConnection.commit()
            return row['id']
        # Add a new entry
        else:
            self.sqliteCursor.execute('''INSERT INTO base_de_vitesse_identification (web_id, name) VALUES (?, ?)''', (web_id, name))
            self.sqliteConnection.commit()
            return self.sqliteCursor.lastrowid

    # Set Default rider
    def set_default_rider(self, rider_id):
        self.sqliteCursor.execute('''UPDATE rider SET is_default = 0''')
        self.sqliteCursor.execute('''UPDATE rider SET is_default = 1 WHERE id = ?''', (rider_id,))
        self.sqliteConnection.commit()

    # Set a log to default rider if it exists
    def set_log_default_rider(self, log_id):
        self.sqliteCursor.execute('''UPDATE log SET rider_id = (SELECT id FROM rider WHERE is_default = 1) WHERE id = ?''', (log_id,))
        self.sqliteConnection.commit()



# Test the class
if __name__ == '__main__':
    db = SeafoilDB()

    db.insert_windfoil_fuselage({'manufacturer': 'AFS', 'model': '', 'year': 2021, 'comment': '', 'length': 0.95, 'id': None})

    db.insert_windfoil_fuselage({'manufacturer': 'AFS', 'model': '', 'year': 2021, 'comment': '', 'length': 0.6, 'id': 1})




