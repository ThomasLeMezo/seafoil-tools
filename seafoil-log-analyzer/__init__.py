# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Seafoil
                                 A QGIS plugin
 Analysis of windfoil session (and other support)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-09-17
        copyright            : (C) 2024 by Thomas Le Mézo
        email                : thomas.le_mezo@ensta-bretagne.org
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Seafoil class from file Seafoil.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    from .seafoil_analyzer import Seafoil
    return Seafoil(iface)
