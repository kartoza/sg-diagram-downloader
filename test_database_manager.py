# -*- coding: utf-8 -*-
"""
/***************************************************************************
Test for Database manager for Surveyor General Diagram
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

import unittest
from database_manager import DatabaseManager
from sg_exceptions import DatabaseException
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

sg_diagrams_database = os.path.join(DATA_DIR, 'sg_diagrams.sqlite')


class TestDatabaseManager(unittest.TestCase):
    def test_connection(self):
        spatialite_path = sg_diagrams_database
        db_manager = DatabaseManager(spatialite_path)

        query = 'SELECT count(*) FROM provinces'
        result = db_manager.fetch_one(query)

        expected_result = (7,)
        message = 'Expected %s, got %s' % (expected_result, result)
        self.assertEqual(result, expected_result, message)

        db_manager.close()

        spatialite_path = sg_diagrams_database + 'zero'
        db_manager = DatabaseManager(spatialite_path)

        query = 'SELECT count(*) FROM provinces'

        self.assertRaises(DatabaseException, db_manager.fetch_one, query)

        db_manager.close()

        if os.path.exists(spatialite_path):
            os.remove(spatialite_path)

    def test_fetchone(self):
        """Test for fetching one record."""
        spatialite_path = sg_diagrams_database
        db_manager = DatabaseManager(spatialite_path)

        query = "SELECT province FROM provinces WHERE "
        query += "Within(GeomFromText('POINT(25 -30)'), Geometry)"

        result = db_manager.fetch_one(query)
        expected_result = ('Free State',)
        message = 'Expected %s, got %s' % (expected_result, result)
        self.assertEqual(result, expected_result, message)

        query = "SELECT province FROM provinces WHERE "
        query += "Within(GeomFromText('POINT(100 100)'), Geometry)"

        result = db_manager.fetch_one(query)
        expected_result = None
        message = 'Expected %s, got %s' % (expected_result, result)
        self.assertEqual(result, expected_result, message)
        db_manager.close()


if __name__ == '__main__':
    unittest.main()
