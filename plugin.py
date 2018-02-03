# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SGDiagramDownloader
                                 A QGIS plugin
A tool for QGIS that will download SG (South African Surveyor General)
diagrams.
                              -------------------
        begin                : 2014-05-30
        copyright            : (C) 2014 by Kartoza (Pty) Ltd
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
import logging

# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
# do it before Qt imports
import qgis  # NOQA pylint: disable=unused-import

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QAction, QIcon
from qgis.core import QgsVectorLayer

# Import the code for the dialog
from sg_downloader import DownloadDialog
from utilities.resources import resources_path

# from pydev import pydevd  # pylint: disable=F0401

MENU_GROUP_LABEL = u'SG Diagram Downloader'
MENU_RUN_LABEL = u'Download Surveyor General Diagram'
LOGGER = logging.getLogger('QGIS')


class SGDiagramDownloader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Enable remote debugging - should normally be commented out.
        # pydevd.settrace(
        #    'localhost', port=5678, stdoutToServer=True,
        #     stderrToServer=True)

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Declare instance attributes
        self.download_dialog = None

        # Declare instance attributes

        self.actions = []
        self.menu = self.tr(MENU_GROUP_LABEL)
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(MENU_GROUP_LABEL)
        self.toolbar.setObjectName(u'SGDiagramDownloader')

        self.province_layer = QgsVectorLayer(
            os.path.join(os.path.dirname(__file__), 'data', 'provinces.shp'),
            'provinces',
            'ogr')

        if self.province_layer is None:
            LOGGER.error('Could not load provinces layer.')
        else:
            LOGGER.error('Provinces loaded ok.')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SGDiagramDownloader', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the Surveyor Diagram toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str, QString

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :type whats_this: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction

        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    # noinspection PyPep8Naming
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.menu = u'Surveyor General Diagram Downloader'
        icon_path = resources_path('icon.svg')
        self.download_dialog = self.add_action(
            icon_path,
            text=self.tr(u'Download Surveyor General Diagram',),
            callback=self.show_download_dialog,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True)
        # Special case setup for our map tool which uses custom QAction
        # icon = QIcon(':/plugins/SGDiagramDownloader/maptool.svg')
        # map_tool = SGAction(
        #     icon,
        #     self.iface,
        #     'Interactive Downloader',
        #     'Click on a parcel to download its SG Diagram.')
        # self.toolbar.addAction(map_tool)
        # self.iface.addPluginToVectorMenu(self.menu, map_tool)
        # self.actions.append(map_tool)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(MENU_RUN_LABEL),
                action)
            self.iface.removeToolBarIcon(action)

    # @staticmethod
    def show_download_dialog(self):
        """Show the download dialog."""
        dialog = DownloadDialog(self.iface)
        dialog.exec_()  # modal
