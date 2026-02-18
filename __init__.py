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

import os
import sys

# Add third party libraries to path
THIRD_PARTY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'third_party'))
if THIRD_PARTY_DIR not in sys.path:
    sys.path.append(THIRD_PARTY_DIR)

# Setup logging - wrapped in try/except to prevent plugin load failure
try:
    from . import custom_logging

    SENTRY_URL = (
        'http://9a83c384bc0f476a9ba80958704383a8:'
        'df90821aa62e42868bbe0b40a17d24d5@sentry.linfiniti.com/11')
    custom_logging.setup_logger(SENTRY_URL)
except Exception:
    # If logging setup fails, continue without it
    pass


# noinspection PyPep8Naming
def classFactory(iface):
    """Load SGDiagramDownloader class from file plugin.py.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .plugin import SGDiagramDownloader
    return SGDiagramDownloader(iface)
