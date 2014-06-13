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
from test.utilities_for_testing import (
    get_temp_shapefile_layer, TEMP_DIR, get_random_string)
from sg_download_utilities import (
    get_sg_codes_and_provinces,
    download_from_url,
    get_office,
    parse_download_page,
    get_filename)


DATA_TEST_DIR = os.path.join(os.path.dirname(__file__), 'test', 'data')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

from test.utilities_for_testing import get_qgis_app

QGIS_APP = get_qgis_app()

erf_layer = os.path.join(DATA_TEST_DIR, 'erf.shp')
farm_portion_layer = os.path.join(DATA_TEST_DIR, 'farm_portion.shp')
parent_farm_layer = os.path.join(DATA_TEST_DIR, 'parent_farm.shp')
provinces_layer = os.path.join(DATA_DIR, 'provinces.shp')
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
            'http://csg.dla.gov.za/esio/viewTIFF?'
            'furl=/images/9a/1018ML01.TIF&office=SGCTN')
        output_directory = TEMP_DIR
        filename = get_random_string() + '.TIF'
        download_from_url(url, output_directory, filename)
        file_path = os.path.join(output_directory, filename)
        message = 'File should be existed in %s.' % file_path
        self.assertTrue(os.path.exists(file_path), message)

    def test_get_sg_codes(self):
        """Test for get_sg_codes_and_provinces."""
        site_layer = get_temp_shapefile_layer(
            purchaseplan_layer, 'purchaseplan')
        diagram_layer = get_temp_shapefile_layer(
            parent_farm_layer, 'parent farm')
        sg_code_field = 'id'
        sa_provinces_layer = get_temp_shapefile_layer(
            provinces_layer, 'provinces')

        site_layer.setSelectedFeatures([7])
        sg_codes = get_sg_codes_and_provinces(
            site_layer, diagram_layer, sg_code_field, sa_provinces_layer)
        message = (
            'The number of sg codes extracted should be 33. I got %s' % len(
                sg_codes))
        self.assertEqual(31, len(sg_codes), message)

    def test_get_office(self):
        """Test for get_office function."""
        province = 'Eastern Cape'
        region_code = 'C0020000'

        expected_result = 'SGELN', '8', 'Rural'
        result = get_office(region_code, province)
        message = 'Expected %s got %s' % (expected_result, result)
        self.assertEqual(expected_result, result, message)

        province = 'Eastern Cape XXX'
        region_code = 'C0020000'
        message = 'Should be None'
        self.assertIsNone(get_office(region_code, province), message)

    def test_parse_download_page(self):
        """Test for parse_download_page."""
        url = ('http://csg.dla.gov.za/esio/listdocument.jsp?regDivision'
               '=C0160013&Noffice=2&Erf=1234&Portion=0&FarmName=')
        urls = parse_download_page(url)
        expected_urls = [
            'http://csg.dla.gov.za/esio/viewTIFF?furl=/'
            'images/9a/1018ML01.TIF&office=SGCTN']
        message = 'Should be %s but got %s' % (expected_urls, urls)
        self.assertEqual(urls, expected_urls, message)

    def test_parse_url(self):
        """Test for get_filename."""
        url = ('http://csg.dla.gov.za/esio/viewTIFF?furl=/'
               'images/9a/1018ML01.TIF&office=SGCTN')
        filename = get_filename(url)
        expected_filename = '1018ML01.TIF'
        message = 'Should be %s but got %s' % (expected_filename, filename)
        self.assertEqual(filename, expected_filename)

if __name__ == '__main__':
    unittest.main()
