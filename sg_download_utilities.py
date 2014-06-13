# -*- coding: utf-8 -*-
"""
/***************************************************************************
Utilities for Surveyor General Diagram
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
__date__ = '30/05/2014'
__copyright__ = ''

import os

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsFeatureRequest,
    QgsSpatialIndex)

import pycurl
import sqlite3
import urllib
import sys
from urlparse import urlparse


third_party_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'third_party'))
if third_party_path not in sys.path:
    sys.path.append(third_party_path)
# pylint: disable=F0401
# noinspection PyUnresolvedReferences
from bs4 import BeautifulSoup
# pylint: enable=F0401

import logging
from custom_logging import LOGGER

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PROVINCES_LAYER_PATH = os.path.join(DATA_DIR, 'provinces.shp')
REGIONAL_OFFICES_SQLITE3 = os.path.join(
    DATA_DIR, 'sg_regional_offices.sqlite3')


def get_office(region_code=None, province=None):
    """Get office and office no from database using region_code and province.

    :param region_code: SG code.
    :type region_code: str

    :param province: province name.
    :type province: str

    :returns: office and office number
    :rtype: tuple
    """
    try:
        db_connection = sqlite3.connect(REGIONAL_OFFICES_SQLITE3)
        db_cursor = db_connection.cursor()
        query = (
            "SELECT office, office_no, typology FROM regional_office WHERE "
            "province='%s' AND region_code='%s'" % (province, region_code))

        print 'Executing %s' % query
        db_cursor.execute(query)
        db_connection.commit()

        row = db_cursor.fetchone()

        db_connection.close()

        return row
    except sqlite3.DatabaseError as e:
        print 'Database error', e


def construct_url(sg_code=None, province=None):
    """Construct url to download sg diagram.

    :param sg_code: SG code.
    :type sg_code: str

    :param province: province name.
    :type province: str

    :returns: URL to download sg diagram.
    :rtype: str
    """
    print 'Constructing url for %s %s' % (sg_code, province)
    if sg_code is None or province is None:
        return (
            'http://csg.dla.gov.za/esio/listdocument.jsp?regDivision=C0160013'
            '&Noffice=2&Erf=1234&Portion=0&FarmName=')

    base_url = 'http://csg.dla.gov.za/esio/listdocument.jsp?'
    reg_division = sg_code[:8]

    office, office_number, typology = get_office(reg_division, province)

    erf = sg_code[8:16]
    portion = sg_code[16:]
    url = base_url + 'regDivision=' + reg_division
    url += '&office=' + office
    url += '&Noffice=' + office_number
    url += '&Erf=' + erf
    url += '&Portion=' + portion
    return url


def get_filename(url):
    """Parse url to get a file name.
    :param url: Url to download a file that contains a filename.
    :type url: str

    :returns: A file name with extension.
    :rtype: str
    """
    parsed_url = urlparse(url)
    url_query = parsed_url[4]
    file_name = url_query.split('&')[0].split('/')[-1]

    return file_name


def download_from_url(url, output_directory, filename=None):
    """Download file from a url and put it under output_directory.

    :param url: Url that gives response.
    :type url: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str

    :returns: File path if success to download, else None
    :rtype: str
    """
    if filename is None:
        filename = get_filename(url)
    print 'Download file %s from %s' % (filename, url)
    file_path = os.path.join(output_directory, filename)
    if os.path.exists(file_path):
        print 'File %s existed, not downloading' % file_path
        return file_path

    try:
        fp = open(file_path, 'wb')
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, str(url))
        curl.setopt(pycurl.CONNECTTIMEOUT, 60)
        curl.setopt(pycurl.FOLLOWLOCATION, True)
        curl.setopt(pycurl.NOBODY, False)

        curl.setopt(pycurl.WRITEDATA, fp)
        curl.perform()

        curl.close()
        fp.close()
    except Exception, e:
        raise Exception(e)

    if os.path.exists(file_path):
        return file_path
    else:
        return None


def parse_download_page(download_page_url):
    """Parse download_page_url to get list of download link.

    :param download_page_url: Url to download page.
    :type download_page_url: str

    :returns: List of url to download the diagram.
    :rtype: list
    """
    download_urls = []
    prefix_url = 'http://csg.dla.gov.za/esio/'
    html = urllib.urlopen(download_page_url)
    download_page_soup = BeautifulSoup(html)
    urls = download_page_soup.find_all('a')
    for url in urls:
        full_url = url['href']
        if full_url[0:2] == './':
            full_url = full_url[2:]
        full_url = prefix_url + full_url
        download_urls.append(str(full_url))
    return download_urls


def download_sg_diagram(sg_code, province, output_directory):
    """Download sg diagram using sg_code and put it under output_directory.

    :param sg_code: Surveyor General code.
    :type sg_code: str

    :param province: Province name.
    :type province: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str
    """
    download_page = construct_url(sg_code, province)
    print 'Download page: %s' % download_page
    # Parse link here
    download_links = parse_download_page(download_page)

    output_directory = os.path.join(output_directory, sg_code)
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    i = 0
    for download_link in download_links:
        i += 1
        try:
            file_path = download_from_url(download_link, output_directory)
            if file_path is not None:
                message = (
                    '%s %s %d %d True %s' % (
                        sg_code, province, i, len(download_links), file_path))
                LOGGER.debug(message)
            else:
                message = (
                    '%s %s %d %d False N/A' % (
                        sg_code, province, i, len(download_links)))
                LOGGER.debug(message)
        except Exception, e:
            message = (
                '%s %s %d %d False %s' % (
                    sg_code, province, i, len(download_links), e))
            LOGGER.debug(message)


def get_spatial_index(data_provider):
    """Create spatial index from a data provider."""
    qgs_feature = QgsFeature()
    index = QgsSpatialIndex()
    qgs_features = data_provider.getFeatures()
    while qgs_features.nextFeature(qgs_feature):
        index.insertFeature(qgs_feature)
    return index


def get_sg_codes_and_provinces(
        target_layer, diagram_layer, sg_code_field, provinces_layer):
    """Obtains sg codes from target layer.

    :param target_layer: The target layer.
    :type target_layer: QgsVectorLayer

    :param diagram_layer: Vector layer that has sg code in its field.
    :type diagram_layer: QgsVectorLayer

    :param sg_code_field: Name of the field that contains sg code
    :type sg_code_field: str

    :param provinces_layer: Vector layer that contains provinces.
    :type provinces_layer: QgsVectorLayer

    :returns: List of tuple sg code and province name
    :rtype: list
    """
    intersects = []
    sg_codes_and_provinces = []

    provinces_data_provider = provinces_layer.dataProvider()
    province_index = provinces_layer.fieldNameIndex('province')
    province_feature = QgsFeature()

    sg_code_index = diagram_layer.fieldNameIndex(sg_code_field)
    if sg_code_index == -1:
        message = 'Field "%s" not found' % sg_code_field
        raise Exception(message)

    data_provider = diagram_layer.dataProvider()

    spatial_index = get_spatial_index(data_provider)

    selected_features = target_layer.selectedFeatures()
    for selected_feature in selected_features:
        for feature in data_provider.getFeatures():
            geometry = selected_feature.geometry()
            feature_geometry = feature.geometry()

            intersect = geometry.intersects(feature_geometry)
            if intersect:
                intersects.append(feature.id())

    feature = QgsFeature()
    for intersect in intersects:
        index = int(intersect)
        data_provider.getFeatures(QgsFeatureRequest().setFilterFid(index))\
            .nextFeature(feature)
        sg_code = feature.attributes()[sg_code_index]

        geometry = feature.geometry()
        centroid = geometry.centroid().asPoint()

        inside_province = False
        province_name = 'Null'
        provinces_data_features = provinces_data_provider.getFeatures()
        while provinces_data_features.nextFeature(province_feature):
            if province_feature.geometry().contains(centroid):
                inside_province = True
                province_name = province_feature.attributes()[province_index]

        if not inside_province:
            province_name = 'Null'

        if [sg_code, province_name] not in sg_codes_and_provinces:
            sg_codes_and_provinces.append([sg_code, province_name])

    return sg_codes_and_provinces


def print_progress_callback(current, maximum, message=None):
    """GUI based callback implementation for showing progress.

    :param current: Current progress.
    :type current: int

    :param maximum: Maximum range (point at which task is complete.
    :type maximum: int

    :param message: Optional message to display in the progress bar
    :type message: str, QString
    """
    print '%d of %d' + str(message) % (current, maximum)


def download_sg_diagrams(
        target_layer,
        diagram_layer,
        sg_code_field,
        output_directory,
        provinces_layer,
        callback=None):
    """Downloads all SG Diagrams.

    :param target_layer: The target layer.
    :type target_layer: QgsVectorLayer

    :param diagram_layer: Vector layer that has sg code in its field.
    :type diagram_layer: QgsVectorLayer

    :param sg_code_field: Name of the field that contains sg code
    :type sg_code_field: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str

    :param provinces_layer: province layer that will be used.
    :type provinces_layer: QgsVectorLayer

    :param callback: A function to all to indicate progress. The function
        should accept params 'current' (int) and 'maximum' (int). Defaults to
        None.
    :type callback: function
    """
    if callback is None:
        callback = print_progress_callback

    sg_codes_and_provinces = get_sg_codes_and_provinces(
        target_layer, diagram_layer, sg_code_field, provinces_layer)
    maximum = len(sg_codes_and_provinces)
    current = 0
    for sg_code_and_province in sg_codes_and_provinces:
        sg_code = sg_code_and_province[0]
        province = sg_code_and_province[1]
        download_sg_diagram(sg_code, province, output_directory)
        message = 'Downloading %s (%d of %d)' % (sg_code, current + 1, maximum)
        callback(current, maximum, message)
        current += 1
        from datetime import datetime
        print datetime.now(), message


if __name__ == '__main__':
    print PROVINCES_LAYER_PATH
    print os.path.exists(PROVINCES_LAYER_PATH)
