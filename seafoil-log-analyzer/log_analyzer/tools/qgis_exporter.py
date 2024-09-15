import datetime
import os

from PyQt5.QtCore import QDateTime, QTimeZone
from PyQt5.QtGui import QColor
from qgis._core import QgsPoint, QgsSymbol, QgsCoordinateTransformContext, QgsGraduatedSymbolRenderer, QgsColorRamp, \
    QgsClassificationMethod, QgsLineSymbol, QgsRendererRange, QgsClassificationRange, QgsFeatureRenderer


class QgisExporter():
    def __init__(self, seafoil_bag):
        self.sb = seafoil_bag

        # Save the layer to a Shapefile using QgsVectorFileWriter
        name = self.sb.file_name[:self.sb.file_name.rfind('.')] # remove the .* extension
        output_path = self.sb.data_folder + "/" + name + "_track"

        # return if the file already exists
        if os.path.exists(output_path + ".gpkg"):
            print(f"QGIS file {output_path} already exists.")
            return

        from qgis.core import (
            QgsVectorLayer,
            QgsField,
            QgsFeature,
            QgsGeometry,
            QgsPointXY,
            QgsVectorFileWriter
        )
        from qgis.PyQt.QtCore import QVariant
        # Create a new vector layer with line geometry
        layer = QgsVectorLayer('LineString?crs=EPSG:4326', 'lines_layer', 'memory')

        # Define fields for the layer
        layer_provider = layer.dataProvider()
        layer_provider.addAttributes([
            QgsField('time', type=QVariant.DateTime, typeName="Time"),
            QgsField('speed_kt', type=QVariant.Double, typeName="Double"),
            QgsField('heading', type=QVariant.Double, typeName="Double"),
            QgsField('v500_kt', type=QVariant.Double, typeName="Double"),
            QgsField('v1850_kt', type=QVariant.Double, typeName="Double"),
            QgsField('roll_2s', type=QVariant.Double, typeName="Double"),
            QgsField('pitch_2s', type=QVariant.Double, typeName="Double"),
            QgsField('height_2s', type=QVariant.Double, typeName="Double"),
        ])
        layer.updateFields()

        # Create features and add them to the layer
        features = []
        ms_to_knots = 1.94384

        for i in range(len(seafoil_bag.gps_fix.longitude[:-1])):
            feat = QgsFeature()

            # Test if latitude and longitude are the same as the next point
            if (seafoil_bag.gps_fix.longitude[i] == seafoil_bag.gps_fix.longitude[i+1]
                    and seafoil_bag.gps_fix.latitude[i] == seafoil_bag.gps_fix.latitude[i+1]):
                continue

            # Create a line geometry from the list of coordinates
            feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(seafoil_bag.gps_fix.longitude[i], seafoil_bag.gps_fix.latitude[i]),
                                                       QgsPoint(seafoil_bag.gps_fix.longitude[i+1], seafoil_bag.gps_fix.latitude[i+1])]))
            feat.setFields(layer.fields())
            t = QDateTime.fromMSecsSinceEpoch(int((seafoil_bag.gps_fix.time[i]+seafoil_bag.gps_fix.starting_time.timestamp())*1000), QTimeZone.utc())
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

        layer_provider.addFeatures(features)

        # # In symbology, add a graduated color renderer
        # symbol = QgsLineSymbol(layer.renderer().symbol())
        # render = QgsGraduatedSymbolRenderer('speed_kt', [])
        # render.calcEqualIntervalBreaks(minimum=0, maximum=42, classes=20, useSymmetricMode=False, symmetryPoint=0., astride=False)
        # # render.setSourceColorRamp(QgsColorRamp('Turbo'))
        #
        # layer.setRenderer(render)
        # layer.updateExtents()



        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer=layer,
            fileName=output_path,
            transformContext=QgsCoordinateTransformContext(),
            options=QgsVectorFileWriter.SaveVectorOptions(),
        )

        if error == QgsVectorFileWriter.NoError:
            print(f"Exported successfully to {output_path}")
        else:
            print(f"Error occurred: {error}")