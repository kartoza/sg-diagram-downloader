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
from __future__ import absolute_import

__author__ = 'ismail@kartoza.com'
__revision__ = '$Format:%H$'
__date__ = '30/05/2014'
__copyright__ = ''

import os
import logging
import subprocess
import sys

from qgis.PyQt.QtWidgets import QDialog

from .utilities.resources import get_ui_class

FORM_CLASS = get_ui_class('sg_log_base.ui')

LOGGER = logging.getLogger('QGIS')


# noinspection PyArgumentList
class LogDialog(QDialog, FORM_CLASS):
    """Beautiful dialog for displaying download results."""

    def __init__(self, iface, parent=None):
        """Constructor.

        :param iface: QGIS interface
        :param parent: Parent widget
        """
        super(LogDialog, self).__init__(parent)
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.iface = iface
        self.log = ''
        self.log_path = ''
        self.output_directory = ''

        # Connect buttons
        self.button_open_log.clicked.connect(self.open_log)
        self.button_open_folder.clicked.connect(self.open_folder)

    def set_log(self, log, log_path, output_directory=None):
        """Set log content and update the dialog.

        :param log: Log text content
        :type log: str

        :param log_path: Path to the log file
        :type log_path: str

        :param output_directory: Path to output folder (optional)
        :type output_directory: str
        """
        self.log = log
        self.log_path = log_path
        self.output_directory = output_directory or os.path.dirname(log_path)

        # Update text display
        self.text_edit_log.setText(self.log)

        # Calculate and display stats
        self._update_stats()

    def _update_stats(self):
        """Update the header stats based on log content."""
        success_count = self.log.count('Success')
        failed_count = self.log.count('Failed')
        total = success_count + failed_count

        if total > 0:
            stats_text = f"{success_count} successful, {failed_count} failed"
        else:
            stats_text = "No downloads processed"

        self.header_stats.setText(stats_text)

        # Update header title based on results
        if failed_count == 0 and success_count > 0:
            self.header_title.setText("Download Complete")
            self.header_frame.setStyleSheet("""
                QFrame#header_frame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1a5f2a, stop:0.5 #228b22, stop:1 #2e8b57);
                    border: none;
                }
            """)
        elif success_count == 0 and failed_count > 0:
            self.header_title.setText("Download Failed")
            self.header_frame.setStyleSheet("""
                QFrame#header_frame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #b71c1c, stop:0.5 #c62828, stop:1 #d32f2f);
                    border: none;
                }
            """)
        elif failed_count > 0:
            self.header_title.setText("Download Completed with Errors")
            self.header_frame.setStyleSheet("""
                QFrame#header_frame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e65100, stop:0.5 #ef6c00, stop:1 #f57c00);
                    border: none;
                }
            """)

    def open_log(self):
        """Open log file using the system's default application."""
        if not self.log_path or not os.path.exists(self.log_path):
            LOGGER.warning(f"Log file not found: {self.log_path}")
            return

        self._open_path(self.log_path)

    def open_folder(self):
        """Open the output folder in the system file manager."""
        folder = self.output_directory

        if not folder or not os.path.exists(folder):
            # Try to get folder from log path
            folder = os.path.dirname(self.log_path) if self.log_path else None

        if folder and os.path.exists(folder):
            self._open_path(folder)
        else:
            LOGGER.warning(f"Folder not found: {folder}")

    def _open_path(self, path):
        """Open a file or folder using the system's default handler.

        :param path: Path to open
        :type path: str
        """
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path], check=True)
            else:
                # Linux and other Unix-like systems
                subprocess.run(['xdg-open', path], check=True)
        except Exception as e:
            LOGGER.error(f"Failed to open {path}: {e}")
