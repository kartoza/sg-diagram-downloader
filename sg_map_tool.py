# coding=utf-8
"""Implementation for SG Downloader map tool."""


# Enable SIP v2

#from PyQt4.QtGui import QRegExpValidator, QValidator
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QProgressBar
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest)
from qgis.gui import QgsMapTool, QgsMessageBar

from sg_utilities import (
    download_sg_diagram,
    province_for_point,
    is_valid_sg_code,
    point_to_rectangle,
    diagram_directory)


class SGMapTool(QgsMapTool):
    """A map tool that lets you click on a parcel to download its SG Diagram.
    """

    def __init__(self, iface, provinces_layer):
        """Constructor.

        :param iface: A QGIS QgisInterface instance.
        :type iface: QgisInterface

        :param provinces_layer: A layer containing provincial boundaries.
        :type provinces_layer: QgsVectorLayer
        """
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.provinces_layer = provinces_layer
        self.message_bar = None
        self.progress_bar = None

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

    def setup_messagebar(self):
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
            level=QgsMessageBar.INFO)

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
            if field.typeName() == 'TEXT':
                text_fields.append(field)

        self.setup_messagebar()

        sg_field = None
        while polygons.nextFeature(feature):
            geom = feature.geometry()
            attributes = feature.attributes()
            matched = False
            sg_code = None
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

        province = province_for_point(place, self.provinces_layer)
        result = ''
        output_path = diagram_directory()

        for sg_code in fetch_list:
            result += download_sg_diagram(
                sg_code,
                province,
                output_path,
                progress_callback)

        log = file('sg_downloader.log', 'a')
        log.write(result)
        log.close()
        # Cant return string from canvas release event
        #return result

