#!/bin/python3
import os
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
from .seafoil_dock import SeafoilDock
import numpy as np
from scipy import signal, interpolate
import copy
import pyqtgraph.opengl as gl


class DockData(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Raw Data")
        self.add_profile()
        # self.add_profile2()
        # self.add_profile_one()
        self.add_imu()
        self.add_imu_calibrated()
        self.add_corr_acc()
        self.add_euler()
        self.add_magnetic_3Dplot()
        self.add_ahrs_error_acc()
        self.add_ahrs_error_mag()
        self.add_battery()
        self.add_wind()
        self.add_wind_info()
        self.add_wind_debug()

        print("DockData initialized")

    def add_profile(self):
        dock_profile = Dock("Profile (default)")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.profile)

        if not data.is_empty():
            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(1, 0, 1, 1, title="interactive")
            p2.addItem(i2, title='')
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle(showValues=False)
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values=(0, 255),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits=(0, None),
                rounding=1,
                orientation='h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem(i2, insert_in=p2)
            dock_profile.addWidget(pg_profile)

    def add_profile2(self):
        dock_profile = Dock("Profile (zero)")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.profile)

        if not data.is_empty():

            # compute the mean of the first 10 profiles
            mean_profile = np.mean(data.profile[0:10, :], axis=0)
            # subtract the mean from all profiles
            data.profile = data.profile - mean_profile
            # for each profile, normalize the maximum to 255
            for i in range(data.nb_elements):
                data.profile[i, :] = data.profile[i, :] / np.max(data.profile[i, :]) * 255

            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(1, 0, 1, 1, title="interactive")
            p2.addItem(i2, title='')
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle(showValues=True)
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values=(0, 255),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits=(0, None),
                rounding=1,
                orientation='h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem(i2, insert_in=p2)
            dock_profile.addWidget(pg_profile)

    def add_profile_one(self):
        dock_profile_one = Dock("Profile analysis")
        self.addDock(dock_profile_one, position='below')
        data = self.sfb.profile
        i = 10

        if not data.is_empty():
            pg_profile = pg.PlotWidget()
            pg_profile.plot(np.arange(128), data.profile[i, :-1], pen=(255, 0, 0), name="signal", stepMode=True)
            pg_profile.setLabel('left', "status")
            dock_profile_one.addWidget(pg_profile)

    def add_battery(self):
        dock_battery = Dock("Battery")
        self.addDock(dock_battery, position='below')
        data = self.sfb.battery

        if not data.is_empty():
            pg_voltage = pg.PlotWidget()
            self.set_plot_options(pg_voltage)
            pg_voltage.plot(data.time, data.voltage, pen=(255, 0, 0), name="voltage")
            pg_voltage.setLabel('left', "voltage")
            dock_battery.addWidget(pg_voltage)

            pg_state_of_charge = pg.PlotWidget()
            self.set_plot_options(pg_state_of_charge)
            pg_state_of_charge.plot(data.time, data.state_of_charge, pen=(0, 255, 0), name="state_of_charge")
            pg_state_of_charge.setLabel('left', "state_of_charge")
            dock_battery.addWidget(pg_state_of_charge)
            pg_state_of_charge.setXLink(pg_voltage)

            pg_average_current = pg.PlotWidget()
            self.set_plot_options(pg_average_current)
            pg_average_current.plot(data.time, data.average_current, pen=(0, 0, 255), name="average_current")
            pg_average_current.setLabel('left', "average_current")
            dock_battery.addWidget(pg_average_current)
            pg_average_current.setXLink(pg_voltage)


    def add_imu(self):
        dock_imu = Dock("IMU RAW")
        self.addDock(dock_imu, position='below')
        data = self.sfb.raw_data
        data_debug = self.sfb.debug_fusion
        pg_acceleration = None

        if not data.is_empty():
            pg_acceleration = pg.PlotWidget()
            self.set_plot_options(pg_acceleration)
            pg_acceleration.plot(data.time, data.accel_x, pen=(255, 0, 0), name="x")
            pg_acceleration.plot(data.time, data.accel_y, pen=(0, 255, 0), name="y")
            pg_acceleration.plot(data.time, data.accel_z, pen=(0, 0, 255), name="z")
            pg_acceleration.plot(data.time, np.sqrt(data.accel_x ** 2 + data.accel_y ** 2 + data.accel_z ** 2),
                                 pen=(255, 255, 255), name="norm")
            pg_acceleration.setLabel('left', "acceleration")
            dock_imu.addWidget(pg_acceleration)

            pg_gyro = pg.PlotWidget()
            self.set_plot_options(pg_gyro)
            pg_gyro.plot(data.time, data.gyro_x, pen=(255, 0, 0), name="x")
            pg_gyro.plot(data.time, data.gyro_y, pen=(0, 255, 0), name="y")
            pg_gyro.plot(data.time, data.gyro_z, pen=(0, 0, 255), name="z")
            pg_gyro.setLabel('left', "gyro")
            dock_imu.addWidget(pg_gyro)
            pg_gyro.setXLink(pg_acceleration)

            pg_mag = pg.PlotWidget()
            self.set_plot_options(pg_mag)
            pg_mag.plot(data.time, data.mag_x, pen=(255, 0, 0), name="x")
            pg_mag.plot(data.time, data.mag_y, pen=(0, 255, 0), name="y")
            pg_mag.plot(data.time, data.mag_z, pen=(0, 0, 255), name="z")
            pg_mag.plot(data.time, np.sqrt(data.mag_x ** 2 + data.mag_y ** 2 + data.mag_z ** 2), pen=(255, 255, 255),
                        name="norm")
            pg_mag.setLabel('left', "mag")
            dock_imu.addWidget(pg_mag)
            pg_mag.setXLink(pg_acceleration)

            pg_temp = pg.PlotWidget()
            self.set_plot_options(pg_temp)
            pg_temp.plot(data.time, data.temp, pen=(255, 0, 0), name="temperature")
            pg_temp.setLabel('left', "temperature")
            dock_imu.addWidget(pg_temp)
            pg_temp.setXLink(pg_acceleration)

        if not data_debug.is_empty():
            pg_debug = pg.PlotWidget()
            self.set_plot_options(pg_debug)
            pg_debug.plot(data_debug.time, data_debug.magnetometer_limit_reached, pen=(255, 0, 0), name="limit_reached")
            pg_debug.plot(data_debug.time, data_debug.magnetometer_data_skipped, pen=(0, 255, 0), name="data_skipped")
            pg_debug.plot(data_debug.time, data_debug.magnetometer_data_is_ready, pen=(0, 0, 255), name="data_is_ready")
            pg_debug.setLabel('left', "magnetometer status")
            dock_imu.addWidget(pg_debug)
            pg_debug.setXLink(pg_acceleration)

        # Add button for magnetic calibration
        button = QtWidgets.QPushButton("Get magnetic calibration")
        button.clicked.connect(self.calibrate_mag)
        dock_imu.addWidget(button)

    def calibrate_mag(self):
        print("Start magnetic calibration")

        ## Call ros2 run icm20948_driver magnetic_calibration
        ## with parameters:
        ## bag_path: the path to the bag file
        ## topic_raw_imu_name: "/driver/raw_data"
        os.system("ros2 run icm20948_driver magnetic_calibration --ros-args -p bag_path:=" + self.sfb.file_name + " -p topic_raw_imu_name:=/driver/raw_data")

    def add_euler(self):
        dock_euler = Dock("Euler")
        self.addDock(dock_euler, position='below')
        data = self.sfb.rpy
        data_debug = self.sfb.debug_fusion

        if not data.is_empty():
            pg_roll = pg.PlotWidget()
            self.set_plot_options(pg_roll)
            pg_roll.plot(data.time, data.roll, pen=(255, 0, 0), name="roll")
            dock_euler.addWidget(pg_roll)

            pg_pitch = pg.PlotWidget()
            self.set_plot_options(pg_pitch)
            pg_pitch.plot(data.time, data.pitch, pen=(0, 255, 0), name="pitch")
            dock_euler.addWidget(pg_pitch)
            pg_pitch.setXLink(pg_roll)

            pg_yaw = pg.PlotWidget()
            self.set_plot_options(pg_yaw)
            pg_yaw.plot(data.time, data.yaw, pen=(0, 0, 255), name="yaw")
            dock_euler.addWidget(pg_yaw)
            pg_yaw.setXLink(pg_roll)

    def add_ahrs_error_acc(self):
        dock_ahrs_error_acc = Dock("AHRS error (Acc)")
        self.addDock(dock_ahrs_error_acc, position='below')
        data_debug = self.sfb.debug_fusion
        data = self.sfb.calibrated_data
        pg_acc = None
        data_rpy = self.sfb.rpy

        if not data.is_empty():
            pg_acc = pg.PlotWidget()
            self.set_plot_options(pg_acc)
            pg_acc.plot(data.time, data.accel_x, pen=(255, 0, 0), name="x")
            pg_acc.plot(data.time, data.accel_y, pen=(0, 255, 0), name="y")
            pg_acc.plot(data.time, data.accel_z, pen=(0, 0, 255), name="z")
            pg_acc.plot(data.time, np.sqrt(data.accel_x ** 2 + data.accel_y ** 2 + data.accel_z ** 2),
                                 pen=(255, 255, 255), name="norm")
            pg_acc.setLabel('left', "acceleration")
            dock_ahrs_error_acc.addWidget(pg_acc)

        if not data_rpy.is_empty():
            pg_pitch_roll = pg.PlotWidget()
            pg_pitch_roll.plot(data_rpy.time, data_rpy.roll, pen=(255, 0, 0), name="roll")
            pg_pitch_roll.plot(data_rpy.time, data_rpy.pitch, pen=(0, 255, 0), name="pitch")
            pg_pitch_roll.setLabel('left', "roll/pitch")
            dock_ahrs_error_acc.addWidget(pg_pitch_roll)
            pg_pitch_roll.setXLink(pg_acc)

        if not data_debug.is_empty():
            # Acceleration error
            pg_acceleration_error = pg.PlotWidget()
            self.set_plot_options(pg_acceleration_error)
            pg_acceleration_error.plot(data_debug.time, data_debug.acceleration_error, pen=(255, 0, 0), name="acceleration_error")
            dock_ahrs_error_acc.addWidget(pg_acceleration_error)
            pg_acceleration_error.setXLink(pg_acc)

            # Acceleration recovery trigger
            pg_acceleration_recovery_trigger = pg.PlotWidget()
            self.set_plot_options(pg_acceleration_recovery_trigger)
            pg_acceleration_recovery_trigger.plot(data_debug.time, data_debug.acceleration_recovery_trigger, pen=(0, 0, 255), name="acceleration_recovery_trigger")
            dock_ahrs_error_acc.addWidget(pg_acceleration_recovery_trigger)
            pg_acceleration_recovery_trigger.setXLink(pg_acc)

            # Acceleration recovery
            pg_acc_bool = pg.PlotWidget()
            self.set_plot_options(pg_acc_bool)
            pg_acc_bool.plot(data_debug.time, data_debug.angular_rate_recovery, pen=(0, 0, 255), name="angular_rate_recovery")
            pg_acc_bool.plot(data_debug.time, data_debug.acceleration_recovery, pen=(255, 0, 0), name="acceleration_recovery")
            pg_acc_bool.plot(data_debug.time, data_debug.accelerometer_ignored, pen=(0, 255, 0), name="accelerometer_ignored")
            pg_acc_bool.plot(data_debug.time, data_debug.initialising, pen=(255, 0, 255), name="initialising")

            dock_ahrs_error_acc.addWidget(pg_acc_bool)
            pg_acc_bool.setXLink(pg_acc)

    def add_ahrs_error_mag(self):
        dock_ahrs_error_mag = Dock("AHRS error (Mag)")
        self.addDock(dock_ahrs_error_mag, position='below')
        data_debug = self.sfb.debug_fusion
        data = self.sfb.calibrated_data

        pg_mag = None

        if not data.is_empty():
            pg_mag = pg.PlotWidget()
            self.set_plot_options(pg_mag)
            pg_mag.plot(data.time, data.mag_x, pen=(255, 0, 0), name="x")
            pg_mag.plot(data.time, data.mag_y, pen=(0, 255, 0), name="y")
            pg_mag.plot(data.time, data.mag_z, pen=(0, 0, 255), name="z")
            pg_mag.plot(data.time, np.sqrt(data.mag_x ** 2 + data.mag_y ** 2 + data.mag_z ** 2),
                                 pen=(255, 255, 255), name="norm")
            pg_mag.setLabel('left', "magnetic")
            dock_ahrs_error_mag.addWidget(pg_mag)

        if not data_debug.is_empty():

            # Magnetic error
            pg_magnetic_error = pg.PlotWidget()
            self.set_plot_options(pg_magnetic_error)
            pg_magnetic_error.plot(data_debug.time, data_debug.magnetic_error, pen=(255, 0, 0), name="magnetic_error")
            dock_ahrs_error_mag.addWidget(pg_magnetic_error)
            pg_magnetic_error.setXLink(pg_mag)

            # Magnetometer ignored
            pg_magnetometer_ignored = pg.PlotWidget()
            self.set_plot_options(pg_magnetometer_ignored)
            pg_magnetometer_ignored.plot(data_debug.time, data_debug.magnetometer_ignored, pen=(0, 255, 0), name="magnetometer_ignored")
            dock_ahrs_error_mag.addWidget(pg_magnetometer_ignored)
            pg_magnetometer_ignored.setXLink(pg_mag)

            # Magnetic recovery trigger
            pg_magnetic_recovery_trigger = pg.PlotWidget()
            self.set_plot_options(pg_magnetic_recovery_trigger)
            pg_magnetic_recovery_trigger.plot(data_debug.time, data_debug.magnetic_recovery_trigger, pen=(0, 0, 255), name="magnetic_recovery_trigger")
            dock_ahrs_error_mag.addWidget(pg_magnetic_recovery_trigger)
            pg_magnetic_recovery_trigger.setXLink(pg_mag)

            # Magnetometer limit reached
            pg_mag_bool = pg.PlotWidget()
            self.set_plot_options(pg_mag_bool)
            pg_mag_bool.plot(data_debug.time, data_debug.magnetic_recovery, pen=(0, 0, 255), name="magnetic_recovery")
            pg_mag_bool.plot(data_debug.time, data_debug.magnetometer_limit_reached, pen=(0, 255, 0), name="magnetometer_limit_reached")
            pg_mag_bool.plot(data_debug.time, data_debug.magnetometer_data_skipped, pen=(255, 0, 0), name="magnetometer_data_skipped")
            pg_mag_bool.plot(data_debug.time, data_debug.magnetometer_data_is_ready, pen=(255, 0, 255), name="magnetometer_data_is_ready")
            dock_ahrs_error_mag.addWidget(pg_mag_bool)
            pg_mag_bool.setXLink(pg_mag)

    def add_corr_acc(self):
        dock_corr_acc = Dock("Correlation acceleration")
        self.addDock(dock_corr_acc, position='below')
        data = self.sfb.rpy

        if not data.is_empty():
            pg_acc_x = pg.PlotWidget()
            self.set_plot_options(pg_acc_x)
            pg_acc_x.plot(data.time, data.acceleration_x, pen=(255, 0, 0), name="acceleration_x")
            pg_acc_x.setLabel('left', "corr_acc")
            dock_corr_acc.addWidget(pg_acc_x)

            pg_acc_y = pg.PlotWidget()
            self.set_plot_options(pg_acc_y)
            pg_acc_y.plot(data.time, data.acceleration_y, pen=(0, 255, 0), name="acceleration_y")
            pg_acc_y.setLabel('left', "corr_acc")
            dock_corr_acc.addWidget(pg_acc_y)
            pg_acc_y.setXLink(pg_acc_x)

            pg_acc_z = pg.PlotWidget()
            self.set_plot_options(pg_acc_z)
            pg_acc_z.plot(data.time, data.acceleration_z, pen=(0, 0, 255), name="acceleration_z")
            pg_acc_z.setLabel('left', "corr_acc")
            dock_corr_acc.addWidget(pg_acc_z)
            pg_acc_z.setXLink(pg_acc_x)

    def add_imu_calibrated(self):
        dock_imu = Dock("IMU CALIBRATED")
        self.addDock(dock_imu, position='below')
        data = self.sfb.calibrated_data

        if not data.is_empty():
            pg_acceleration = pg.PlotWidget()
            self.set_plot_options(pg_acceleration)
            pg_acceleration.plot(data.time, data.accel_x, pen=(255, 0, 0), name="x")
            pg_acceleration.plot(data.time, data.accel_y, pen=(0, 255, 0), name="y")
            pg_acceleration.plot(data.time, data.accel_z, pen=(0, 0, 255), name="z")
            pg_acceleration.plot(data.time, np.sqrt(data.accel_x ** 2 + data.accel_y ** 2 + data.accel_z ** 2),
                                 pen=(255, 255, 255), name="norm")
            pg_acceleration.setLabel('left', "acceleration")
            dock_imu.addWidget(pg_acceleration)

            pg_gyro = pg.PlotWidget()
            self.set_plot_options(pg_gyro)
            pg_gyro.plot(data.time, data.gyro_x, pen=(255, 0, 0), name="x")
            pg_gyro.plot(data.time, data.gyro_y, pen=(0, 255, 0), name="y")
            pg_gyro.plot(data.time, data.gyro_z, pen=(0, 0, 255), name="z")
            pg_gyro.setLabel('left', "gyro")
            dock_imu.addWidget(pg_gyro)
            pg_gyro.setXLink(pg_acceleration)

            pg_mag = pg.PlotWidget()
            self.set_plot_options(pg_mag)
            pg_mag.plot(data.time, data.mag_x, pen=(255, 0, 0), name="x")
            pg_mag.plot(data.time, data.mag_y, pen=(0, 255, 0), name="y")
            pg_mag.plot(data.time, data.mag_z, pen=(0, 0, 255), name="z")
            pg_mag.plot(data.time, np.sqrt(data.mag_x ** 2 + data.mag_y ** 2 + data.mag_z ** 2), pen=(255, 255, 255),
                        name="norm")
            pg_mag.setLabel('left', "mag")
            dock_imu.addWidget(pg_mag)
            pg_mag.setXLink(pg_acceleration)

    def add_magnetic_3Dplot(self):
        dock_imu = Dock("MAG 3D")
        self.addDock(dock_imu, position='below')
        data = self.sfb.calibrated_data
        data_raw = self.sfb.raw_data

        if not data.is_empty():
            w = gl.GLViewWidget()
            w.setCameraPosition(distance=200)

            gx = gl.GLGridItem()
            gx.rotate(90, 0, 1, 0)
            gx.translate(-10, 0, 0)
            w.addItem(gx)
            gy = gl.GLGridItem()
            gy.rotate(90, 1, 0, 0)
            gy.translate(0, -10, 0)
            w.addItem(gy)
            gz = gl.GLGridItem()
            gz.translate(0, 0, -10)
            w.addItem(gz)

            axisitem = gl.GLAxisItem()
            axisitem.setSize(100., 100., 100.)
            w.addItem(axisitem)

            pi = gl.GLScatterPlotItem(pos=np.vstack((data.mag_x, data.mag_y, data.mag_z)).T, color=(0, 1, 0, 1), size=1)
            pi.setGLOptions('opaque')
            w.addItem(pi)
            pi2 = gl.GLScatterPlotItem(pos=np.vstack((data_raw.mag_x, data_raw.mag_y, data_raw.mag_z)).T, color=(1, 0, 0, 1), size=1)
            pi2.setGLOptions('opaque')
            w.addItem(pi2)

            dock_imu.addWidget(w)

    def add_wind(self):
        dock_wind = Dock("Wind")
        self.addDock(dock_wind, position='below')
        data = self.sfb.wind

        if not data.is_empty():
            pg_wind = pg.PlotWidget()
            self.set_plot_options(pg_wind)
            pg_wind.plot(data.time, data.velocity * 1.94384, pen=(255, 0, 0), name="velocity (in kt)")
            pg_wind.setLabel('left', "velocity")
            dock_wind.addWidget(pg_wind)

            pg_wind_dir = pg.PlotWidget()
            self.set_plot_options(pg_wind_dir)
            pg_wind_dir.plot(data.time, data.direction, pen=(0, 255, 0), name="direction")
            pg_wind_dir.setLabel('left', "direction")
            dock_wind.addWidget(pg_wind_dir)
            pg_wind_dir.setXLink(pg_wind)

    def add_wind_info(self):
        dock_wind_info = Dock("Wind info")
        self.addDock(dock_wind_info, position='below')
        data = self.sfb.wind

        if not data.is_empty():
            pg_wind_info_battery = pg.PlotWidget()
            self.set_plot_options(pg_wind_info_battery)
            pg_wind_info_battery.plot(data.time, data.battery, pen=(255, 0, 0), name="battery")
            pg_wind_info_battery.setLabel('left', "battery")
            dock_wind_info.addWidget(pg_wind_info_battery)

            pg_wind_info_temperature = pg.PlotWidget()
            self.set_plot_options(pg_wind_info_temperature)
            pg_wind_info_temperature.plot(data.time, data.temperature, pen=(0, 255, 0), name="temperature")
            pg_wind_info_temperature.setLabel('left', "temperature")
            dock_wind_info.addWidget(pg_wind_info_temperature)
            pg_wind_info_temperature.setXLink(pg_wind_info_battery)

            pg_wind_info_roll = pg.PlotWidget()
            self.set_plot_options(pg_wind_info_roll)
            pg_wind_info_roll.plot(data.time, data.roll, pen=(0, 0, 255), name="roll")
            pg_wind_info_roll.setLabel('left', "roll")
            dock_wind_info.addWidget(pg_wind_info_roll)
            pg_wind_info_roll.setXLink(pg_wind_info_battery)

            pg_wind_info_pitch = pg.PlotWidget()
            self.set_plot_options(pg_wind_info_pitch)
            pg_wind_info_pitch.plot(data.time, data.pitch, pen=(255, 0, 0), name="pitch")
            pg_wind_info_pitch.setLabel('left', "pitch")
            dock_wind_info.addWidget(pg_wind_info_pitch)
            pg_wind_info_pitch.setXLink(pg_wind_info_battery)

            pg_wind_info_heading = pg.PlotWidget()
            self.set_plot_options(pg_wind_info_heading)
            pg_wind_info_heading.plot(data.time, data.heading, pen=(0, 255, 0), name="heading")
            pg_wind_info_heading.setLabel('left', "heading")
            dock_wind_info.addWidget(pg_wind_info_heading)
            pg_wind_info_heading.setXLink(pg_wind_info_battery)

    def add_wind_debug(self):
        dock_wind_debug = Dock("Wind debug")
        self.addDock(dock_wind_debug, position='below')
        data = self.sfb.wind_debug

        if not data.is_empty():
            pg_wind_status = pg.PlotWidget()
            self.set_plot_options(pg_wind_status)
            pg_wind_status.plot(data.time, data.status, pen=(255, 0, 0), symbol='o', name="status")
            dock_wind_debug.addWidget(pg_wind_status)

            pg_wind_rate = pg.PlotWidget()
            self.set_plot_options(pg_wind_rate)
            pg_wind_rate.plot(data.time, data.rate, pen=(0, 255, 0), symbol='o', name="rate")
            dock_wind_debug.addWidget(pg_wind_rate)
            pg_wind_rate.setXLink(pg_wind_status)

            pg_wind_sensors = pg.PlotWidget()
            self.set_plot_options(pg_wind_sensors)
            pg_wind_sensors.plot(data.time, data.sensors, pen=(0, 0, 255), symbol='o', name="sensors")
            dock_wind_debug.addWidget(pg_wind_sensors)
            pg_wind_sensors.setXLink(pg_wind_status)

            pg_wind_rssi = pg.PlotWidget()
            self.set_plot_options(pg_wind_rssi)
            pg_wind_rssi.plot(data.time, data.rssi, pen=(255, 0, 255), symbol='o', name="rssi")
            dock_wind_debug.addWidget(pg_wind_rssi)
            pg_wind_rssi.setXLink(pg_wind_status)


