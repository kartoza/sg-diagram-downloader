# coding=utf-8
"""Tests for Utilities functionality.


.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'ismail@linfiniti.com'
__date__ = '30/05/2014'
__copyright__ = ''


import unittest
import os
from test.utilities_for_testing import get_temp_shapefile_layer, TEMP_DIR
from sg_download_utilities import get_sg_codes, download_from_url

DATA_TEST_DIR = os.path.join(os.path.dirname(__file__), 'data')

from test.utilities_for_testing import get_qgis_app

QGIS_APP = get_qgis_app()

erf_layer = os.path.join(DATA_TEST_DIR, 'erf.shp')
farm_portion_layer = os.path.join(DATA_TEST_DIR, 'farm_portion.shp')
parent_farm_layer = os.path.join(DATA_TEST_DIR, 'parent_farm.shp')
provinces_layer = os.path.join(DATA_TEST_DIR, 'provinces.shp')
purchaseplan_layer = os.path.join(DATA_TEST_DIR, 'purchaseplan.shp')

class TestUtilities(unittest.TestCase):
    def test_data(self):
        self.assertTrue(os.path.exists(erf_layer), erf_layer)
        self.assertTrue(os.path.exists(farm_portion_layer), farm_portion_layer)
        self.assertTrue(os.path.exists(parent_farm_layer), parent_farm_layer)
        self.assertTrue(os.path.exists(provinces_layer), provinces_layer)
        self.assertTrue(os.path.exists(purchaseplan_layer), purchaseplan_layer)

    def test_download_from_url(self):
        """Test for download from url."""
        url = (
            'http://csg.dla.gov.za/esio/viewTIFF?furl=/images/9a/1018ML01.TIF')
        # url = 'http://ismailsunni.files.wordpress.com/2014/05/2014-05-04-08-10-51.jpg'
        output_directory = TEMP_DIR
        # download_from_url(url, output_directory, 'random.jpeg')
        download_from_url(url, output_directory, 'random.TIF')

    def test_get_sg_codes(self):
        """Test for get_sg_codes."""
        target_layer = get_temp_shapefile_layer(
            purchaseplan_layer, 'purchaseplan')
        diagram_layer = get_temp_shapefile_layer(
            parent_farm_layer, 'parent farm')
        sg_code_field = 'id'

        target_layer.setSelectedFeatures([7])
        sg_codes = get_sg_codes(target_layer, diagram_layer, sg_code_field)
        message = (
            'The number of sg codes extracted should be 33. I got %s' % len(
                sg_codes))
        self.assertEqual(31, len(sg_codes), message)

if __name__ == '__main__':
    unittest.main()
