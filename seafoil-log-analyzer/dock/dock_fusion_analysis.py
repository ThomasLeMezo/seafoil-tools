#!/bin/python3

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


class DockFusionAnalysis(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget, dock_analysis):
        SeafoilDock.__init__(self, seafoil_bag)

        # return if raw_data is empty
        if self.sfb.raw_data.is_empty():
            return

        tabWidget.addTab(self, "Fusion Analysis")

        self.dock_analysis = dock_analysis
        self.fusion_gain_ = 0.5
        self.acceleration_rejection_ = 10.0
        self.magnetic_rejection_ = 10.0
        self.recovery_trigger_period_ = 1

        self.first_time_replay = True

        self.analysis_time = np.array([])
        self.analysis_euler_angle_roll = np.array([])
        self.analysis_euler_angle_pitch = np.array([])
        self.analysis_euler_angle_yaw = np.array([])
        self.analysis_lin_acc_axis_x = np.array([])
        self.analysis_lin_acc_axis_y = np.array([])
        self.analysis_lin_acc_axis_z = np.array([])
        self.analysis_accelerometer_axis_x = np.array([])
        self.analysis_accelerometer_axis_y = np.array([])
        self.analysis_accelerometer_axis_z = np.array([])
        self.analysis_gyroscope_axis_x = np.array([])
        self.analysis_gyroscope_axis_y = np.array([])
        self.analysis_gyroscope_axis_z = np.array([])
        self.analysis_magnetometer_axis_x = np.array([])
        self.analysis_magnetometer_axis_y = np.array([])
        self.analysis_magnetometer_axis_z = np.array([])
        self.analysis_int_states_accelerationError = np.array([])
        self.analysis_int_states_accelerometerIgnored = np.array([])
        self.analysis_int_states_accelerationRecoveryTrigger = np.array([])
        self.analysis_int_states_magneticError = np.array([])
        self.analysis_int_states_magnetometerIgnored = np.array([])
        self.analysis_int_states_magneticRecoveryTrigger = np.array([])
        self.analysis_flags_initialising = np.array([])
        self.analysis_flags_angularRateRecovery = np.array([])
        self.analysis_flags_accelerationRecovery = np.array([])
        self.analysis_flags_magneticRecovery = np.array([])

        self.add_replay_fusion()

        print("DockFusionAnalysis initialized")

    def get_data_val(self, id):
        if (id == 0):
            return self.fusion_gain_
        elif (id == 1):
            return self.acceleration_rejection_
        elif (id == 2):
            return self.magnetic_rejection_
        elif (id == 3):
            return self.recovery_trigger_period_
        else:
            return 0.

    def set_data_val(self, id, val):
        if (id == 0):
            self.fusion_gain_ = val
        elif (id == 1):
            self.acceleration_rejection_ = val
        elif (id == 2):
            self.magnetic_rejection_ = val
        elif (id == 3):
            self.recovery_trigger_period_ = val

    def valueChanged(self, sb):
        self.set_data_val(self.spins[sb][1], sb.value())
        self.spins[sb][2].setText(str(self.get_data_val(self.spins[sb][1])))

    def process_data(self):
        # Export yaml parameters
        import yaml
        data = {
            'fusion_analysis': {
                'ros__parameters': {
                    'fusion_gain': self.fusion_gain_,
                    'acceleration_rejection': self.acceleration_rejection_,
                    'magnetic_rejection': self.magnetic_rejection_,
                    'recovery_trigger_period': self.recovery_trigger_period_,
                    'bag_path': self.sfb.file_name,
                }
            }
        }

        yaml_content = yaml.dump(data)
        with open('/tmp/seafoil_analysis_data.yaml', 'w') as file:
            yaml.dump(data, file)

        # Call subprocess cpp ros node fusion_analysis from icm20948_driver with yaml file parameters
        import os
        os.system("ros2 run icm20948_driver fusion_analysis  --ros-args --params-file /tmp/seafoil_analysis_data.yaml")

        # Load the csv file result and extract the data
        import pandas as pd
        data = pd.read_csv('/tmp/seafoil_fusion_replay.csv', delimiter=";")

        self.analysis_time = data['time'].to_numpy()
        self.analysis_time -= self.sfb.rosout.starting_time.timestamp()
        self.analysis_euler_angle_roll = data['euler_angle_roll'].to_numpy()
        self.analysis_euler_angle_pitch = data['euler_angle_pitch'].to_numpy()
        self.analysis_euler_angle_yaw = (data['euler_angle_yaw'].to_numpy()+180)%360.0
        self.analysis_lin_acc_axis_x = data['lin_acc_axis_x'].to_numpy()
        self.analysis_lin_acc_axis_y = data['lin_acc_axis_y'].to_numpy()
        self.analysis_lin_acc_axis_z = data['lin_acc_axis_z'].to_numpy()
        self.analysis_accelerometer_axis_x = data['accelerometer_axis_x'].to_numpy()
        self.analysis_accelerometer_axis_y = data['accelerometer_axis_y'].to_numpy()
        self.analysis_accelerometer_axis_z = data['accelerometer_axis_z'].to_numpy()
        self.analysis_gyroscope_axis_x = data['gyroscope_axis_x'].to_numpy()
        self.analysis_gyroscope_axis_y = data['gyroscope_axis_y'].to_numpy()
        self.analysis_gyroscope_axis_z = data['gyroscope_axis_z'].to_numpy()
        self.analysis_magnetometer_axis_x = data['magnetometer_axis_x'].to_numpy()
        self.analysis_magnetometer_axis_y = data['magnetometer_axis_y'].to_numpy()
        self.analysis_magnetometer_axis_z = data['magnetometer_axis_z'].to_numpy()
        self.analysis_int_states_accelerationError = data['int_states_accelerationError'].to_numpy()
        self.analysis_int_states_accelerometerIgnored = data['int_states_accelerometerIgnored'].to_numpy()
        self.analysis_int_states_accelerationRecoveryTrigger = data['int_states_accelerationRecoveryTrigger'].to_numpy()
        self.analysis_int_states_magneticError = data['int_states_magneticError'].to_numpy()
        self.analysis_int_states_magnetometerIgnored = data['int_states_magnetometerIgnored'].to_numpy()
        self.analysis_int_states_magneticRecoveryTrigger = data['int_states_magneticRecoveryTrigger'].to_numpy()
        self.analysis_flags_initialising = data['flags_initialising'].to_numpy()
        self.analysis_flags_angularRateRecovery = data['flags_angularRateRecovery'].to_numpy()
        self.analysis_flags_accelerationRecovery = data['flags_accelerationRecovery'].to_numpy()
        self.analysis_flags_magneticRecovery = data['flags_magneticRecovery'].to_numpy()

    def call_compute_fusion(self):
        style = self.button.styleSheet()
        self.button.setStyleSheet("background-color : red")
        self.button.update()
        self.process_data()
        if self.first_time_replay:
            self.add_replay_euler()

            self.first_time_replay = False
        else:
            self.update_replay_fusion()
        self.button.setStyleSheet(style)

    def add_replay_fusion(self):
        dock_replay = Dock("Replay Fusion")
        self.addDock(dock_replay, position='below')

        cw = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        cw.setLayout(layout)
        dock_replay.addWidget(cw)

        self.spins = {
            pg.SpinBox(): ["fusion_gain", 0, QtWidgets.QLabel()],
            pg.SpinBox(): ["acceleration_rejection", 1, QtWidgets.QLabel()],
            pg.SpinBox(): ["magnetic_rejection", 2, QtWidgets.QLabel()],
            pg.SpinBox(int=True): ["covery_trigger_period", 3, QtWidgets.QLabel()],
        }

        i = 0
        for spin in self.spins:
            spin.setValue(self.get_data_val(self.spins[spin][1]))
            self.spins[spin][2].setText(str(self.get_data_val(self.spins[spin][1])))
            label = QtWidgets.QLabel(self.spins[spin][0])
            spin.sigValueChanged.connect(self.valueChanged)
            layout.addWidget(label, i, 0)
            layout.addWidget(spin, i, 1)
            layout.addWidget(self.spins[spin][2], i, 2)
            i += 1

        # self.button_param = QtWidgets.QPushButton('Load parameters')
        # layout.addWidget(self.button_param)
        # self.button_param.clicked.connect(self.open_yaml)

        self.button = QtWidgets.QPushButton('Compute Fusion')
        layout.addWidget(self.button)
        self.button.clicked.connect(self.call_compute_fusion)

    def update_replay_fusion(self):
        self.replay_roll.setData(self.analysis_time, self.analysis_euler_angle_roll)
        self.replay_pitch.setData(self.analysis_time, self.analysis_euler_angle_pitch)
        self.replay_yaw.setData(self.analysis_time, self.analysis_euler_angle_yaw)

        self.dock_analysis_replay_pitch.setData(self.analysis_time, self.analysis_euler_angle_pitch)
        self.dock_analysis_replay_roll.setData(self.analysis_time, self.analysis_euler_angle_roll)
        self.dock_analysis_replay_yaw.setData(self.analysis_time, self.analysis_euler_angle_yaw)

    def add_replay_euler(self):
        dock_euler = Dock("Euler")
        self.addDock(dock_euler, position='above')
        data = self.sfb.rpy
        data_debug = self.sfb.debug_fusion

        if not data.is_empty():
            pg_roll = pg.PlotWidget()
            self.set_plot_options(pg_roll)
            pg_roll.plot(data.time, data.roll, pen=(255, 0, 0), name="roll")
            self.replay_roll = pg_roll.plot(self.analysis_time, self.analysis_euler_angle_roll, pen=(0, 0, 255), name="roll [recomputed]")
            dock_euler.addWidget(pg_roll)

            pg_pitch = pg.PlotWidget()
            self.set_plot_options(pg_pitch)
            pg_pitch.plot(data.time, data.pitch, pen=(0, 255, 0), name="pitch")
            self.replay_pitch = pg_pitch.plot(self.analysis_time, self.analysis_euler_angle_pitch, pen=(255, 0, 0), name="pitch [recomputed]")
            dock_euler.addWidget(pg_pitch)
            pg_pitch.setXLink(pg_roll)

            pg_yaw = pg.PlotWidget()
            self.set_plot_options(pg_yaw)
            pg_yaw.plot(data.time, data.yaw, pen=(0, 0, 255), name="yaw")
            self.replay_yaw = pg_yaw.plot(self.analysis_time, self.analysis_euler_angle_yaw, pen=(0, 255, 0), name="yaw [recomputed]")
            dock_euler.addWidget(pg_yaw)
            pg_yaw.setXLink(pg_roll)

            self.dock_analysis_replay_pitch = self.dock_analysis.list_pg_roll_pitch[0].plot(self.analysis_time, self.analysis_euler_angle_pitch, pen=(255, 0, 0), name="pitch [recomputed]")
            self.dock_analysis_replay_roll = self.dock_analysis.list_pg_roll_pitch[0].plot(self.analysis_time, self.analysis_euler_angle_roll, pen=(0, 0, 255), name="roll [recomputed]")
            self.dock_analysis_replay_yaw = self.dock_analysis.list_pg_yaw[0].plot(self.analysis_time, self.analysis_euler_angle_yaw, pen=(0, 255, 0), name="yaw [recomputed]")
