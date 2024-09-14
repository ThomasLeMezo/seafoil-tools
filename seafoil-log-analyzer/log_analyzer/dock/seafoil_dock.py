#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
import numpy as np
import datetime
from pyqtgraph.Qt import QtGui, QtCore

class SeafoilDock(DockArea):
    def __init__(self, seafoil_bag):
        DockArea.__init__(self)
        self.proxy = []
        self.sfb = seafoil_bag

    def set_plot_options(self, plot):
        plot.addLegend()
        plot.showGrid(x=True, y=True)

    def text_write_reset(self, p, t):
        text = pg.TextItem(html='<div style="text-align: left"><span style="color: #FFF;">RESET</span></div>', anchor=(-0.3,1.3),border='w', fill=(0, 0, 255, 100))
        p.addItem(text)
        text.setPos(t, 0)
        arrow = pg.ArrowItem(pos=(t, 0), angle=-45)
        p.addItem(arrow)

    def text_write_plot(self, p, t, x, msg):
        text = pg.TextItem(html='<div style="text-align: left"><span style="color: #FFF;">'+msg+'</span></div>', anchor=(-0.3,1.3),border='w', fill=(0, 0, 255, 100))
        p.addItem(text)
        text.setPos(t, x)
        arrow = pg.ArrowItem(pos=(t, x), angle=-45)
        p.addItem(arrow)

    def add_label_with_text(self, dock, text):
        label = QtGui.QLabel()
        label.setText(text)
        # label align center
        label.setAlignment(QtCore.Qt.AlignCenter)
        # label increase font size
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        # Add to widget
        dock.addWidget(label, row=dock.currentRow+1, col=0)

    def add_label_time(self, pg_list, starting_time, dock):
        label_time = QtGui.QLabel()
        label_time.setText("Time")
        # label align center
        label_time.setAlignment(QtCore.Qt.AlignCenter)
        # label increase font size
        font = label_time.font()
        font.setPointSize(14)
        label_time.setFont(font)
        # Add to widget
        dock.addWidget(label_time, row=dock.currentRow+1, col=0)

        v_line_list = []
        for p in pg_list:
            v_line = pg.InfiniteLine(angle=90, movable=False)
            v_line_list.append(v_line)
            p.addItem(v_line, ignoreBounds=True)

            if p.plotItem.legend is None:
                self.set_plot_options(p)
            #p.plotItem.legend.addItem(p.plotItem.items[0], "time")
            #label.setText("<span style='font-size: 12pt'>x=%0.1f" % 0)

        def mouse_moved(evt):
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            t = starting_time
            ts_string = t.strftime("%Y-%m-%d %H:%M:%S")
            mouse_point = None

            for p1 in pg_list:
                if p1.sceneBoundingRect().contains(pos):
                    mouse_point = p1.getViewBox().mapSceneToView(pos)
                    t = starting_time + datetime.timedelta(seconds = mouse_point.x())
                    ts_string = t.strftime("%Y-%m-%d %H:%M:%S")
                    label_time.setText(ts_string)
                    break

            if mouse_point is not None:
                # for p1 in pg_list:
                #     p1.plotItem.legend.items[-1][1].setText(ts_string)
                for v in v_line_list:
                    v.setPos(mouse_point.x())

        for p in pg_list:
            self.proxy.append(pg.SignalProxy(p.scene().sigMouseMoved, rateLimit=60, slot=mouse_moved))


