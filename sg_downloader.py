# -*- coding: utf-8 -*-
"""
/***************************************************************************
DownloadDialog
                                 A QGIS plugin
 options
                             -------------------
        begin                : 2014-05-16
        copyright            : (C) 2014 by Options
        email                : tim@kartoza.com
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

__author__ = 'ismail@kartoza.com'
__revision__ = '$Format:%H$'
__date__ = '30/05/2014'
__copyright__ = ''

import os
from os.path import expanduser
import logging

# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
# do it before Qt imports
import qgis  # pylint: disable=W0611
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
from sg_log import LogDialog

from sg_utilities import download_sg_diagrams, write_log
from database_manager import DatabaseManager

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

sg_diagrams_database = os.path.join(DATA_DIR, 'sg_diagrams.sqlite')

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sg_downloader_base.ui'))

LOGGER = logging.getLogger('QGIS')


# noinspection PyArgumentList
class DownloadDialog(QtGui.QDialog, FORM_CLASS):
    """GUI for downloading SG Plans."""
    def __init__(self, iface, parent=None):
        """Constructor.

        :param iface:
        :param parent:
        """
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

        self.site_layer = iface.activeLayer()
        self.parcel_layer = None
        self.sg_code_field = None
        self.output_directory = None
        self.all_features = None
        self.log_file = None

        self.database_manager = DatabaseManager(sg_diagrams_database)

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
                self.combo_box_parcel_layer.insertItem(0, text, data)
        if found_flag:
            self.combo_box_parcel_layer.setCurrentIndex(0)

    # noinspection PyPep8Naming
    @pyqtSignature('int')
    def on_combo_box_parcel_layer_currentIndexChanged(self, index=None):
        """Automatic slot executed when the layer is changed to update fields.

        :param index: Passed by the signal that triggers this slot.
        :type index: int
        """
        layer_id = self.combo_box_parcel_layer.itemData(
            index, Qt.UserRole)
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
        new_output_directory = QtGui.QFileDialog.getExistingDirectory(
            self,
            self.tr('Set output directory'),
            self.output_directory
        )
        if new_output_directory:
            self.output_directory = new_output_directory
        self.line_edit_output_directory.setText(self.output_directory)

    @pyqtSignature('')  # prevents actions being handled twice
    def on_log_file_button_clicked(self):
        """Auto-connect slot activated when cache file tool button is clicked.
        """
        # noinspection PyCallByClass,PyTypeChecker
        new_log_file = QtGui.QFileDialog.getSaveFileName(
            self,
            self.tr('Set log file'),
            self.log_file,
            self.tr('Log file (*.log)'))
        if new_log_file:
            self.log_file = new_log_file
        self.line_edit_log_file.setText(self.log_file)

    # noinspection PyArgumentList
    @staticmethod
    def layer_has_selection(layer):
        """Check if a layer has any selected features.
        :param layer: A polygon layer.
        :type layer: QgsVectorLayer

        :return: True if some features are selected, false if none.
        :rtype: bool
        """
        selected_features = layer.selectedFeatureCount()
        if selected_features == 0:
            return False
        else:
            return True

    def accept(self):
        """Event handler for when OK is pressed."""
        LOGGER.debug('run the tools')
        self.get_user_options()

        if self.site_layer is None:
            self.show_site_layer_information_message()
            return

        if self.parcel_layer is None:
            self.show_parcel_layer_information_message()
            return

        # check if no feature is selected
        if (not self.layer_has_selection(self.site_layer) and
                self.selected_sites_only.isChecked()):
            self.show_no_selection_warning()
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
        progress_bar.setMaximumWidth(150)
        progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        message_bar.layout().addWidget(progress_bar)
        self.iface.messageBar().pushWidget(
            message_bar, self.iface.messageBar().INFO)
        self.message_bar = message_bar
        self.save_state()
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

        report = download_sg_diagrams(
            self.database_manager,
            self.site_layer,
            self.parcel_layer,
            self.sg_code_field,
            self.output_directory,
            self.all_features,
            callback=progress_callback)

        # Get rid of the message bar again.
        self.iface.messageBar().popWidget(message_bar)

        #QgsMapLayerRegistry.instance().addMapLayers([layer])
        self.iface.messageBar().pushMessage(
            self.tr('Download completed.'),
            self.tr('Your files are available in %s.' % self.output_directory),
            level=QgsMessageBar.INFO,
            duration=10)
        write_log(report, self.log_file)
        self.show_log(report, self.log_file)

    def show_site_layer_information_message(self):
        """Helper to show information message about target layer."""
        message = (
            'There is no site layer available. Please select a layer for '
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
            'Your output directory is either empty or does not exist.'
            'Please fill in the correct one.')
        # noinspection PyCallByClass
        QtGui.QMessageBox.information(
            self, self.tr('Surveyor General Diagram Downloader'), message)

    def show_no_selection_warning(self):
        """Helper to show information message about selected features."""
        message = (
            'There are no features selected in your target layer (%s). Please '
            'select some features before trying to download the Surveyor '
            'General diagram(s) or please uncheck "Use only selected sites. '
            'Leave unchecked to fetch plans for all sites."' %
            self.site_layer.name())
        # noinspection PyCallByClass
        QtGui.QMessageBox.information(
            self, self.tr('Surveyor General Diagram Downloader'), message)

    def restore_state(self):
        """Restore state from previous session."""
        home_user = expanduser("~")
        default_log_file = os.path.join(home_user, 'sg_downloader.log')

        previous_settings = QSettings()

        previous_output_directory = str(previous_settings.value(
            'sg-diagram-downloader/output_directory', home_user, type=str))
        self.line_edit_output_directory.setText(previous_output_directory)

        previous_log_file = str(previous_settings.value(
            'sg-diagram-downloader/log_file', default_log_file, type=str))
        self.line_edit_log_file.setText(previous_log_file)

        previous_all_features = bool(previous_settings.value(
            'sg-diagram-downloader/all_features', True, type=bool))
        self.selected_sites_only.setChecked(not previous_all_features)

        self.get_user_options()

    def save_state(self):
        """Save state from current session."""
        settings = QSettings()
        settings.setValue(
            'sg-diagram-downloader/output_directory', self.output_directory)
        settings.setValue(
            'sg-diagram-downloader/all_features', self.all_features)
        settings.setValue(
            'sg-diagram-downloader/log_file', self.log_file)

    def get_user_options(self):
        """Obtain dialog current options that are input by the user."""
        self.output_directory = self.line_edit_output_directory.text()

        self.sg_code_field = self.combo_box_sg_code_field.currentText()

        self.all_features = not self.selected_sites_only.isChecked()

        self.log_file = self.line_edit_log_file.text()

        index = self.combo_box_parcel_layer.currentIndex()
        parcel_layer_id = self.combo_box_parcel_layer.itemData(
            index, Qt.UserRole)
        # noinspection PyArgumentList
        self.parcel_layer = QgsMapLayerRegistry.instance().mapLayer(
            parcel_layer_id)

    def show_log(self, log, log_path):
        """Show log dialog.

        :param log: Log in text
        :type log: str

        :param log_path: Log file path.
        :type log_path: str
        """
        dialog = LogDialog(self.iface)
        dialog.set_log(log, log_path)
        dialog.exec_()
