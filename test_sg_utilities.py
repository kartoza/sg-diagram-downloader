# coding=utf-8
"""Tests for Utilities functionality.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'ismail@kartoza.com'
__date__ = '30/05/2014'
__copyright__ = ''


import unittest
import os

from qgis.core import (
    QgsPoint,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform
)
from PyQt4 import QtCore

from test.utilities_for_testing import (
    get_temp_shapefile_layer, TEMP_DIR, get_random_string)
from definitions import BASE_URL
from sg_utilities import (
    map_sg_codes_to_provinces,
    download_from_url,
    get_office,
    parse_download_page,
    get_filename,
    is_valid_sg_code,
    point_to_rectangle,
    diagram_directory,
    download_sg_diagram,
    construct_url,
    province_for_point)

from database_manager import DatabaseManager

DATA_TEST_DIR = os.path.join(os.path.dirname(__file__), 'test', 'data')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

sg_diagrams_database = os.path.join(DATA_DIR, 'sg_diagrams.sqlite')

from test.utilities_for_testing import get_qgis_app

QGIS_APP = get_qgis_app()

erf_layer = os.path.join(DATA_TEST_DIR, 'erf.shp')
farm_portion_layer = os.path.join(DATA_TEST_DIR, 'farm_portion.shp')
parent_farm_layer = os.path.join(DATA_TEST_DIR, 'parent_farm.shp')
purchaseplan_layer = os.path.join(DATA_TEST_DIR, 'purchaseplan.shp')

dummy_erf_layer = os.path.join(DATA_TEST_DIR, 'dummy_erf.shp')
dummy_purchaseplan_layer = os.path.join(
    DATA_TEST_DIR, 'dummy_purchaseplan.shp')
dummy_farm_layer = os.path.join(DATA_TEST_DIR, 'dummy_farm.shp')


class TestUtilities(unittest.TestCase):
    # merely assign an attribute
    database_manager = None

    @classmethod
    def setUpClass(cls):
        """Setup Test Class."""
        cls.database_manager = DatabaseManager(sg_diagrams_database)
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

    @classmethod
    def tearDownClass(cls):
        """Tear down Test Class."""
        cls.database_manager.close()

    def test_data(self):
        self.assertTrue(os.path.exists(erf_layer), erf_layer)
        self.assertTrue(os.path.exists(farm_portion_layer), farm_portion_layer)
        self.assertTrue(os.path.exists(parent_farm_layer), parent_farm_layer)
        self.assertTrue(os.path.exists(purchaseplan_layer), purchaseplan_layer)
        self.assertTrue(os.path.exists(dummy_erf_layer), dummy_erf_layer)
        self.assertTrue(os.path.exists(
            dummy_purchaseplan_layer), dummy_purchaseplan_layer)
        self.assertTrue(os.path.exists(dummy_farm_layer), dummy_farm_layer)

    def test_download_from_url(self):
        """Test for download from url."""
        url = (
            BASE_URL +
            'esio/viewTIFF?furl=/images/9a/1018ML01.TIF&office=SGCTN')
        output_directory = TEMP_DIR

        filename = get_random_string() + '.TIF'
        download_from_url(url, output_directory, filename)
        file_path = os.path.join(output_directory, filename)
        message = 'File should be existed in %s.' % file_path
        self.assertTrue(os.path.exists(file_path), message)

    def test_map_sg_codes_to_provinces(self):
        """Test for map_sg_codes_to_provinces."""
        site_layer = get_temp_shapefile_layer(
            purchaseplan_layer, 'purchaseplan')
        diagram_layer = get_temp_shapefile_layer(
            parent_farm_layer, 'parent farm')
        sg_code_field = 'id'

        site_layer.setSelectedFeatures([7])
        sg_codes = map_sg_codes_to_provinces(
            self.database_manager, site_layer, diagram_layer, sg_code_field)
        message = (
            'The number of sg codes extracted should be 33. I got %s' % len(
                sg_codes))
        self.assertEqual(31, len(sg_codes), message)

        site_layer = get_temp_shapefile_layer(
            dummy_purchaseplan_layer, 'purchaseplan')
        diagram_layer = get_temp_shapefile_layer(
            dummy_erf_layer, 'parent farm')
        sg_code_field = 'id'

        sg_codes = map_sg_codes_to_provinces(
            self.database_manager, site_layer, diagram_layer, sg_code_field,
            all_features=True)
        expected_result = {u'C01300280000000600000': 'Western Cape'}
        message = 'Should be %s but got %s' % (expected_result, sg_codes)
        self.assertEqual(expected_result, sg_codes, message)

        # site and parcel layer do not use 4326 crs
        site_layer = get_temp_shapefile_layer(
            dummy_purchaseplan_layer, 'purchaseplan')
        diagram_layer = get_temp_shapefile_layer(
            dummy_farm_layer, 'parent farm')
        sg_code_field = 'id'

        # site and parcel layer have different crs
        sg_codes = map_sg_codes_to_provinces(
            self.database_manager, site_layer, diagram_layer, sg_code_field,
            all_features=True)
        expected_result = {u'C01300280000000600000': 'Western Cape'}
        message = 'Should be %s but got %s' % (expected_result, sg_codes)
        self.assertEqual(expected_result, sg_codes, message)

    def test_get_office(self):
        """Test for get_office function."""
        province = 'Eastern Cape'
        region_code = 'C0020000'

        expected_result = 'SGELN', '8', 'Rural'
        result = get_office(self.database_manager, region_code, province)
        message = 'Expected %s got %s' % (expected_result, result)
        self.assertEqual(expected_result, result, message)

        province = 'Eastern Cape XXX'
        region_code = 'C0020000'
        message = 'Should be None'
        self.assertIsNone(
            get_office(self.database_manager, region_code, province), message)

    def test_parse_download_page(self):
        """Test for parse_download_page."""
        url = (
            BASE_URL +
            'esio/listdocument.jsp?regDivision'
               '=C0160013&Noffice=2&Erf=1234&Portion=0&FarmName=')
        urls = parse_download_page(url)
        expected_urls = [
            BASE_URL + 'esio/viewTIFF?furl=/'
            'images/9a/1018ML01.TIF&office=SGCTN']
        message = 'Should be %s but got %s' % (expected_urls, urls)
        self.assertEqual(urls, expected_urls, message)

    def test_parse_url(self):
        """Test for get_filename."""
        url = (
            BASE_URL + 'esio/viewTIFF?furl=/'
               'images/9a/1018ML01.TIF&office=SGCTN')
        filename = get_filename(url)
        expected_filename = '1018ML01.TIF'
        message = 'Should be %s but got %s' % (expected_filename, filename)
        self.assertEqual(filename, expected_filename, message)

    def test_is_valid_sg_code(self):
        """Test for is_valid_sg_code."""

        self.assertTrue(is_valid_sg_code('C01900000000026300000'))
        self.assertTrue(is_valid_sg_code('B01900000000026300000'))

        # issue #20
        self.assertTrue(is_valid_sg_code('T0JP00000000010800008'))

        self.assertFalse(is_valid_sg_code('Foo'))
        # Too long
        self.assertFalse(is_valid_sg_code('B019000000000263000000'))
        # Too short
        self.assertFalse(is_valid_sg_code('B01900000000026300'))
        # not valid regex
        self.assertFalse(is_valid_sg_code('C0190000000002630000X'))
        # Null
        # noinspection PyUnresolvedReferences
        null_variant = QtCore.QPyNullVariant(str)
        self.assertFalse(is_valid_sg_code(null_variant))

        # unicode
        unicode_sg_code = unicode('B01900000000026300000')
        self.assertTrue(is_valid_sg_code(unicode_sg_code))
        unicode_sg_code = unicode('B0190000000002630000X')
        self.assertFalse(is_valid_sg_code(unicode_sg_code))

    def test_point_to_rectangle(self):
        """Test for point to rectangle."""
        point = QgsPoint(1.0, 1.0)
        rectangle = point_to_rectangle(point)
        expected_rectangle = QgsRectangle(
            0.9999999999900000,
            0.9999999999900000,
            1.0000000000100000,
            1.0000000000100000)
        self.assertEqual(rectangle.toString(), expected_rectangle.toString())

    def test_diagram_directory(self):
        """Test we can get the diagram directory properly."""
        path = diagram_directory()
        self.assertTrue(os.path.exists(path))

    def test_download_sg_diagram(self):
        """Test for download sg diagram."""
        # Do it 5 times, just for checking that everything is fine.
        # No worries, it will not download if the file is existed
        i = 0
        while i < 5:
            sg_code = 'C01300000000001400000'
            province_name = 'Western Cape'
            output_directory = TEMP_DIR
            report = download_sg_diagram(
                self.database_manager,
                sg_code,
                province_name,
                output_directory)
            self.assertEqual(4, report.count('Success'))
            i += 1
        # issue #20
        sg_code = 'T0JP00000000010800008'
        province_name = 'Gauteng'
        output_directory = TEMP_DIR
        report = download_sg_diagram(
            self.database_manager,
            sg_code,
            province_name,
            output_directory)
        message = 'Expected 1 success got %d success' % report.count('Success')
        self.assertEqual(1, report.count('Success'), message)

    def test_construct_url(self):
        """Test constructing url."""
        sg_code = 'C01300000000076700000'
        province = 'Western Cape'
        url = construct_url(self.database_manager, sg_code, province)
        expected_url = (
            BASE_URL + 'esio/listdocument.jsp?regDivision='
            'C0130000&office=SGCTN&Noffice=2&Erf=00000767&Portion=00000')

        message = 'Expected %s, got %s' % (expected_url, url)
        self.assertEqual(url, expected_url, message)

    def test_province_for_point(self):
        """Test for province for point function."""
        # Point falls in South Africa
        point = QgsPoint(21, -30)
        expected_province = 'Free State'
        province = province_for_point(self.database_manager, point)
        message = 'Should be %s but got %s' % (expected_province, province)
        self.assertEqual(expected_province, province, message)

        # Point falls in Indonesia
        point = QgsPoint(109, -7)
        expected_province = None
        province = province_for_point(self.database_manager, point)
        message = 'Should be %s but got %s' % (expected_province, province)
        self.assertEqual(expected_province, province, message)

        # Point falls in South Africa but uses different CRS
        point = QgsPoint(2265216.874, -3952469.869)
        expected_province = None
        province = province_for_point(self.database_manager, point)
        message = 'Should be %s but got %s' % (expected_province, province)
        self.assertEqual(expected_province, province, message)

        # Point falls in South Africa but uses different CRS, reproject to 4326
        osm_crs = QgsCoordinateReferenceSystem(3857)
        wgs84_crs = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(osm_crs, wgs84_crs)

        point = QgsPoint(2265216.874, -3952469.869)
        point_transformed = transformer.transform(point)

        expected_province = 'Western Cape'
        province = province_for_point(self.database_manager, point_transformed)
        message = 'Should be %s but got %s' % (expected_province, province)
        self.assertEqual(expected_province, province, message)


if __name__ == '__main__':
    unittest.main()
