# -*- coding: utf-8 -*-
"""
/***************************************************************************
Exceptions for Surveyor General Diagram
                                 A QGIS plugin
 options
                             -------------------
        begin                : 2014-05-30
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
__date__ = '23/06/2014'
__copyright__ = ''


class DownloadException(Exception):
    """Raised download is failed."""
    reason = 'Failed to download file.'


class DatabaseException(Exception):
    """Raised if return None or error in executing query."""
    reason = 'Failed to execute query.'


class UrlException(Exception):
    """Raised if the url is failed to construct."""
    reason = 'Failed to construct url.'


class InvalidSGCodeException(Exception):
    """Raised if sg code is not valid."""
    reason = 'Invalid sg code.'


class ParseException(Exception):
    """Raised if error in parsing html page."""
    reason = 'Failed to parse html page.'


class NotInSouthAfricaException(Exception):
    """Raised if a geometry is not in South Africa."""
    reason = 'The geometry is not in South Africa.'
