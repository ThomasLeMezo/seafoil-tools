import paramiko
import datetime
import os
from scp import SCPClient
import yaml

class SeafoilConnexion:

    def __init__(self, host='seafoil'):
        self.host = host + ".local" # use the avahi service to find the host
        self.username = 'pi'
        self.service_name = 'seafoil.service'
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.is_connected = False
        # project folder is one level above the current file
        self.projet_folder = os.path.dirname(os.path.abspath(__file__)) + '/../'
        self.log_folder = self.projet_folder + '/data/log/'

        self.stored_log_list = []

    def __del__(self):
        # if connected, close the connection
        if self.is_connected and self.ssh_client.get_transport().is_active():
            self.ssh_client.close()

    def check_if_connected(self):
        if not self.is_connected or not self.ssh_client.get_transport().is_active():
            print("Not connected to the server.")
            self.is_connected = False
            return False
        return True

    def connect(self):
        try:
            if not self.is_connected or not self.ssh_client.get_transport().is_active():
                self.ssh_client.connect(self.host, username=self.username, auth_timeout=5, banner_timeout=5)
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
            command = f"sudo systemctl stop {self.service_name}"

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
        try:
            # Command to start the service
            command = f"sudo systemctl start {self.service_name}"

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
        if not self.check_if_connected():
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

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        # Remove the temporary file
        os.remove(config_file)

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
                self.stored_log_list.append({'name': name, 'timestamp': timestamp, 'id': i})

            return self.stored_log_list

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    # Download a log folder from the seafoil to data/log folder
    def seafoil_download_log(self, log_id):
        # Test if the log_id is valid
        if log_id < 0 or log_id >= len(self.stored_log_list):
            print("Invalid log id.")
            return False

        # get the log name from the stored list
        log_name = self.stored_log_list[log_id]['name']
        log_date = self.stored_log_list[log_id]['timestamp']


        # Create the log folder if it does not exist
        os.makedirs(f"{self.log_folder}", exist_ok=True)

        # Create if not exists a folder for year and month
        year = log_date.year
        month = log_date.month
        os.makedirs(f"{self.log_folder}/{year}", exist_ok=True)
        os.makedirs(f"{self.log_folder}/{year}/{month}", exist_ok=True)

        # Test if log folder already exists
        if os.path.exists(f"{self.log_folder}/{year}/{month}/{log_name}"):
            print("The log folder already exists.")
            return False

        try:
            def progress(filename, size, sent):
                print("%s's progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )

            # Create an SCP client
            with SCPClient(self.ssh_client.get_transport(), progress=progress) as scp:
                # Download the file
                scp.get(f"/home/{self.username}/log/{log_name}", f"{self.log_folder}/{year}/{month}/", recursive=True, preserve_times=True)
                print("Download complete!")


            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

if __name__ == '__main__':
    sc = SeafoilConnexion()
    print(sc.seafoil_service_stop())
    print(sc.seafoil_get_log_list())
    sc.seafoil_download_log(0)