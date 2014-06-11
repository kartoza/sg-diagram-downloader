# -*- coding: utf-8 -*-
"""
/***************************************************************************
DownloadDialog
                                 A QGIS plugin
 options
                             -------------------
        begin                : 2014-05-16
        copyright            : (C) 2014 by Options
        email                : tim@linfiniti.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'ismail@linfiniti.com'
__revision__ = '$Format:%H$'
__date__ = '30/05/2014'
__copyright__ = ''

import os

# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
# do it before Qt imports
import qgis  # pylint: disable=W0611

from PyQt4 import QtGui, uic
from qgis.core import (
    QGis,
    QgsField,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsMapLayer,
    QgsRectangle,
    QgsFeatureRequest,
    QgsSpatialIndex,
    QgsMapLayerRegistry)
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignature

from sg_download_utilities import download_sg_diagrams

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'download_dialog_base.ui'))


class DownloadDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(DownloadDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.populate_combo_box()
        self.province_layer = QgsVectorLayer(
            'data/provinces.shp', 'provinces', 'ogr')

    def populate_combo_box(self):
        """Populate the combo boxes with all polygon layers loaded in QGIS."""
        # noinspection PyArgumentList
        registry = QgsMapLayerRegistry.instance()
        layers = registry.mapLayers().values()
        found_flag = False
        for layer in layers:
            # check if layer is a vector polygon layer
            if (layer.type() == QgsMapLayer.VectorLayer and
                    layer.geometryType() == QGis.Polygon):
                found_flag = True
                text = layer.name()
                data = str(layer.id())
                self.combo_box_target_layer.insertItem(0, text, data)
                self.combo_box_parcel_layer.insertItem(0, text, data)
        if found_flag:
            self.combo_box_target_layer.setCurrentIndex(0)
            self.combo_box_parcel_layer.setCurrentIndex(0)

        self.set_tool_tip()

    # noinspection PyPep8Naming
    @pyqtSignature('int')
    def on_combo_box_parcel_layer_currentIndexChanged(self, theIndex=None):
        """Automatic slot executed when the layer is changed to update fields.

        :param theIndex: Passed by the signal that triggers this slot.
        :type theIndex: int
        """
        layer_id = self.combo_box_parcel_layer.itemData(
            theIndex, QtCore.Qt.UserRole)
        # noinspection PyArgumentList
        layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
        fields = layer.dataProvider().fieldNameMap().keys()
        self.combo_box_sg_code_field.clear()
        for field in fields:
            self.combo_box_sg_code_field.insertItem(0, field, field)

        diagram_layer_name = self.combo_box_parcel_layer.currentText()

    @pyqtSignature('')  # prevents actions being handled twice
    def on_output_directory_button_clicked(self):
        """Auto-connect slot activated when cache file tool button is clicked.
        """
        # noinspection PyCallByClass,PyTypeChecker
        output_directory = QtGui.QFileDialog.getExistingDirectory(
            self,
            self.tr('Set output directory'))
        self.output_directory.setText(output_directory)

    def accept(self):
        """Event handler for when ok is pressed."""

        index = self.combo_box_target_layer.currentIndex()
        target_layer_id = self.combo_box_target_layer.itemData(
            index, QtCore.Qt.UserRole)

        # noinspection PyArgumentList
        target_layer = QgsMapLayerRegistry.instance().mapLayer(target_layer_id)

        index = self.combo_box_parcel_layer.currentIndex()
        diagram_layer_id = self.combo_box_parcel_layer.itemData(
            index, QtCore.Qt.UserRole)
        # noinspection PyArgumentList
        diagram_layer = QgsMapLayerRegistry.instance().mapLayer(
            diagram_layer_id)

        sg_code_field = self.combo_box_sg_code_field.currentText()

        output_directory = self.output_directory.text()

        download_sg_diagrams(
            target_layer,
            diagram_layer,
            sg_code_field,
            output_directory,
            self.province_layer)

        self.close()

    def set_tool_tip(self):
        """Set tool tip as helper text for some objects."""

        target_layer_tooltip = (
            'Select at least one feature in the layer you want to use to '
            'select parcels')
        parcel_layer_tooltip = 'Any layer with 21-digit SG code field'

        self.label_target_layer.setToolTip(target_layer_tooltip)
        self.label_parcel_layer.setToolTip(parcel_layer_tooltip)

        self.combo_box_target_layer.setToolTip(target_layer_tooltip)
        self.combo_box_parcel_layer.setToolTip(parcel_layer_tooltip)
