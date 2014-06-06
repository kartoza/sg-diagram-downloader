# -*- coding: utf-8 -*-
"""
/***************************************************************************
Script to convert csv file to sqlite.
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
__date__ = '06/06/2014'
__copyright__ = ''

import csv
import sqlite3

if __name__ == '__main__':
    csv_path = '../data/sg_regional_offices.csv'
    sqlite3_path = '../data/sg_regional_offices.sqlite3'

    # adapted from http://stackoverflow.com/a/2888042/1198772
    con = sqlite3.connect(sqlite3_path)
    cur = con.cursor()
    query = "DROP TABLE IF EXISTS regional_office; "

    print 'Executing %s' % query
    cur.execute(query)

    query = "CREATE TABLE regional_office "
    query += "('province', 'region_code', 'typology', 'office', 'office_no');"

    print 'Executing %s' % query
    cur.execute(query)

    with open(csv_path, 'rb') as fin:  # `with` statement available in 2.5+
        # csv.DictReader uses first line in file for column headings by default
        dict_reader = csv.DictReader(fin)  # comma is default delimiter

        # province,region_code,typology,office,office_no
        rows = [(i['province'], i['region_code'], i['typology'],
                  i['office'], i['office_no']) for i in dict_reader]

    query = "INSERT INTO regional_office "
    query += "('province', 'region_code', 'typology', 'office', 'office_no') "
    query += "VALUES (?, ?, ?, ?, ?)"

    print 'Executing %s' % query
    cur.executemany(query, rows)

    con.commit()
