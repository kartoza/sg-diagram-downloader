# coding=utf-8
"""Implementation for SG Downloader map tool."""
# Enable SIP v2
import qgis

from PyQt4.QtCore import Qt, QRegExp
from PyQt4.QtGui import QRegExpValidator, QValidator

from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsRectangle)
from qgis.gui import QgsMapTool, QgsMessageBar


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
        self.iface.messageBar().pushMessage(
            self.tr('SG Downloader.'),
            self.tr('Click on a polygon with a 21 Digit code attribute'),
            level=QgsMessageBar.INFO,
            duration=10)

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

    def canvasReleaseEvent(self, event):
        """Slot called when the mouse button is released on the canvas.

        :param event: Canvas event containing position of click, which button
            was clicked etc.
        """
        if not event.button() == Qt.LeftButton:
            return

        # No need to check that it is a valid, polygon layer
        # as the QAction for this map tool already does that
        layer = self.canvas.currentLayer()

        # Regex to check for the presence of an SG 21 digit code e.g.
        # C01900000000026300000
        # I did a quick scan of all the unique starting letters from
        # Gavin's test dataset and came up with OBCFNT
        prefixes = 'OBCFNT'
        sg_code_regex = QRegExp(
            '^[%s][0-9]{20}$' % prefixes,
            Qt.CaseInsensitive)
        place = self.toMapCoordinates(event.pos())
        # arbitrarily small number
        threshold = 0.00000000000000001
        rectangle = QgsRectangle(
            place.x() - threshold,
            place.y() - threshold,
            place.x() + threshold,
            place.y() + threshold)
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

        sg_field = None
        while polygons.nextFeature(feature):
            geom = feature.geometry()
            attributes = feature.attributes()
            matched = False
            sg_code = None
            if sg_field is None:
                for field in text_fields:
                    value = str(feature[field.name()])
                    if len(value) != 21:
                        continue
                    if value[0] not in prefixes:
                        continue
                    # TODO Regex check
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
                level=QgsMessageBar.INFO,
                duration=10)
        else:
            self.iface.messageBar().pushMessage(
                self.tr('SG Downloader.'),
                self.tr('Fetching diagrams for %s parcels.' % len(fetch_list)),
                level=QgsMessageBar.INFO,
                duration=10)
