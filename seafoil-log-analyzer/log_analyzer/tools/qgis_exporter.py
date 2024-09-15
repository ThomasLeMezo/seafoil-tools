import datetime

from PyQt5.QtCore import QDate
from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorFileWriter
)
from qgis.PyQt.QtCore import QVariant
from log_analyzer.seafoil_bag import SeafoilBag

class QgisExporter():
    def __init__(self, seafoil_bag):
        self.sb = seafoil_bag

        # Initialize QGIS (only needed if running outside QGIS)
        import qgis
        qgis.core.QgsApplication.setPrefixPath("/usr", True)

        # Create a new vector layer with point geometry
        layer = QgsVectorLayer('Point?crs=EPSG:4326', 'point_layer', 'memory')

        # Define fields for the layer
        layer_provider = layer.dataProvider()
        layer_provider.addAttributes([
            QgsField('time', type=QVariant.Date, typeName="QDate"),
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

        # Data for the features
        points_data = []
        for i in range(len(self.sb.statistics.speed_v500)):
            point = {
                'coordinates': [self.sb.gps_fix.longitude[i], self.sb.gps_fix.latitude[i]],
                # get time as datetime python object
                'time': datetime.datetime.fromtimestamp(self.sb.gps_fix.time[i]),
                'speed_kt': self.sb.gps_fix.speed[i]*1.94384,
                'heading': self.sb.gps_fix.track[i],
                'v500_kt': self.sb.statistics.speed_v500[i],
                'v1850_kt': self.sb.statistics.speed_v1852[i],
                'roll_2s': self.sb.statistics.roll_2s[i] if self.sb.statistics.roll_2s is not None else 0.0,
                'pitch_2s': self.sb.statistics.pitch_2s[i] if self.sb.statistics.pitch_2s is not None else 0.0,
                'height_2s': self.sb.statistics.height_2s[i] if self.sb.statistics.height_2s is not None else 0.0,
            }
            points_data.append(point)

        for point in points_data:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point['coordinates'][0], point['coordinates'][1])))
            # feat.setAttributes([
            #     point['time'],
            #     point['speed_kt'],
            #     point['heading'],
            #     point['v500_kt'],
            #     point['v1850_kt'],
            #     point['roll_2s'],
            #     point['pitch_2s'],
            #     point['height_2s'],
            # ])
            features.append(feat)
        layer_provider.addFeatures(features)

        # Save the layer to a Shapefile using QgsVectorFileWriter
        output_path = "/home/lemezoth/gqis_seafoil_test.shp"
        error = QgsVectorFileWriter.writeAsVectorFormat(
            layer,
            output_path,
            "UTF-8",
            layer.crs(),
            "ESRI Shapefile"
        )

        if error == QgsVectorFileWriter.NoError:
            print(f"Exported successfully to {output_path}")
        else:
            print(f"Error occurred: {error}")