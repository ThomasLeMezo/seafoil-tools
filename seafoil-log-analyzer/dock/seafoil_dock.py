#!/bin/python3

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import pyqtgraph.console
from pyqtgraph.dockarea import *
import numpy as np
import datetime

class SeafoilDock(DockArea):
    def __init__(self, seafoil_bag):
        DockArea.__init__(self)
        self.proxy = []
        self.sfb = seafoil_bag

    def set_plot_options(self, plot):
        plot.addLegend()

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

    def add_label_time(self, p1, starting_time):
        v_line = pg.InfiniteLine(angle=90, movable=False)
        p1.addItem(v_line, ignoreBounds=True)

        if p1.plotItem.legend is None:
            self.set_plot_options(p1)
        p1.plotItem.legend.addItem(p1.plotItem.items[0], "time")
        #label.setText("<span style='font-size: 12pt'>x=%0.1f" % 0)

        def mouse_moved(evt):
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if p1.sceneBoundingRect().contains(pos):
                mouse_point = p1.getViewBox().mapSceneToView(pos)
                t = starting_time + datetime.timedelta(seconds = mouse_point.x())
                ts_string = t.strftime("%Y-%m-%d %H:%M:%S")

                p1.plotItem.legend.items[-1][1].setText(ts_string)
                v_line.setPos(mouse_point.x())

        self.proxy.append(pg.SignalProxy(p1.scene().sigMouseMoved, rateLimit=60, slot=mouse_moved))


