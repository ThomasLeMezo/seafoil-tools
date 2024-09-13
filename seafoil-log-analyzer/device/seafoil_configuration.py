import subprocess, os
from db.seafoil_db import SeafoilDB
import yaml
from device.seafoil_connexion import SeafoilConnexion

# class to manage the yaml configuration file of the seafoil box
class SeafoilConfiguration():
    def __init__(self):
        self.configuration_list = None
        self.current_index = None
        self.config_file_name = 'observer.yaml'
        self.sc = SeafoilConnexion()
        self.db = SeafoilDB()

        self.seafoil_box_name = self.db.get_seafoil_box_first()

        self.v500 = 30.0
        self.v1850 = 30.0
        self.voice_interval = 5000
        self.heading_enable = False
        self.height_high = 0.5
        self.height_too_high = 0.8
        self.min_speed_sound = 8.0
        self.wind_heading = 0

        self.yaml_observer = None
        self.yaml_observer_path = self.config_file_name
        self.load_ros2_seafoil_config_yaml('observer.yaml')

        self.db_get_configuration_list()

    # Get the path of the configuration file in ros2 environment
    def load_ros2_seafoil_config_yaml(self, file_name):
        # Determine user name
        user = os.getlogin()
        command = f"source /home/{user}/.zshrc && ros2 pkg prefix seafoil"
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/zsh')
        output = result.stdout.decode('utf-8').strip()
        path = output + '/share/seafoil/config/default/' + file_name
        # Test if the file exists
        if not os.path.exists(path):
            return None
        else:
            self.yaml_observer_path = path
            # Load yaml
            with open(self.yaml_observer_path, 'r') as file:
                self.yaml_observer = yaml.load(file, Loader=yaml.FullLoader)

    def update_yaml(self):
        self.yaml_observer['observer']['voice_text']['ros__parameters']['mean_target_velocity_v500'] = self.v500
        self.yaml_observer['observer']['voice_text']['ros__parameters']['mean_target_velocity_v1850'] = self.v1850
        self.yaml_observer['observer']['voice_text']['ros__parameters']['loop_dt'] = self.voice_interval
        self.yaml_observer['observer']['voice_text']['ros__parameters']['gnss_cog_enable_voice'] = self.heading_enable
        self.yaml_observer['observer']['voice_text']['ros__parameters']['wind_heading'] = self.wind_heading
        self.yaml_observer['observer']['height_audio']['ros__parameters']['height_high'] = self.height_high
        self.yaml_observer['observer']['height_audio']['ros__parameters']['height_too_high'] = self.height_too_high
        self.yaml_observer['observer']['height_audio']['ros__parameters']['minimum_speed'] = self.min_speed_sound

    def upload_configuration(self):
        self.update_yaml()
        return self.sc.seafoil_send_config(self.config_file_name, self.yaml_observer)

    def update_index(self, index):
        if self.current_index != index:
            if index < len(self.configuration_list):
                self.current_index = index
                self.db_load_configuration(index)
                return True
        return False

    def db_load_configuration(self, index):
        if index is not None and 0 <= index < len(self.configuration_list):
            data = self.db.get_configuration_by_id(self.configuration_list[index]['id'])
            if data is None:
                return
            self.v500 = data['v500']
            self.v1850 = data['v1850']
            self.voice_interval = data['voice_interval']
            self.heading_enable = data['heading_enable']
            self.height_high = data['height_high']
            self.height_too_high = data['height_too_high']
            self.min_speed_sound = data['min_speed_sound']

    def db_save_configuration(self, name=None, is_new=False):
        if is_new==False and self.current_index < 0:
            return
        id_config = None
        if not is_new:
            id_config = self.configuration_list[self.current_index]['id']
            name = self.configuration_list[self.current_index]['name']

        # build a map
        data = {'name': name,
                'v500': self.v500,
                'v1850': self.v1850,
                'heading_enable': self.heading_enable,
                'voice_interval': self.voice_interval,
                'height_high': self.height_high,
                'height_too_high': self.height_too_high,
                'min_speed_sound': self.min_speed_sound,
                'id': id_config}

        self.db.set_configuration(data)
        self.db_get_configuration_list()


    def db_get_configuration_list(self):
        self.configuration_list = self.db.get_configuration_all()
        if self.current_index is None:
            self.current_index = min(len(self.configuration_list) -1, 0)
        self.db_load_configuration(self.current_index)


    def db_remove_configuration(self):
        if 0 <= self.current_index < len(self.configuration_list):
            self.db.remove_configuration(self.configuration_list[self.current_index]['id'])
            self.current_index = None
            self.db_get_configuration_list()