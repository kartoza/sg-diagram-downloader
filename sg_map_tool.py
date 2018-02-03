# coding=utf-8
"""Implementation for SG Downloader map tool."""


# Enable SIP v2

# from PyQt4.QtGui import QRegExpValidator, QValidator
from PyQt4.QtCore import Qt, QSettings
from PyQt4.QtGui import QProgressBar
from qgis.core import QgsFeature, QgsFeatureRequest
from qgis.gui import QgsMapTool, QgsMessageBar

from sg_utilities import (
    download_sg_diagram,
    province_for_point,
    is_valid_sg_code,
    point_to_rectangle,
    write_log)

from database_manager import DatabaseManager
from sg_log import LogDialog
import os
from os.path import expanduser
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class SGMapTool(QgsMapTool):
    """A map tool that lets you click on a parcel to download its SG Diagram.
    """

    def __init__(self, iface):
        """Constructor.

        :param iface: A QGIS QgisInterface instance.
        :type iface: QgisInterface
        """
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.message_bar = None
        self.progress_bar = None
        self.output_directory = None
        self.log_file = None

        self.restore_state()

        sg_diagrams_database = os.path.join(DATA_DIR, 'sg_diagrams.sqlite')

        self.db_manager = DatabaseManager(sg_diagrams_database)

    def canvasPressEvent(self, event):
        """Slot called when a mouse press occurs on the canvas.

        :param event: Canvas event containing position of click, which button
            was clicked etc.
        """
        pass

    def canvasMoveEvent(self, event):
        """Slot called when a mouse move event occurs on the canvas.

        :param event: Canvas event containing position of click, which button
            was clicked etc.
        """
        pass

    def setup_message_bar(self):
        """Setup a QgsMessageBar for use from callback and user notifications.
        """
        if self.message_bar is not None:
            return

        self.message_bar = self.iface.messageBar().createMessage(
            self.tr('SG Diagram Downloader'),
            self.tr('Please stand by while download process is in progress.'),
            self.iface.mainWindow())
        # Set up message bar for progress reporting
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_bar.layout().addWidget(self.progress_bar)
        self.iface.messageBar().pushWidget(
            self.message_bar, self.iface.messageBar().INFO)

    def canvasReleaseEvent(self, event):
        """Slot called when the mouse button is released on the canvas.

        :param event: Canvas event containing position of click, which button
            was clicked etc.
        """
        if not event.button() == Qt.LeftButton:
            return

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
                self.message_bar.setText(message)
            if self.progress_bar is not None:
                self.progress_bar.setMaximum(maximum)
                self.progress_bar.setValue(current)

        self.iface.messageBar().pushMessage(
            self.tr('SG Downloader.'),
            self.tr('Preparing for download'),
            level=QgsMessageBar.INFO,
            duration=10)

        # No need to check that it is a valid, polygon layer
        # as the QAction for this map tool already does that
        layer = self.canvas.currentLayer()

        place = self.toMapCoordinates(event.pos())
        rectangle = point_to_rectangle(place)

        request = QgsFeatureRequest(QgsFeatureRequest.FilterRect)
        # Ensure only those features really intersecting the rect are returned
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        request.setFilterRect(rectangle)
        polygons = layer.getFeatures(request)
        feature = QgsFeature()
        fetch_list = []
        all_fields = layer.pendingFields()
        text_fields = []
        # Ignore any columns that don't contain text data
        for field in all_fields:
            if field.typeName() == 'String' or field.typeName() == 'Text':
                text_fields.append(field)

        self.setup_message_bar()
        sg_field = None
        while polygons.nextFeature(feature):
            # geom = feature.geometry()
            # attributes = feature.attributes()
            # matched = False
            # sg_code = None
            if sg_field is None:
                for field in text_fields:
                    value = str(feature[field.name()])
                    if not is_valid_sg_code(value):
                        continue
                    sg_field = field.name()
                    fetch_list.append(value)
            else:
                # We already know which column has SG codes
                value = str(feature[sg_field])
                fetch_list.append(value)
        if len(fetch_list) == 0:
            self.iface.messageBar().pushMessage(
                self.tr('SG Downloader.'),
                self.tr('No parcels found with a valid 21 Digit code'),
                level=QgsMessageBar.WARNING,
                duration=10)
            return

        province = province_for_point(self.db_manager, place)

        report = ''
        sg_diagrams_database = os.path.join(DATA_DIR, 'sg_diagrams.sqlite')
        data_manager = DatabaseManager(sg_diagrams_database)

        i = 0
        for sg_code in fetch_list:
            i += 1
            message = 'Downloading SG Code %s from %s' % (sg_code, province)
            progress_callback(i, len(fetch_list), message)
            report += download_sg_diagram(
                data_manager,
                sg_code,
                province,
                self.output_directory,
                callback=progress_callback)
        data_manager.close()

        try:
            write_log(report, self.log_file)
        except IOError as e:
            print e

        self.show_log(report, self.log_file)

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

    def restore_state(self):
        """Restore state from previous session."""
        home_user = expanduser("~")
        default_log_file = os.path.join(home_user, 'sg_downloader.log')

        previous_settings = QSettings()

        self.output_directory = str(previous_settings.value(
            'sg-diagram-downloader/output_directory', home_user, type=str))

        self.log_file = str(previous_settings.value(
            'sg-diagram-downloader/log_file', default_log_file, type=str))
