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

class DockData(SeafoilDock):
    def __init__(self, seafoil_bag, tabWidget):
        SeafoilDock.__init__(self, seafoil_bag)
        tabWidget.addTab(self, "Raw Data")
        self.add_profile()
        self.add_profile2()
        self.add_profile_one()
        self.add_imu()
        self.add_imu_calibrated()
        self.add_corr_acc()
        self.add_euler()
        self.add_magnetic_3Dplot()


        print("DockData initialized")

    def add_profile(self):
        dock_profile = Dock("Profile (default)")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.profile)

        if not data.is_empty():

            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(1,0, 1,1, title="interactive")
            p2.addItem( i2, title='' )
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle( showValues=False )
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values = (0, 255),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits = (0, None),
                rounding=1,
                orientation = 'h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem( i2, insert_in=p2 )
            dock_profile.addWidget(pg_profile)

    def add_profile2(self):
        dock_profile = Dock("Profile (zero)")
        self.addDock(dock_profile, position='below')
        data = copy.copy(self.sfb.profile)

        if not data.is_empty():

            # compute the mean of the first 10 profiles
            mean_profile = np.mean(data.profile[0:10,:], axis=0)
            # subtract the mean from all profiles
            data.profile = data.profile - mean_profile
            # for each profile, normalize the maximum to 255
            for i in range(data.nb_elements):
                data.profile[i,:] = data.profile[i,:] / np.max(data.profile[i,:]) * 255

            pg_profile = pg.GraphicsLayoutWidget()
            i2 = pg.ImageItem(image=data.profile)
            p2 = pg_profile.addPlot(1,0, 1,1, title="interactive")
            p2.addItem( i2, title='' )
            # inserted color bar also works with labels on the right.
            p2.showAxis('left')
            p2.getAxis('left').setStyle( showValues=True )
            p2.getAxis('bottom').setLabel('time')
            p2.getAxis('left').setLabel('distance')

            bar = pg.ColorBarItem(
                values = (0, 255),
                colorMap='CET-L4',
                label='horizontal color bar',
                limits = (0, None),
                rounding=1,
                orientation = 'h',
                pen='#8888FF', hoverPen='#EEEEFF', hoverBrush='#EEEEFF80'
            )
            bar.setImageItem( i2, insert_in=p2 )
            dock_profile.addWidget(pg_profile)

    def add_profile_one(self):
        dock_profile_one = Dock("Profile analysis")
        self.addDock(dock_profile_one, position='below')
        data = self.sfb.profile
        i = 10

        if not data.is_empty():
            pg_profile = pg.PlotWidget()
            pg_profile.plot(np.arange(128), data.profile[i,:-1], pen=(255, 0, 0), name="signal", stepMode=True)
            pg_profile.setLabel('left', "status")
            dock_profile_one.addWidget(pg_profile)

    def add_imu(self):
        dock_imu = Dock("IMU RAW")
        self.addDock(dock_imu, position='below')
        data = self.sfb.raw_data

        if not data.is_empty():
            pg_acceleration = pg.PlotWidget()
            self.set_plot_options(pg_acceleration)
            pg_acceleration.plot(data.time, data.accel_x, pen=(255, 0, 0), name="x")
            pg_acceleration.plot(data.time, data.accel_y, pen=(0, 255, 0), name="y")
            pg_acceleration.plot(data.time, data.accel_z, pen=(0, 0, 255), name="z")
            pg_acceleration.plot(data.time, np.sqrt(data.accel_x**2 + data.accel_y**2 + data.accel_z**2), pen=(255, 255, 255), name="norm")
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
            pg_mag.plot(data.time, np.sqrt(data.mag_x**2 + data.mag_y**2 + data.mag_z**2), pen=(255, 255, 255), name="norm")
            pg_mag.setLabel('left', "mag")
            dock_imu.addWidget(pg_mag)
            pg_mag.setXLink(pg_acceleration)

        # Add button for magnetic calibration
        button = QtWidgets.QPushButton("Get magnetic calibration")
        button.clicked.connect(self.calibrate_mag)
        dock_imu.addWidget(button)

    def calibrate_mag(self):
        print("Start magnetic calibration")
        from .ellipsoid_fit import ellipsoid_fit, ellipsoid_plot, data_regularize
        data_raw_mag = self.sfb.raw_data
        print(data_raw_mag.mag_x)
        data = np.column_stack((data_raw_mag.mag_x, data_raw_mag.mag_y, data_raw_mag.mag_z))
        print(data)
        print("Regularizing data")
        data2 = data_regularize(data, divs=256)

        print("Computing ellipsoid fit")
        center, radii, evecs, v = ellipsoid_fit(data2)
        dataC = data - center.T
        dataC2 = data2 - center.T
        a, b, c = radii
        r = (a * b * c) ** (1. / 3.) #preserve volume?
        D = np.array([[r/a, 0., 0.], [0., r/b, 0.], [0., 0., r/c]])
        #http://www.cs.brandeis.edu/~cs155/Lecture_07_6.pdf
        #affine transformation from ellipsoid to sphere (translation excluded)
        TR = evecs.dot(D).dot(evecs.T)
        dataE = TR.dot(dataC2.T).T

        print('ellipsoid_offset: [', center[0][0], ', ', center[1][0], ', ', center[2][0], ']')
        print('ellipsoid_matrix0: [', TR[0][0], ', ', TR[0][1], ', ', TR[0][2], ']')
        print('ellipsoid_matrix1: [', TR[1][0], ', ', TR[1][1], ', ', TR[1][2], ']')
        print('ellipsoid_matrix2: [', TR[2][0], ', ', TR[2][1], ', ', TR[2][2], ']')

        np.savetxt('magcal_ellipsoid.txt', np.vstack((center.T, TR)))
        #
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        #
        #hack  for equal axes
        ax.set_aspect('auto')
        MAX = 50
        for direction in (-1, 1):
            for point in np.diag(direction * MAX * np.array([1, 1, 1])):
                ax.plot([point[0]], [point[1]], [point[2]], 'w')

        ax.scatter(dataC[:,0], dataC[:,1], dataC[:,2], marker='o', color='g')
        ax.scatter(dataC2[:, 0], dataC2[:, 1], dataC2[:, 2], marker='o', color='b')
        ax.scatter(dataE[:, 0], dataE[:, 1], dataE[:, 2], marker='o', color='r')
        # ax.scatter(data_raw_mag.mag_x, data_raw_mag.mag_y, data_raw_mag.mag_z, marker='o', color='k')

        ellipsoid_plot([0, 0, 0], radii, evecs, ax=ax, plotAxes=True, cageColor='g')
        ellipsoid_plot([0, 0, 0], [r, r, r], evecs, ax=ax, plotAxes=True, cageColor='orange')

        ax.plot([r],[0],[0],color='r',marker='o')
        ax.plot([radii[0]],[0],[0],color='b',marker='o')
        # print (np.array([radii[0],0,0]).dot(transform)[0], r)

        plt.show()

    def add_euler(self):
        dock_euler = Dock("Euler")
        self.addDock(dock_euler, position='below')
        data = self.sfb.rpy

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
            pg_acceleration.plot(data.time, np.sqrt(data.accel_x**2 + data.accel_y**2 + data.accel_z**2), pen=(255, 255, 255), name="norm")
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
            pg_mag.plot(data.time, np.sqrt(data.mag_x**2 + data.mag_y**2 + data.mag_z**2), pen=(255, 255, 255), name="norm")
            pg_mag.setLabel('left', "mag")
            dock_imu.addWidget(pg_mag)
            pg_mag.setXLink(pg_acceleration)

    def add_magnetic_3Dplot(self):
        dock_imu = Dock("MAG 3D")
        self.addDock(dock_imu, position='below')
        data = self.sfb.calibrated_data

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

            pi = gl.GLScatterPlotItem(pos=np.vstack((data.mag_x, data.mag_y, data.mag_z)).T, color=(1, 0, 0, 1), size=1)
            pi.setGLOptions('opaque')
            w.addItem(pi)
            dock_imu.addWidget(w)

