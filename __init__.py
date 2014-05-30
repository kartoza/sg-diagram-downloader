# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StreamFeatureExtractor
                                 A QGIS plugin
 A tool to extract features from a stream network.
                             -------------------
        begin                : 2014-05-07
        copyright            : (C) 2014 by Linfiniti Consulting CC.
        email                : tim@linfiniti.com
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
# Import the PyQt and QGIS libraries
# this import required to enable PyQt API v2
import qgis  # pylint: disable=W0611

import custom_logging  # pylint: disable=relative-import


SENTRY_URL = (
    ' http://9a83c384bc0f476a9ba80958704383a8:'
    'df90821aa62e42868bbe0b40a17d24d5@sentry.linfiniti.com/11')
custom_logging.setup_logger(SENTRY_URL)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """load StreamFeatureExtractor class from file StreamFeatureExtractor."""
    # pylint: disable=relative-import
    from stream_feature_extractor import StreamFeatureExtractor
    # pylint: enable=relative-import
    return StreamFeatureExtractor(iface)
