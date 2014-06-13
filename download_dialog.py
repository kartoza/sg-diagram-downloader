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
from datetime import datetime

# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
# do it before Qt imports
import qgis  # pylint: disable=W0611
from os.path import expanduser
from PyQt4 import QtGui, uic
from qgis.core import (
    QGis,
    QgsVectorLayer,
    QgsMapLayer,
    QgsMapLayerRegistry)
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QProgressBar
from PyQt4.QtCore import pyqtSignature, QSettings
from qgis.gui import QgsMessageBar

from sg_download_utilities import download_sg_diagrams

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'download_dialog_base.ui'))

import logging
LOGGER = logging.getLogger('SG-D')


# noinspection PyArgumentList
class DownloadDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(DownloadDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.message_bar = None
        self.iface = iface
        self.populate_combo_box()
        self.province_layer = QgsVectorLayer(
            'data/provinces.shp', 'provinces', 'ogr')
        self.target_layer = None
        self.parcel_layer = None
        self.sg_code_field = None
        self.output_directory = None
        self.restore_state()

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
            theIndex, Qt.UserRole)
        # noinspection PyArgumentList
        layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
        fields = layer.dataProvider().fieldNameMap().keys()
        self.combo_box_sg_code_field.clear()
        for field in fields:
            self.combo_box_sg_code_field.insertItem(0, field, field)

    @pyqtSignature('')  # prevents actions being handled twice
    def on_output_directory_button_clicked(self):
        """Auto-connect slot activated when cache file tool button is clicked.
        """
        # noinspection PyCallByClass,PyTypeChecker
        self.output_directory = QtGui.QFileDialog.getExistingDirectory(
            self,
            self.tr('Set output directory'))
        self.line_edit_output_directory.setText(self.output_directory)

    # noinspection PyArgumentList
    def accept(self):
        """Event handler for when ok is pressed."""
        LOGGER.debug('run the tools')
        self.get_user_options()

        if self.target_layer is None:
            self.show_target_layer_information_message()
            return

        if self.parcel_layer is None:
            self.show_parcel_layer_information_message()
            return

        # check if no feature is selected
        selected_features = self.target_layer.selectedFeatureCount()
        if selected_features == 0:
            self.show_selected_features_information_message()
            return

        if self.output_directory is '' or not os.path.exists(
                self.output_directory):
            self.show_output_directory_information_message()
            return

        message_bar = self.iface.messageBar().createMessage(
            self.tr('Download SG Diagram'),
            self.tr('Please stand by while download process is in progress.'),
            self.iface.mainWindow())

        progress_bar = QProgressBar()
        progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        message_bar.layout().addWidget(progress_bar)
        self.iface.messageBar().pushWidget(
            message_bar, self.iface.messageBar().INFO)
        self.message_bar = message_bar

        self.close()

        def progress_callback(current, maximum, message=None):
            """GUI based callback implementation for showing progress.

            :param current: Current progress.
            :type current: int

            :param maximum: Maximum range (point at which task is complete.
            :type maximum: int

            :param message: Optional message to display in the progress bar
            :type message: str, QString
            """
            if message is not None:
                message_bar.setText(message)
            if progress_bar is not None:
                progress_bar.setMaximum(maximum)
                progress_bar.setValue(current)

        print datetime.now(), '188'

        download_sg_diagrams(
            self.target_layer,
            self.parcel_layer,
            self.sg_code_field,
            self.output_directory,
            self.province_layer,
            callback=progress_callback)

        print datetime.now(), '198'

        message = 'Download completed'
        progress_callback(100, 100, message)

        # Get rid of the message bar again.
        self.iface.messageBar().popWidget(message_bar)

        #QgsMapLayerRegistry.instance().addMapLayers([layer])
        self.iface.messageBar().pushMessage(
            self.tr('Download completed.'),
            self.tr('Your files are available in %s.' % self.output_directory),
            level=QgsMessageBar.INFO,
            duration=10)

        self.save_state()

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

    def show_target_layer_information_message(self):
        """Helper to show information message about target layer."""
        message = (
            'There is no target layer available. Please open a layer for '
            'it')
        # noinspection PyCallByClass
        QtGui.QMessageBox.information(
            self, self.tr('Surveyor General Diagram Downloader'), message)

    def show_parcel_layer_information_message(self):
        """Helper to show information message about parcel layer."""
        message = (
            'There is no parcel layer available. Please open a layer for '
            'it')
        # noinspection PyCallByClass
        QtGui.QMessageBox.information(
            self, self.tr('Surveyor General Diagram Downloader'), message)

    def show_output_directory_information_message(self):
        """Helper to show information message about output directory."""
        message = (
            'Your output directory is either empty or not exist. Please '
            'fill the correct one.')
        # noinspection PyCallByClass
        QtGui.QMessageBox.information(
            self, self.tr('Surveyor General Diagram Downloader'), message)

    def show_selected_features_information_message(self):
        """Helper to show information message about selected features."""
        message = (
            'There is no layer selected in your target layer (%s). Please '
            'select some features to download the surveyor general '
            'diagram' % self.target_layer.name())
        # noinspection PyCallByClass
        QtGui.QMessageBox.information(
            self, self.tr('Surveyor General Diagram Downloader'), message)

    def restore_state(self):
        """Restore state from previous session."""
        home_user = expanduser("~")

        previous_settings = QSettings()
        previous_output_directory = str(previous_settings.value(
            'sg-diagram-downloader/output_directory', home_user, type=str))
        self.line_edit_output_directory.setText(previous_output_directory)

    def save_state(self):
        """Save state from current session."""
        settings = QSettings()
        settings.setValue(
            'sg-diagram-downloader/output_directory', self.output_directory)

    def get_user_options(self):
        """Obtain dialog current options that are input by the user."""
        self.output_directory = self.line_edit_output_directory.text()

        self.sg_code_field = self.combo_box_sg_code_field.currentText()

        index = self.combo_box_target_layer.currentIndex()
        target_layer_id = self.combo_box_target_layer.itemData(
            index, Qt.UserRole)
        # noinspection PyArgumentList
        self.target_layer = QgsMapLayerRegistry.instance().mapLayer(
            target_layer_id)

        index = self.combo_box_parcel_layer.currentIndex()
        diagram_layer_id = self.combo_box_parcel_layer.itemData(
            index, Qt.UserRole)
        # noinspection PyArgumentList
        self.parcel_layer = QgsMapLayerRegistry.instance().mapLayer(
            diagram_layer_id)
