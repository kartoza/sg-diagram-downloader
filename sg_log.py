# -*- coding: utf-8 -*-
"""
/***************************************************************************
LogDialog
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
import logging
import webbrowser

# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
# do it before Qt imports
import qgis  # pylint: disable=W0611
from PyQt4 import QtGui

from utilities.resources import get_ui_class

FORM_CLASS = get_ui_class('sg_log_base.ui')

LOGGER = logging.getLogger('QGIS')


# noinspection PyArgumentList
class LogDialog(QtGui.QDialog, FORM_CLASS):
    """GUI for downloading SG Plans."""
    def __init__(self, iface, parent=None):
        """Constructor.

        :param iface:
        :param parent:
        """
        super(LogDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        QtGui.QDialog.__init__(self, parent)
        self.iface = iface
        self.setupUi(self)
        self.log = ''
        self.log_path = ''

        open_button = self.button_box.button(QtGui.QDialogButtonBox.Open)
        open_button.clicked.connect(self.open_log)

    def set_log(self, log, log_path):
        """Set log in the dialog.

        :param log: Log from a process
        :type log: str
        """
        self.log = log
        self.log_path = log_path
        self.text_edit_log.setText(self.log)

    def open_log(self):
        """Open log file using default text editor."""
        webbrowser.open(self.log_path)
