import gpxpy
import paramiko
import datetime
import os

from PyQt5.QtCore import pyqtSignal, QObject
from scp import SCPClient
import yaml
from db.seafoil_db import SeafoilDB
from enum import IntEnum
import re

def correction_of_malformed_gpx(gpx_file_content):
    # remplace balise of the form *:* by *_* in the gpx file (only with letters around)
    gpx_file_content = re.sub(r'([a-zA-Z]):([a-zA-Z])', r'\1_\2', gpx_file_content)

    return gpx_file_content



class StateConnexion(IntEnum):
    Disconnected = 0
    SeafoilServiceStop = 1
    DownloadLogList = 2
    DownloadLog = 3
    ProcessLog = 4
    Error = 4

class SeafoilConnexion(QObject):
    # Create signal for progress bar
    signal_download_log = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.db = SeafoilDB()

        self.seafoil_box = self.db.get_seafoil_box_all()

        if len(self.seafoil_box) == 0:
            self.host = "seafoil"
        else:
            self.host = self.seafoil_box[0]["name"]
        self.host += ".local" # use the avahi service to find the host

        # Default parameters
        self.username = 'pi'
        self.service_name = 'seafoil.service'
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.is_connected = False

        # project folder is one level above the current file (and simplify the path)
        self.projet_folder = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../')
        self.log_folder = self.projet_folder + '/data/log/'

        self.stored_log_list = []

        self.connexion_state = StateConnexion.Disconnected

        self.remaining_log_to_download = 0

    def __del__(self):
        # if connected, close the connection
        if self.is_connected and self.ssh_client.get_transport().is_active():
            self.ssh_client.close()

    def get_file_directory(self, id, file_name):
        ret = self.log_folder + str(id) + '/' + file_name
        # if file name is a gpx file
        if not file_name.endswith('.gpx'):
            ret += "/"
        return ret

    def check_if_connected(self):
        if not self.is_connected or not self.ssh_client.get_transport().is_active():
            print("Not connected to the server.")
            self.is_connected = False
            return False
        return True

    def connect(self):
        try:
            if not self.is_connected or not self.ssh_client.get_transport().is_active():
                self.ssh_client.connect(self.host, username=self.username, auth_timeout=2, banner_timeout=2)
                print(f"Connected to the server {self.host} as {self.username}.")
                self.is_connected = True
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def disconnect(self):
        try:
            if self.is_connected and self.ssh_client.get_transport().is_active():
                self.ssh_client.close()
                print(f"Disconnected from the server {self.host}.")
                self.is_connected = False
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def seafoil_service_stop(self):
        try:
            # Command to stop the service
            command = f"systemctl stop {self.service_name}"

            # Execute the command
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            # Read the output
            output = stdout.read().decode().strip()

            # Determine if the service was stopped
            if output == '':
                print(f"The service '{self.service_name}' was stopped.")
                return True
            else:
                print(f"An error occurred: {output}")
                return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def seafoil_service_start(self):
        if not self.connect():
            return False

        try:
            # Command to start the service
            command = f"systemctl start {self.service_name}"

            # Execute the command
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            # Read the output
            output = stdout.read().decode().strip()

            # Determine if the service was started
            if output == '':
                print(f"The service '{self.service_name}' was started.")
                return True
            else:
                print(f"An error occurred: {output}")
                return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def seafoil_service_status(self):
        try:

            # Command to check the service status
            command = f"systemctl is-active {self.service_name}"

            # Execute the command
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            # Read the output
            status = stdout.read().decode().strip()

            # Determine if the service is running
            if status == 'active':
                print(f"The service '{self.service_name}' is running.")
                return True
            else:
                print(f"The service '{self.service_name}' is not running.")
                return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    # Send a yaml configuration file to the seafoil box
    def seafoil_send_config(self, file_name, yaml_data):
        # Test if connected
        if not self.connect():
            return False

        # Create temporary yaml file (test if directory exists)
        os.makedirs(f"{self.projet_folder}/data/", exist_ok=True)
        config_file = f"{self.projet_folder}/data/tmp.yaml"
        with open(config_file, 'w') as file:
            yaml.dump(yaml_data, file)

        # Stop the service
        if not self.seafoil_service_stop():
            return False

        try:
            # Send the file
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.put(config_file, f"/home/{self.username}/config/default/" + file_name)
                print("File sent successfully.")

            # Remove .bkp files
            command = f"rm /home/{self.username}/config/default/*.bkp"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)


        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        # Remove the temporary file
        os.remove(config_file)
        return True

    # Read a yaml configuration file from the seafoil box
    def seafoil_read_config(self, file_name):
        # Create temporary yaml file (test if directory exists)
        os.makedirs(f"{self.projet_folder}/data/", exist_ok=True)
        config_file = f"{self.projet_folder}/data/tmp.yaml"
        # Errase file if it exists
        if os.path.exists(config_file):
            os.remove(config_file)

        try:
            # Get the file
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(f"/home/{self.username}/config/default/" + file_name, config_file)
                print("File received successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        # Read the file
        yaml_data = None
        try:
            with open(config_file, 'r') as file:
                yaml_data = yaml.load(file, Loader=yaml.FullLoader)

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        # Remove the temporary file
        os.remove(config_file)

        return yaml_data

    # Get the list of folder in the seafoil home/log directory
    def seafoil_get_log_list(self):
        try:
            # Command to list the log folder sort by time with complete date and name and size of folder content
            command = f"ls -lt --time-style=full-iso /home/{self.username}/log | grep ^d | awk '{{print $6, $7, $8, $9}}'"

            # Execute the command and get the output
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode().strip()

            # Add each entry to a dict with the name, date, and an id (enumeration)
            self.stored_log_list = []
            for i, line in enumerate(output.split('\n')):
                date, time, _, name = line.split(' ')
                # convert date and time as datetime object
                timestamp = datetime.datetime.strptime((date + ' ' + time)[:23], '%Y-%m-%d %H:%M:%S.%f')
                timestamp_ros =  datetime.datetime.strptime(name, 'rosbag2_%Y_%m_%d-%H_%M_%S')
                is_new_log = self.db.is_new_log(name)
                self.stored_log_list.append({'name': name, 'timestamp': timestamp, 'timestamp_ros': timestamp_ros, 'id': i, 'is_new': is_new_log})

            return self.stored_log_list

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def seafoil_delete_logs(self, log_list):
        success = True
        for log_id in log_list:
            if not self.seafoil_delete_log(log_id):
                success = False

        # Update the log list
        self.seafoil_get_log_list()

        return success

    def seafoil_delete_log(self, log_id):
        # Test if the log_id is valid
        if log_id < 0 or log_id >= len(self.stored_log_list):
            print("Invalid log id.")
            return False

        # get the log name from the stored list
        log_name = self.stored_log_list[log_id]['name']

        try:
            # Command to delete the log folder
            command = f"rm -r /home/{self.username}/log/{log_name}"

            # Execute the command
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            # Read the output
            output = stdout.read().decode().strip()

            # Determine if the folder was deleted
            if output == '':
                print(f"The log folder '{log_name}' was deleted.")
                return True
            else:
                print(f"An error occurred: {output}")
                return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def seafoil_download_logs(self, log_list):
        log_added = []
        success = True
        self.remaining_log_to_download = len(log_list)
        for log_id in log_list:
            ret, db_id = self.seafoil_download_log(log_id)
            if db_id is not None:
                log_added.append(db_id)
            success &= ret
            self.remaining_log_to_download -= 1

        # Update the log list
        self.seafoil_get_log_list()

        return success, log_added

    # Download a log folder from the seafoil to data/log folder
    def seafoil_download_log(self, log_id):
        # Test if the log_id is valid
        if log_id < 0 or log_id >= len(self.stored_log_list):
            print("Invalid log id.")
            return False, -1

        # get the log name from the stored list
        log_name = self.stored_log_list[log_id]['name']
        log_date = self.stored_log_list[log_id]['timestamp_ros'].timestamp()

        # Create the log folder if it does not exist
        os.makedirs(f"{self.log_folder}", exist_ok=True)

        # Create new rosbag in db
        db_id, is_downloaded, is_new = self.db.insert_log(log_name, log_date, type='rosbag')

        self.db.set_log_default_rider(db_id)

        # If the rosbag already exists, verify if the log folder already exists
        if not is_new and is_downloaded:
            print("The log folder already exists in the database.")
            return False, db_id

        download_target = f"{self.log_folder}/{db_id}"
        os.makedirs(download_target, exist_ok=True)

        try:
            def progress(filename, size, sent):
                # print("%s's progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )
                # Emit the signal
                self.signal_download_log.emit(int(float(sent)/float(size)*100), self.remaining_log_to_download)

            # Create an SCP client
            with SCPClient(self.ssh_client.get_transport(), progress=progress) as scp:
                # Download the file
                scp.get(f"/home/{self.username}/log/{log_name}", f"{download_target}/", recursive=True, preserve_times=True)
                print("Download complete!")

            # Update the db
            self.db.set_log_download(db_id)

            return True,db_id

        except Exception as e:
            print(f"An error occurred: {e}")
            # Remove the folder if the download failed, if not exists, it will not do anything
            os.system(f"rm -r {download_target}")
            # Remove the log from the database
            self.db.remove_log(db_id)
            print(f"Download failed {log_name}! Remove the log from the database.")
            return False, None

    def import_seafoil_log(self, dir_path):
        # Get the name of the last directory of the path
        name = os.path.basename(dir_path)
        timestamp_ros = None
        try:
            timestamp_ros =  datetime.datetime.strptime(name, 'rosbag2_%Y_%m_%d-%H_%M_%S').timestamp()
        except ValueError:
            print(f"Invalid directory name: {name}")
            return False, None

        # Create the log folder if it does not exist
        os.makedirs(f"{self.log_folder}", exist_ok=True)

        # Create new rosbag in db
        db_id, is_downloaded, is_new = self.db.insert_log(name, timestamp_ros, type='rosbag')

        self.db.set_log_default_rider(db_id)

        # If the rosbag already exists, verify if the log folder already exists
        if not is_new and is_downloaded:
            print("The log folder already exists in the database.")
            return False, db_id

        download_target = f"{self.log_folder}/{db_id}"
        os.makedirs(download_target, exist_ok=True)

        # Copy the directory
        try:
            os.system(f"cp -r {dir_path} {download_target}")
            print(f"The log folder {name} was added successfully.")

            # Update the db
            self.db.set_log_download(db_id)

            return True, db_id
        except Exception as e:
            print(f"An error occurred: {e}")
            # Remove the folder if the download failed, if not exists, it will not do anything
            os.system(f"rm -r {download_target}")
            # Remove the log from the database
            self.db.remove_log(db_id)
            print(f"Add log failed {name}! Remove the log from the database.")
            return False, None

    def download_gpx_file(self, url):
        # Use requests to download the file
        # Test if the url ends with ".gpx"
        if not url.endswith('.gpx'):
            print("The url is not a gpx file : ", url)
            return False, None

        try:
            import requests
            response = requests.get(url)
            if response.status_code == 200:
                # Create the log folder if it does not exist
                os.makedirs(f"{self.log_folder}", exist_ok=True)

                # Get the file name from the url
                file_name = url.split('/')[-1]

                # Create new gpx in db
                db_id, is_downloaded, is_new = self.db.insert_log(file_name, None, type='gpx')

                # If the gpx already exists, verify if the log folder already exists
                if not is_new and is_downloaded:
                    print("The GPX file already exists in the database.")
                    return False, db_id

                download_target = f"{self.log_folder}/{db_id}"
                os.makedirs(download_target, exist_ok=True)

                # Save the file
                with open(f"{download_target}/{file_name}", 'wb') as file:
                    file.write(response.content)

                # Update the db
                self.db.set_log_download(db_id)

                # Update starting and ending time
                try:
                    # Load the gpx file
                    f = open(f"{download_target}/{file_name}", 'r')
                    gpx = gpxpy.parse(correction_of_malformed_gpx(f.read()))

                    # Get the starting time of the gpx file in timestamp format
                    starting_time = gpx.tracks[0].segments[0].points[0].time.timestamp()
                    ending_time = gpx.tracks[0].segments[0].points[-1].time.timestamp()

                    self.db.update_log_time(db_id, starting_time, ending_time)
                except Exception as e:
                    print(f"An error occurred while updating the time: {e}")
                    # Remove the log from the database and the folder
                    self.db.remove_log(db_id)
                    os.system(f"rm -r {download_target}")
                    return False, None

                print(f"The GPX file {file_name} was added successfully.")
                return True, db_id

            else:
                print(f"An error occurred while downloading the GPX file: {response.status_code}")
                return False, None
        except Exception as e:
            print(f"An error occurred while downloading the GPX file: {e}")
            return False, None

    def add_gpx_file(self, file_path):
        # Try to parse the file
        file_name = ''
        try:
            gpx_file = open(file_path, 'r')
            gpx = gpxpy.parse(correction_of_malformed_gpx(gpx_file.read()))

            # Get the starting time of the gpx file in timestamp format
            starting_time = gpx.tracks[0].segments[0].points[0].time.timestamp()
            ending_time = gpx.tracks[0].segments[0].points[-1].time.timestamp()

            # Insert the gpx file in the database
            file_name = os.path.basename(file_path)
            db_id, is_download, is_new = self.db.insert_log(os.path.basename(file_name), starting_time, ending_time, 'gpx')
            folder = self.log_folder + str(db_id) + '/'
            os.makedirs(folder, exist_ok=True)

            self.db.set_log_default_rider(db_id)

            db_file_path = folder + file_name

            if not is_new and is_download:
                # Open dialog error
                print(f'This GPX file {file_name} already exists in the database.')
                return False, db_id
            else:
                # Create folder if it does not exist
                os.system('cp ' + file_path + ' ' + db_file_path)
                # Add path to the db
                self.db.set_log_download(db_id)
                print(f'The GPX file {file_name} was added successfully.')
                return True, db_id

        except Exception as e:
            print(f'An error occurred while importing the GPX file {file_name}: {e}')
            return False, None

    def remove_log(self, db_id):
        # Get the log name from the database
        log = self.db.get_log(db_id)
        log_name = log['name']

        # Remove the log from the database
        self.db.remove_log(db_id)

        # Remove the log folder
        os.system(f"rm -r {self.log_folder}/{db_id}")

        print(f"The log '{log_name}' was removed.")

    def process_connexion(self):
        if self.connexion_state == StateConnexion.Disconnected:
            if self.connect():
                self.connexion_state = StateConnexion.SeafoilServiceStop

        elif self.connexion_state == StateConnexion.SeafoilServiceStop:
            if self.seafoil_service_stop():
                self.connexion_state = StateConnexion.DownloadLogList
            else:
                self.connexion_state = StateConnexion.Disconnected

        elif self.connexion_state == StateConnexion.DownloadLogList:
            if self.seafoil_get_log_list():
                self.connexion_state = StateConnexion.DownloadLog
            else:
                self.connexion_state = StateConnexion.Disconnected

if __name__ == '__main__':
    sc = SeafoilConnexion()
    print(sc.seafoil_service_stop())
    print(sc.seafoil_get_log_list())
    sc.seafoil_download_log(0)