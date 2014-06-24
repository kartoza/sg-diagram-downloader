# coding=utf-8
"""Custom QAction implementation."""
from PyQt4.QtGui import QAction
from qgis.core import (
    QGis,
    QgsMapLayer)
from sg_map_tool import SGMapTool


class SGAction(QAction):
    """Custom QAction that will invoke the sg_map_tool when clicked."""
    def __init__(
            self, icon, iface, provinces_layer, menu_text, whats_this_text):
        """Constructor."""
        main_window = iface.mainWindow()
        QAction.__init__(self, icon, menu_text, main_window)
        self.setWhatsThis(whats_this_text)
        self.iface = iface
        self.provinces_layer = provinces_layer
        self.activated.connect(self.run)
        self.iface.currentLayerChanged.connect(self.set_enabled_state)
        self.tool = SGMapTool(self.iface, self.provinces_layer)
        self.set_enabled_state(self.iface.mapCanvas().currentLayer())

    def _disable(self):
        """Disabled the map tool."""
        self.setEnabled(False)
        self.iface.mapCanvas().setMapTool(None)

    def set_enabled_state(self, layer):
        """Slot called when current layer changes to check if tool is usable.

        :param layer: A map layer.
        :type layer: QgsMapLayer
        """
        if not layer:
            self._disable()
            return

        if not layer.isValid():
            self._disable()
            return

        if not layer.type() == QgsMapLayer.VectorLayer:
            self._disable()
            return

        if not layer.geometryType() == QGis.Polygon:
            self._disable()
            return

        self.setEnabled(True)

    def run(self):
        """Slot called when the action is enabled.

        Will make the active map tool the SGMapTool so that when you
        click on the canvas it will try to fetch plans for the clicked
        parcel.
        """
        self.iface.mapCanvas().setMapTool(self.tool)
