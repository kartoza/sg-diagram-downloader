# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SGDiagramDownloader
                                 A QGIS plugin
A tool for QGIS that will download SG (South African Surveyor General)
diagrams.
                             -------------------
        begin                : 2014-05-07
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
 This script initializes the plugin, making it known to QGIS.
"""
from __future__ import absolute_import

# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
import os
import sys

from . import custom_logging  # pylint: disable=relative-import

THIRD_PARTY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'third_party'))
if THIRD_PARTY_DIR not in sys.path:
    sys.path.append(THIRD_PARTY_DIR)

LOG_FILE_PATH = '/tmp/sg-download/log.log'

SENTRY_URL = (
    'http://9a83c384bc0f476a9ba80958704383a8:'
    'df90821aa62e42868bbe0b40a17d24d5@sentry.kartoza.com/11')
custom_logging.setup_logger(SENTRY_URL)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """load SGDiagramDownloader class from file SGDiagramDownloader."""
    # pylint: disable=relative-import
    from .plugin import SGDiagramDownloader
    # pylint: enable=relative-import
    return SGDiagramDownloader(iface)
