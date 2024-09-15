
import numpy as np
import os

from scipy.interpolate import interpolate


class SeafoilStatistics:
    def __init__(self, seafoil_bag):

        self.sfb = seafoil_bag
        self.time = None
        self.speed_v500 = None
        self.speed_v1852 = None
        self.max_v500 = None
        self.max_v1852 = None
        self.max_speed = None
        self.roll_2s = None
        self.pitch_2s = None
        self.height_2s = None

        self.file_save = self.sfb.data_folder + "/statistics.npz"

        self.open_statistics()

    def open_statistics(self):
        try:
            data = np.load(self.file_save)
            self.speed_v500 = data['speed_v500']
            self.speed_v1852 = data['speed_v1852']
            self.time = data['time']
            if 'height_2s' in data.files:
                self.height_2s = data['height_2s']
            if 'roll_2s' in data.files:
                self.roll_2s = data['roll_2s']
            if 'pitch_2s' in data.files:
                self.pitch_2s = data['pitch_2s']
            data.close()
        except:
            self.speed_v500 = self.compute_speed_for_distance(self.sfb.distance, 500)
            self.speed_v1852 = self.compute_speed_for_distance(self.sfb.distance, 1852)
            self.time = self.sfb.distance.time

            # Interpolate roll, pitch and height to match the gps fix data
            # interpolate data_height to data_gnss.time_gnss
            if not self.sfb.height.is_empty():
                height_filter = np.convolve(self.sfb.height.height, np.ones(2) / 2, mode='same')

                f_height = interpolate.interp1d(self.sfb.height.time, height_filter, bounds_error=False, kind="zero")
                self.height_2s = f_height(self.time)

            if not self.sfb.rpy.is_empty():
                # convolve roll and pitch with a 2s filter
                roll_filter = np.convolve(self.sfb.rpy.roll, np.ones(2) / 2, mode='same')
                pitch_filter = np.convolve(self.sfb.rpy.pitch, np.ones(2) / 2, mode='same')

                f_roll = interpolate.interp1d(self.sfb.rpy.time, roll_filter, bounds_error=False, kind="zero")
                self.roll_2s = f_roll(self.time)

                f_pitch = interpolate.interp1d(self.sfb.rpy.time, pitch_filter, bounds_error=False, kind="zero")
                self.pitch_2s = f_pitch(self.time)

            self.save_statistics()

        # Compute the max speed
        self.max_v500 = np.max(self.speed_v500)
        self.max_v1852 = np.max(self.speed_v1852)
        self.max_speed = max(self.sfb.gps_fix.speed)

    def save_statistics(self):
        # If folder does not exist, create it
        if not os.path.exists(os.path.dirname(self.file_save)):
            os.makedirs(os.path.dirname(self.file_save))

        np.savez(self.file_save, speed_v500=self.speed_v500,
                                 speed_v1852=self.speed_v1852,
                                 time=self.time,
                                 height_2s=self.height_2s,
                                 roll_2s=self.roll_2s,
                                 pitch_2s=self.pitch_2s)

    def compute_speed_for_distance(self, data_distance, distance):
        speed_distance = None
        if not data_distance.is_empty():
            # Compute the speed for 500 m
            speed_distance = np.zeros(len(data_distance.distance))
            d0_idx_last = 0
            for d1_idx in range(1, len(data_distance.distance)):
                d1 = data_distance.distance[d1_idx]
                d0 = data_distance.distance[d0_idx_last]
                if (d1 - d0) >= distance:
                    for d0_idx in range(d0_idx_last, d1_idx):
                        d0 = data_distance.distance[d0_idx]
                        if d1 - d0 <= distance:
                            dt = data_distance.time[d1_idx] - data_distance.time[d0_idx]
                            if dt > 0:
                                speed_distance[d1_idx] = (d1 - d0) / dt
                            else:
                                speed_distance[d1_idx] = 0
                            d0_idx_last = max(0, d0_idx - 1)
                            break
        return speed_distance


    def get_starting_index_for_distance_from_last_point(self, data_distance, distance, ending_idx):
        starting_idx = 0
        d1 = data_distance.distance[ending_idx]
        for d0_idx in range(ending_idx, 0, -1):
            d0 = data_distance.distance[d0_idx]
            if d1 - d0 >= distance:
                return d0_idx
        return starting_idx