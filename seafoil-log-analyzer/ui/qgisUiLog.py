import datetime
import os
import time

from PyQt5 import Qt
from PyQt5.QtCore import QDateTime, QTimeZone, QMetaType

from datetime import datetime

from PyQt5.QtGui import QColor
from qgis._core import QgsLineSymbol
from tzlocal import get_localzone

from qgis.core import (
    QgsProject,
    QgsPoint,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsGraduatedSymbolRenderer,
    QgsRendererRangeLabelFormat,
    QgsStyle,
    QgsClassificationCustom,
    Qgis,
    QgsArrowSymbolLayer,
)

import numpy as np


class QgisUiLog():
    def __init__(self, seafoil_bag, log):
        self.sb = seafoil_bag
        self.sb.load_data()
        self.log = log

        first_name = self.log["rider_first_name"]
        last_name = self.log["rider_last_name"]
        # Get timezone of the system
        local_timezone = get_localzone()

        # in str format, local time (self.sb.gps_fix.starting_time is in UTC), using datetime
        starting_time = self.sb.gps_fix.starting_time.astimezone(local_timezone).strftime("%Y-%m-%d %H:%M:%S")

        self.layer_name = f"{first_name} {last_name} - {starting_time}"
        print("layer_name = ", self.layer_name)

        ## Find if layer already exist (and removed it)
        layer_list = QgsProject.instance().mapLayersByName(self.layer_name)
        if len(layer_list)!=0:
            QgsProject.instance().removeMapLayer(layer_list[0])

        # Create a new vector layer with line geometry
        self.layer = QgsVectorLayer('LineString?crs=EPSG:4326', self.layer_name, 'memory')

        # Define fields for the layer
        self.layer_provider = self.layer.dataProvider()
        self.layer_provider.addAttributes(self.get_fields())
        self.layer.updateFields()

        self.layer_provider.addFeatures(self.get_features())

        self.set_renderer()
        self.set_temporal_controller()

        # add the layer to the canvas
        self.layer.updateExtents()
        QgsProject.instance().addMapLayer(self.layer, addToLegend=True)

        print("Layer created")

    def set_temporal_controller(self):
        # Dynamic Temporal control
        temporal = self.layer.temporalProperties()
        temporal.setIsActive(True)
        temporal.setMode(Qgis.VectorTemporalMode.ModeFeatureDateTimeInstantFromField)
        temporal.setStartField("time")
        temporal.setDurationUnits(Qgis.TemporalUnit.Seconds)
        temporal.setFixedDuration(60)

    def set_renderer(self):
        # https://gis.stackexchange.com/questions/342352/apply-a-color-ramp-to-vector-layer-using-pyqgis3
        # In symbology, add a graduated color renderer
        format = QgsRendererRangeLabelFormat()
        format.setFormat("%1 - %2")
        format.setPrecision(2)
        format.setTrimTrailingZeroes(True)

        default_style = QgsStyle().defaultStyle()
        color_ramp = default_style.colorRamp('Turbo')

        renderer = QgsGraduatedSymbolRenderer()
        arrow = QgsArrowSymbolLayer().create()

        # Set stroke color to transparent
        # qls = QgsLineSymbol([arrow])
        qls = QgsLineSymbol.createSimple({'color': 'transparent', 'width': '0.5'})

        renderer.setSourceSymbol(qls)
        renderer.setClassAttribute("speed_kt")
        renderer.setClassificationMethod(QgsClassificationCustom())
        renderer.setLabelFormat(format)
        renderer.setGraduatedMethod(QgsGraduatedSymbolRenderer.GraduatedMethod.GraduatedColor)
        renderer.updateClasses(self.layer,  QgsGraduatedSymbolRenderer.EqualInterval, 42)

        for i in range(42):
            renderer.updateRangeLowerValue(i, float(i))
            renderer.updateRangeUpperValue(i, float(i+1))

        renderer.updateColorRamp(color_ramp)

        self.layer.setRenderer(renderer)

    def get_fields(self):
        return [
            QgsField('time', type=QMetaType.QDateTime, typeName="Time"),
            QgsField('speed_kt', type=QMetaType.Double, typeName="Double"),
            QgsField('heading', type=QMetaType.Double, typeName="Double"),
            QgsField('v500_kt', type=QMetaType.Double, typeName="Double"),
            QgsField('v1850_kt', type=QMetaType.Double, typeName="Double"),
            QgsField('roll_2s', type=QMetaType.Double, typeName="Double"),
            QgsField('pitch_2s', type=QMetaType.Double, typeName="Double"),
            QgsField('height_2s', type=QMetaType.Double, typeName="Double"),
        ]

    def get_features(self):
        # Create features and add them to the layer
        features = []
        ms_to_knots = 1.94384
        for i in range(len(self.sb.statistics.speed_v500[:-1])):
            feat = QgsFeature()

            # Test if latitude and longitude are the same as the next point
            if (self.sb.gps_fix.longitude[i] == self.sb.gps_fix.longitude[i+1]
                    and self.sb.gps_fix.latitude[i] == self.sb.gps_fix.latitude[i+1])\
                or np.isnan(self.sb.gps_fix.longitude[i]) or np.isnan(self.sb.gps_fix.latitude[i]):
                continue

            # Create a line geometry from the list of coordinates
            feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(self.sb.gps_fix.longitude[i], self.sb.gps_fix.latitude[i]),
                                                       QgsPoint(self.sb.gps_fix.longitude[i+1], self.sb.gps_fix.latitude[i+1])]))
            feat.setFields(self.layer.fields())
            t = QDateTime.fromMSecsSinceEpoch(int((self.sb.gps_fix.time[i]+self.sb.gps_fix.starting_time.timestamp())*1000), QTimeZone.utc())
            feat.setAttributes([t,
                                float(self.sb.gps_fix.speed[i] * ms_to_knots),
                                float(self.sb.gps_fix.track[i]),
                                float(self.sb.statistics.speed_v500[i] * ms_to_knots),
                                float(self.sb.statistics.speed_v1852[i] * ms_to_knots),
                                float(self.sb.statistics.roll_2s[i] if self.sb.statistics.roll_2s is not None else 0.0),
                                float(self.sb.statistics.pitch_2s[i] if self.sb.statistics.pitch_2s is not None else 0.0),
                                float(self.sb.statistics.height_2s[i] if self.sb.statistics.height_2s is not None else 0.0),
                                ])
            features.append(feat)
        return features


    # def __del__(self):
    #     layer_list = QgsProject.instance().mapLayersByName(self.layer_name)
    #     if len(layer_list)!=0:
    #         QgsProject.instance().removeMapLayer(layer_list[0])