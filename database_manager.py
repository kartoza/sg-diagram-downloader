# -*- coding: utf-8 -*-
"""
/***************************************************************************
Database manager for Surveyor General Diagram
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
__author__ = 'ismail@linfiniti.com'
__revision__ = '$Format:%H$'
__date__ = '24/06/2014'
__copyright__ = ''

from pyspatialite import dbapi2 as db
import os
from sg_exceptions import DatabaseException

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

REGIONAL_OFFICES_SQLITE3 = os.path.join(
    DATA_DIR, 'sg_regional_offices.sqlite3')


class DatabaseManager():
    """Class for handling database connections."""
    def __init__(self, spatialite_path):
        """Init method.

        :param spatialite_path: Path to spatialite file.
        :type spatialite_path: str
        """
        self.db_connection = None
        self.db_cursor = None

        self.connect(spatialite_path)

    def connect(self, spatialite_path):
        """Create connection and cursor to database.

        :param spatialite_path: Path to spatialite file.
        :type spatialite_path: str
        """
        self.db_connection = db.connect(spatialite_path)
        self.db_cursor = self.db_connection.cursor()

    def execute_query(self, query):
        """Execute a query.

        :param query: A query.
        :type query: str

        :returns: Cursor to result
        :rtype: db.Cursor

        :raise: DatabaseException
        """
        try:
            result = self.db_cursor.execute(query)
            return result
        except db.Error as e:
            raise DatabaseException(e)

    def fetch_one(self, query):
        """Execute query and return one record of the result.

        :param query: A query.
        :type query: str

        :returns: Tuple to the element obtained
        :rtype: tuple

        :raise: DatabaseException
        """
        self.execute_query(query)
        return self.db_cursor.fetchone()

    def close(self):
        """Close all connections of the database."""
        self.db_cursor.close()
        self.db_connection.close()

        self.db_cursor = None
        self.db_connection = None
