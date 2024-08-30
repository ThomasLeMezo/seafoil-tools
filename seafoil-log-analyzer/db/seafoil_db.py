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
            time_start DATETIME DEFAULT 0,
            time_end DATETIME DEFAULT 0,
            rider_id INTEGER,
            wind_mean_heading REAL,
            FOREIGN KEY (rider_id) REFERENCES rider(id)
        )''')

        # Create table for rosbag
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS rosbag
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            time_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            rosbag_name TEXT,
            folder TEXT,
            session INTEGER,
            FOREIGN KEY (session) REFERENCES session(id)
        )''')

        # Create table for gpx
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS gpx
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            time_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_start DATETIME DEFAULT 0,
            gpx_name TEXT NOT NULL,
            folder TEXT NOT NULL,
            session INTEGER,
            FOREIGN KEY (session) REFERENCES session(id)
        )''')

        # Create table for windfoil board
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_board
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            manufacturer TEXT,
            model TEXT,
            length REAL,
            width REAL,
            volume REAL,
            year INTEGER,
            comment TEXT
        )''')

        # Create table for windfoil sail
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_sail
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            manufacturer TEXT,
            model TEXT,
            size REAL,
            year INTEGER,
            comment TEXT
        )''')

        # Create table for windfoil front foil
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_front_foil
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            manufacturer TEXT,
            model TEXT,
            surface REAL,
            year INTEGER,
            comment TEXT
        )''')

        # Create table for windfoil back foil
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_back_foil
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            manufacturer TEXT,
            model TEXT,
            surface REAL,
            year INTEGER,
            comment TEXT
        )''')

        # Create table for windfoil foil mast
        self.sqliteCursor.execute('''CREATE TABLE IF NOT EXISTS windfoil_foil_mast
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            manufacturer TEXT,
            model TEXT,
            length REAL,
            year INTEGER,
            comment TEXT
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

    # Add new gpx file to the database if it does not exist
    def insert_gpx(self, gpx_name, folder, time_start):
        # Test if the gpx file is already in the database and return the id if it is
        self.sqliteCursor.execute('''SELECT id FROM gpx WHERE gpx_name = ?''', (gpx_name,))
        row = self.sqliteCursor.fetchone()
        if row:
            return row['id'], True

        self.sqliteCursor.execute('''INSERT INTO gpx (gpx_name, folder, time_start) VALUES (?, ?, ?)''', (gpx_name, folder, time_start))
        self.sqliteConnection.commit()

        # return the id of the last inserted row
        return self.sqliteCursor.lastrowid, False

    # Set configuration for a seafoil box
    def set_configuration(self, name, v500, v1850, heading_enable, voice_interval, height_too_high, height_high, min_speed_sound, id_config=None):
        if id_config is not None:
            print(f"Update configuration {id_config}")
            self.sqliteCursor.execute('''UPDATE seafoil_box_configuration SET name = ?, v500 = ?, v1850 = ?, heading_enable = ?, voice_interval = ?, height_too_high = ?, height_high = ?, min_speed_sound = ? WHERE id = ?''', (name, v500, v1850, heading_enable, voice_interval, height_too_high, height_high, min_speed_sound, id_config))
        else:
            print(f"Save configuration {name}")
            self.sqliteCursor.execute('''INSERT INTO seafoil_box_configuration (name, v500, v1850, heading_enable, voice_interval, height_too_high, height_high, min_speed_sound) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (name, v500, v1850, heading_enable, voice_interval, height_too_high, height_high, min_speed_sound))
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

# Test the class
if __name__ == '__main__':
    db = SeafoilDB()




