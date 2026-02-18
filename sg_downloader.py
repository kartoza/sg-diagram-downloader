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
import qgis  # NOQA pylint: disable=unused-import
from qgis.core import (
    Qgis,
    QgsMapLayer,
    QgsProject,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from qgis.PyQt.QtGui import QPixmap, QIcon
from qgis.PyQt.QtCore import QSettings

from .utilities.resources import get_ui_class, resources_path

from .sg_log import LogDialog

from .sg_utilities import download_sg_diagrams, write_log
from .database_manager import DatabaseManager

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

sg_diagrams_database = os.path.join(DATA_DIR, 'sg_diagrams.gpkg')

FORM_CLASS = get_ui_class('sg_downloader_base.ui')

LOGGER = logging.getLogger('SG-Downloader')


# noinspection PyArgumentList
class DownloadDialog(QDialog, FORM_CLASS):
    """Beautiful and intuitive GUI for downloading SG Plans."""

    def __init__(self, iface, parent=None):
        """Constructor.

        :param iface: QGIS interface instance
        :param parent: Parent widget
        """
        super(DownloadDialog, self).__init__(parent)
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.message_bar = None
        self.iface = iface
        self.is_downloading = False

        # Instance variables
        self.site_layer = iface.activeLayer()
        self.parcel_layer = None
        self.sg_code_field = None
        self.output_directory = None
        self.all_features = None
        self.log_file = None

        # Initialize database manager
        self.database_manager = DatabaseManager(sg_diagrams_database)

        # Setup UI components
        self._setup_header_icon()
        self._setup_connections()
        self._populate_layers()
        self._update_selection_status()

        # Restore previous settings
        self.restore_state()

    def _setup_header_icon(self):
        """Set up the header icon from resources."""
        icon_path = resources_path('icon.svg')
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.header_icon.setPixmap(
                    pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            # Also set window icon
            self.setWindowIcon(QIcon(icon_path))

    def _setup_connections(self):
        """Set up signal/slot connections."""
        # Button connections
        self.button_download.clicked.connect(self.on_download_clicked)
        self.output_directory_button.clicked.connect(self.on_output_directory_button_clicked)
        self.log_file_button.clicked.connect(self.on_log_file_button_clicked)

        # Combo box connections
        self.combo_box_parcel_layer.currentIndexChanged.connect(
            self.on_combo_box_parcel_layer_currentIndexChanged
        )

        # Radio button connections for visual feedback
        self.radio_selected_only.toggled.connect(self._update_selection_status)
        self.radio_all_features.toggled.connect(self._update_selection_status)

    def _populate_layers(self):
        """Populate the combo boxes with all polygon layers loaded in QGIS."""
        project = QgsProject.instance()
        layers = list(project.mapLayers().values())
        found_flag = False

        for layer in layers:
            # Check if layer is a vector polygon layer
            if (layer.type() == QgsMapLayer.VectorLayer and
                    layer.geometryType() == QgsWkbTypes.PolygonGeometry):
                found_flag = True
                text = layer.name()
                data = str(layer.id())
                self.combo_box_parcel_layer.insertItem(0, text, data)

        if found_flag:
            self.combo_box_parcel_layer.setCurrentIndex(0)

    def _update_selection_status(self):
        """Update the selection status label with current layer info."""
        if self.site_layer:
            layer_name = self.site_layer.name()
            selected_count = self.site_layer.selectedFeatureCount()
            total_count = self.site_layer.featureCount()

            if self.radio_selected_only.isChecked():
                if selected_count == 0:
                    status_text = (
                        f"Active layer: {layer_name} | "
                        f"No features selected - please select features first"
                    )
                    self.selection_status.setStyleSheet("""
                        QLabel {
                            color: #c62828;
                            font-weight: normal;
                            font-size: 11px;
                            font-style: italic;
                            padding: 4px 8px;
                            background-color: #ffebee;
                            border-radius: 4px;
                            border: 1px solid #ffcdd2;
                        }
                    """)
                else:
                    status_text = (
                        f"Active layer: {layer_name} | "
                        f"Selected: {selected_count} of {total_count} features"
                    )
                    self.selection_status.setStyleSheet("""
                        QLabel {
                            color: #2e7d32;
                            font-weight: normal;
                            font-size: 11px;
                            font-style: italic;
                            padding: 4px 8px;
                            background-color: #e8f5e9;
                            border-radius: 4px;
                            border: 1px solid #c8e6c9;
                        }
                    """)
            else:
                status_text = (
                    f"Active layer: {layer_name} | "
                    f"Will process all {total_count} features"
                )
                self.selection_status.setStyleSheet("""
                    QLabel {
                        color: #e65100;
                        font-weight: normal;
                        font-size: 11px;
                        font-style: italic;
                        padding: 4px 8px;
                        background-color: #fff3e0;
                        border-radius: 4px;
                        border: 1px solid #ffe0b2;
                    }
                """)
        else:
            status_text = "No active layer selected - please select a layer in QGIS"
            self.selection_status.setStyleSheet("""
                QLabel {
                    color: #c62828;
                    font-weight: normal;
                    font-size: 11px;
                    font-style: italic;
                    padding: 4px 8px;
                    background-color: #ffebee;
                    border-radius: 4px;
                    border: 1px solid #ffcdd2;
                }
            """)

        self.selection_status.setText(status_text)

    def cleanup(self):
        """Clean up resources when done."""
        if self.database_manager is not None:
            self.database_manager.close()
            self.database_manager = None

    def reject(self):
        """Handle dialog cancel/close."""
        self.cleanup()
        super(DownloadDialog, self).reject()

    def on_combo_box_parcel_layer_currentIndexChanged(self, index=None):
        """Update SG code field dropdown when layer is changed.

        :param index: Combo box index
        :type index: int
        """
        if not isinstance(index, int):
            return

        layer_id = self.combo_box_parcel_layer.itemData(index, Qt.UserRole)
        layer = QgsProject.instance().mapLayer(layer_id)

        if layer is None:
            return

        fields = list(layer.dataProvider().fieldNameMap().keys())
        self.combo_box_sg_code_field.clear()

        # Try to find a likely SG code field and put it first
        sg_field_hints = ['sg_code', 'sgcode', 'sg', 'code', 'id', 'parcel_id']
        sorted_fields = []
        other_fields = []

        for field in fields:
            if any(hint in field.lower() for hint in sg_field_hints):
                sorted_fields.append(field)
            else:
                other_fields.append(field)

        # Add likely fields first, then others
        for field in sorted_fields + other_fields:
            self.combo_box_sg_code_field.addItem(field, field)

    def on_output_directory_button_clicked(self):
        """Open directory browser for output folder."""
        current_dir = self.line_edit_output_directory.text() or expanduser("~")
        new_output_directory = QFileDialog.getExistingDirectory(
            self,
            self.tr('Select Output Folder for Diagrams'),
            current_dir
        )
        if new_output_directory:
            self.line_edit_output_directory.setText(new_output_directory)

    def on_log_file_button_clicked(self):
        """Open file dialog for log file selection."""
        current_file = self.line_edit_log_file.text() or expanduser("~")
        new_log_file, _ = QFileDialog.getSaveFileName(
            self,
            self.tr('Select Log File Location'),
            current_file,
            self.tr('Log Files (*.log);;All Files (*)')
        )
        if new_log_file:
            self.line_edit_log_file.setText(new_log_file)

    @staticmethod
    def layer_has_selection(layer):
        """Check if a layer has any selected features.

        :param layer: A polygon layer
        :type layer: QgsVectorLayer
        :return: True if some features are selected
        :rtype: bool
        """
        return layer.selectedFeatureCount() > 0

    def on_download_clicked(self):
        """Handle download button click."""
        LOGGER.debug('Download button clicked')
        self.get_user_options()

        # Validation
        if not self._validate_inputs():
            return

        # Start download process
        self._start_download()

    def _validate_inputs(self):
        """Validate all user inputs before download.

        :return: True if all inputs are valid
        :rtype: bool
        """
        if self.site_layer is None:
            self._show_error(
                "No Active Layer",
                "Please select a layer in QGIS before opening this dialog. "
                "The active layer will be used to identify which parcels to process."
            )
            return False

        if self.parcel_layer is None:
            self._show_error(
                "No Parcel Layer",
                "Please select a parcel layer from the dropdown. "
                "This layer should contain cadastral polygons with SG codes."
            )
            return False

        # Check for feature selection if using selected features only
        if self.radio_selected_only.isChecked() and not self.layer_has_selection(self.site_layer):
            self._show_warning(
                "No Features Selected",
                f"No features are selected in '{self.site_layer.name()}'.\n\n"
                "Please either:\n"
                "  - Select some features in QGIS, or\n"
                "  - Choose 'All features' option"
            )
            return False

        if not self.output_directory or not os.path.exists(self.output_directory):
            self._show_error(
                "Invalid Output Folder",
                "Please select a valid output folder where the diagrams will be saved."
            )
            return False

        if not self.sg_code_field:
            self._show_error(
                "No SG Code Field",
                "Please select the field containing SG codes from the dropdown."
            )
            return False

        return True

    def _show_error(self, title, message):
        """Show an error message box with consistent styling.

        :param title: Dialog title
        :param message: Error message
        """
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def _show_warning(self, title, message):
        """Show a warning message box with consistent styling.

        :param title: Dialog title
        :param message: Warning message
        """
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def _start_download(self):
        """Start the download process with progress tracking."""
        self.is_downloading = True
        self.save_state()

        # Show progress section
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_status.setText("Initializing download...")

        # Disable controls during download
        self._set_controls_enabled(False)
        self.button_download.setText("Downloading...")

        # Process events to update UI
        QApplication.processEvents()

        # Create progress callback
        def progress_callback(current, maximum, message=None):
            """Update progress bar and status."""
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(current)
            if message:
                # Truncate long messages
                display_msg = message if len(message) < 80 else message[:77] + "..."
                self.progress_status.setText(display_msg)
            QApplication.processEvents()

        try:
            # Run download
            report = download_sg_diagrams(
                self.database_manager,
                self.site_layer,
                self.parcel_layer,
                self.sg_code_field,
                self.output_directory,
                self.all_features,
                callback=progress_callback
            )

            # Update progress to complete
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.progress_status.setText("Download complete!")
            QApplication.processEvents()

            # Write log file
            if self.log_file:
                write_log(report, self.log_file)

            # Show completion message
            self._show_completion_message()

            # Show log dialog
            self.show_log(report, self.log_file)

        except Exception as e:
            LOGGER.exception("Download failed")
            self._show_error(
                "Download Failed",
                f"An error occurred during download:\n\n{str(e)}"
            )
        finally:
            # Clean up
            self.is_downloading = False
            self.cleanup()
            self._set_controls_enabled(True)
            self.button_download.setText("Download Diagrams")
            self.progress_frame.setVisible(False)
            self.close()

    def _set_controls_enabled(self, enabled):
        """Enable or disable form controls.

        :param enabled: Whether controls should be enabled
        :type enabled: bool
        """
        self.step1_group.setEnabled(enabled)
        self.step2_group.setEnabled(enabled)
        self.step3_group.setEnabled(enabled)
        self.button_download.setEnabled(enabled)
        # Keep cancel button enabled for user to close dialog

    def _show_completion_message(self):
        """Show completion notification in QGIS message bar."""
        self.iface.messageBar().pushMessage(
            self.tr('Download Complete'),
            self.tr(f'Diagrams saved to: {self.output_directory}'),
            level=Qgis.Success,
            duration=10
        )

    def restore_state(self):
        """Restore state from previous session."""
        home_user = expanduser("~")
        default_output = os.path.join(home_user, 'sg-diagrams')
        default_log_file = os.path.join(home_user, 'sg_downloader.log')

        settings = QSettings()

        # Restore output directory
        previous_output = settings.value(
            'sg-diagram-downloader/output_directory', default_output, type=str
        )
        self.line_edit_output_directory.setText(previous_output)

        # Restore log file
        previous_log = settings.value(
            'sg-diagram-downloader/log_file', default_log_file, type=str
        )
        self.line_edit_log_file.setText(previous_log)

        # Always default to selected features only for safety
        self.radio_selected_only.setChecked(True)

        # Update internal state
        self.get_user_options()

    def save_state(self):
        """Save state for next session."""
        settings = QSettings()
        settings.setValue(
            'sg-diagram-downloader/output_directory', self.output_directory
        )
        settings.setValue(
            'sg-diagram-downloader/log_file', self.log_file
        )

    def get_user_options(self):
        """Extract current dialog options into instance variables."""
        self.output_directory = self.line_edit_output_directory.text()
        self.sg_code_field = self.combo_box_sg_code_field.currentText()
        self.all_features = self.radio_all_features.isChecked()
        self.log_file = self.line_edit_log_file.text()

        index = self.combo_box_parcel_layer.currentIndex()
        if index >= 0:
            parcel_layer_id = self.combo_box_parcel_layer.itemData(index, Qt.UserRole)
            self.parcel_layer = QgsProject.instance().mapLayer(parcel_layer_id)

    def show_log(self, log, log_path):
        """Show log dialog with download results.

        :param log: Log content
        :type log: str
        :param log_path: Path to log file
        :type log_path: str
        """
        dialog = LogDialog(self.iface)
        dialog.set_log(log, log_path, self.output_directory)
        dialog.exec_()
