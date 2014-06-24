# -*- coding: utf-8 -*-
"""
/***************************************************************************
Exceptions for Surveyor General Diagram
                                 A QGIS plugin
 options
                             -------------------
        begin                : 2014-05-30
        copyright            : (C) 2014 by Options
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
"""
from PyQt4.QtCore import QRegExp, Qt, QSettings

__author__ = 'ismail@linfiniti.com'
__revision__ = '$Format:%H$'
__date__ = '23/06/2014'
__copyright__ = ''


class DownloadException(Exception):
    """Raised if radii for volcano buffer is not as we expect."""
    suggestion = 'Failed to download file'


class DatabaseException(Exception):
    """Raised if radii for volcano buffer is not as we expect."""
    suggestion = 'Failed to execute query'