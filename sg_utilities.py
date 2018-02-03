# -*- coding: utf-8 -*-
"""
/***************************************************************************
Utilities for Surveyor General Diagram
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
__date__ = '30/05/2014'
__copyright__ = ''

import os
import re

from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsSpatialIndex,
    QgsRectangle,
    QgsCoordinateReferenceSystem)

from PyQt4.QtNetwork import QNetworkAccessManager
from PyQt4.QtCore import QSettings

import urllib
import sys
from urlparse import urlparse
from definitions import BASE_URL
from file_downloader import FileDownloader
from sg_exceptions import (
    DownloadException,
    DatabaseException,
    UrlException,
    InvalidSGCodeException,
    ParseException,
    NotInSouthAfricaException
)
from proxy import get_proxy

# pylint: disable=F0401
# noinspection PyUnresolvedReferences
from bs4 import BeautifulSoup
# pylint: enable=F0401

from custom_logging import LOGGER

third_party_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'third_party'))
if third_party_path not in sys.path:
    sys.path.append(third_party_path)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SG_DIAGRAM_SQLITE3 = os.path.join(DATA_DIR, 'sg_diagrams.sqlite')
PROVINCE_NAMES = [
    'Eastern Cape',
    'KwaZulu-Natal',
    'Limpopo',
    'Mpumalanga',
    'Western Cape',
    'Gauteng',
    'Free State'
]


def write_log(log, log_path):
    """Show log dialog.

    :param log: Log in text
    :type log: str

    :param log_path: Log file path.
    :type log_path: str
    """
    try:
        f = open(log_path, 'a')
        f.write(log)
        f.close()
    except IOError as e:
        raise e


def get_office(db_manager, region_code=None, province=None):
    """Get office and office no from database using region_code and province.

    :param db_manager: A database manager
    :type db_manager: DatabaseManager

    :param region_code: SG code.
    :type region_code: str

    :param province: province name.
    :type province: str

    :returns: office and office number
    :rtype: tuple
    """
    try:
        query = (
            "SELECT office, office_no, typology FROM regional_office WHERE "
            "province='%s' AND region_code='%s'" % (province, region_code))

        result = db_manager.fetch_one(query)

        return result
    except DatabaseException as e:
        raise DatabaseException(e)


def is_valid_sg_code(value):
    """Check if a string is a valid SG Code.

    :param value: The string to be tested.
    :type value: str, unicode

    :returns: True if the code is valid, otherwise False.
    :rtype: bool
    """
    # Handling unicode input. Found on Windows.
    if type(value) == unicode:
        value = str(value)

    # False if value is not a string or value is not True
    if type(value) != str or not value:
        return False
    # Regex to check for the presence of an SG 21 digit code e.g.
    # C01900000000026300000
    # I did a quick scan of all the unique starting letters from
    # Gavin's test dataset and came up with OBCFNT
    prefixes = 'OBCFNT'
    sg_code_regex_string = '^[%s][A-Z0-9]{4}[0-9]{16}$' % prefixes
    sg_code_regex = re.compile(sg_code_regex_string)
    if len(value) != 21:
        return False
    if value[0] not in prefixes:
        return False
    if not sg_code_regex.match(value):
        return False

    return True


def construct_url(db_manager, sg_code=None, province_name=None):
    """Construct url to download sg diagram.

    :param db_manager: A database manager
    :type db_manager: DatabaseManager

    :param sg_code: SG code.
    :type sg_code: str

    :param province_name: province_name name.
    :type province_name: str

    :returns: URL to download sg diagram.
    :rtype: str
    """
    LOGGER.info('Constructing url for %s %s' % (sg_code, province_name))
    if not is_valid_sg_code(sg_code):
        raise InvalidSGCodeException

    if sg_code is None or province_name is None:
        raise UrlException()

    if province_name not in PROVINCE_NAMES:
        raise NotInSouthAfricaException

    base_url = BASE_URL + 'esio/listdocument.jsp?'
    reg_division = sg_code[:8]

    try:
        record = get_office(db_manager, reg_division, province_name)
    except DatabaseException:
        raise DatabaseException

    if record is None or bool(record) is None:
        raise DatabaseException

    office, office_number, typology = record

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


def download_from_url(url, output_directory, filename=None, use_cache=True):
    """Download file from a url and put it under output_directory.

    :param url: Url that gives response.
    :type url: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str

    :param filename: Optional filename for downloaded file.
    :type filename: str

    :param use_cache: If there is a cached copy of the file already in the
        output directory, do not refetch it (True) or force refecth it (False).
    :type use_cache: bool

    :returns: File path if success to download, else None
    :rtype: str
    """
    if filename is None:
        filename = get_filename(url)
    LOGGER.info('Download file %s from %s' % (filename, url))
    file_path = os.path.join(output_directory, filename)
    if os.path.exists(file_path) and use_cache:
        LOGGER.info('File %s exists, not downloading' % file_path)
        return file_path

    # Set Proxy in webpage
    proxy = get_proxy()
    network_manager = QNetworkAccessManager()
    if proxy is not None:
        network_manager.setProxy(proxy)

    # Download Process
    # noinspection PyTypeChecker
    downloader = FileDownloader(network_manager, url, file_path)
    try:
        result = downloader.download()
    except IOError as ex:
        raise DownloadException(ex)

    if result[0] is not True:
        _, error_message = result
        raise DownloadException(error_message)

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
    url_prefix = BASE_URL + 'esio/'
    try:
        html = urllib.urlopen(download_page_url)
        download_page_soup = BeautifulSoup(html)
        urls = download_page_soup.find_all('a')
        for url in urls:
            full_url = url['href']
            if full_url[0:2] == './':
                full_url = full_url[2:]
            full_url = url_prefix + full_url
            download_urls.append(str(full_url))
        return download_urls
    except IOError as e:
        raise ParseException(e)


def download_sg_diagram(
        db_manager, sg_code, province_name, output_directory, callback=None):
    """Download sg diagram using sg_code and put it under output_directory.

    :param db_manager: A database manager
    :type db_manager: DatabaseManager

    :param sg_code: Surveyor General code.
    :type sg_code: str

    :param province_name: Province name.
    :type province_name: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str

    :param callback: A function to all to indicate progress. The function
        should accept params 'current' (int) and 'maximum' (int). Defaults to
        None.
    :type callback: function

    :returns: A report listing which files were downloaded and their
        download failure or success.
    :rtype: str
    """
    if callback is None:
        callback = print_progress_callback

    report = 'Downloading documents for %s in %s\n' % (sg_code, province_name)

    try:
        download_page = construct_url(db_manager, sg_code, province_name)
    except (InvalidSGCodeException,
            DatabaseException,
            UrlException,
            NotInSouthAfricaException) as e:
        report += (
            'Failed: Downloading SG code %s for province %s because of %s\n' %
            (sg_code, province_name, e.reason))
        return report
    try:
        download_links = parse_download_page(download_page)
    except ParseException as e:
        report += (
            'Failed: Downloading SG code %s for province %s because of %s\n' %
            (sg_code, province_name, e.reason))
        return report

    output_directory = os.path.join(output_directory, sg_code)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    count = 0
    total = len(download_links)
    if total == 0:
        report += 'No documents found for %s in %s' % (sg_code, province_name)

    for download_link in download_links:
        count += 1
        message = ('[%s - %s] Downloading file %s of %s' % (
            sg_code, province_name, count, total))
        callback(count, total, message)
        try:
            file_path = download_from_url(download_link, output_directory)
            if file_path is not None:
                report += 'Success: File %i of %i : %s saved to %s\n' % (
                    count, total, download_link, file_path)
            else:
                report += 'Failed: File %i of %i : %s \n' % (
                    count, total, download_link)
        except DownloadException as e:
            message = 'Failed to download %s for %s in %s because %s' % (
                download_link, sg_code, province_name, e.reason)
            LOGGER.exception(message)
            report += 'Failed: File %i of %i : %s \n' % (
                count, total, download_link)

    message = 'Downloads completed for %s in %s' % (sg_code, province_name)
    callback(count, total, message)
    return report


def get_spatial_index(data_provider):
    """Create spatial index from a data provider.

    :param data_provider: QGIS data provider name .e.g.'ogr'.
    :type data_provider: str
    """
    qgs_feature = QgsFeature()
    index = QgsSpatialIndex()
    # noinspection PyUnresolvedReferences
    qgs_features = data_provider.getFeatures()
    while qgs_features.nextFeature(qgs_feature):
        index.insertFeature(qgs_feature)
    return index


def province_for_point(db_manager, centroid):
    """Determine which province a point falls into.

    Typically you will get the centroid of a parcel or a click position
    on the map and then call this function with it.

    :param db_manager: A database manager
    :type db_manager: DatabaseManager

    :param centroid: Point at which lookup should occur.
    :type centroid: QgsPoint

    :returns: Province Name
    :rtype: str
    """
    centroid_wkt = centroid.wellKnownText()

    query = "SELECT province FROM provinces WHERE "
    query += "Within(GeomFromText('%s'), Geometry)" % centroid_wkt

    row = db_manager.fetch_one(query)

    if row is None:
        return None
    else:
        return row[0]


def map_sg_codes_to_provinces(
        db_manager,
        site_layer,
        parcels_layer,
        sg_code_field,
        all_features=False):
    """Obtains sg codes from target layer.

    :param db_manager: A database manager
    :type db_manager: DatabaseManager

    :param site_layer: The target layer.
    :type site_layer: QgsVectorLayer

    :param parcels_layer: Vector layer that has sg code in one of its fields.
    :type parcels_layer: QgsVectorLayer

    :param sg_code_field: Name of the field that contains sg code
    :type sg_code_field: str

    :param all_features: If True select all features, else only the selected
        ones.
    :type all_features: bool

    :returns: Dict where key is sg code and value is province name
    :rtype: dict
    """
    intersecting_parcels = []
    sg_code_provinces = {}

    sg_code_index = parcels_layer.fieldNameIndex(sg_code_field)
    if sg_code_index == -1:
        message = 'Field "%s" not found' % sg_code_field
        raise Exception(message)

    parcels_provider = parcels_layer.dataProvider()
    site_crs = site_layer.crs()
    parcel_crs = parcels_layer.crs()
    province_crs = QgsCoordinateReferenceSystem(4326)

    site_parcel_transformer = QgsCoordinateTransform(site_crs, parcel_crs)

    province_transformer = QgsCoordinateTransform(parcel_crs, province_crs)

    if not all_features:
        selected_features = site_layer.selectedFeatures()
    else:
        selected_features = site_layer.getFeatures()
    for selected_feature in selected_features:
        for feature in parcels_provider.getFeatures():
            geometry = selected_feature.geometry()
            feature_geometry = feature.geometry()

            geometry.transform(site_parcel_transformer)

            intersect = geometry.intersects(feature_geometry)
            if intersect:
                intersecting_parcels.append(feature.id())

    feature = QgsFeature()
    for intersect in intersecting_parcels:
        index = int(intersect)
        request = QgsFeatureRequest()
        request.setFilterFid(index)
        parcels_provider.getFeatures(request).nextFeature(feature)
        sg_code = feature.attributes()[sg_code_index]
        geometry = feature.geometry()
        centroid = geometry.centroid().asPoint()
        centroid = province_transformer.transform(centroid)
        # noinspection PyTypeChecker
        province_name = province_for_point(db_manager, centroid)
        sg_code_provinces[sg_code] = province_name

    return sg_code_provinces


def print_progress_callback(current, maximum, message=None):
    """GUI based callback implementation for showing progress.

    :param current: Current progress.
    :type current: int

    :param maximum: Maximum range (point at which task is complete.
    :type maximum: int

    :param message: Optional message to display in the progress bar
    :type message: str, QString
    """
    print ('%d of %d' + str(message)) % (current, maximum)


def download_sg_diagrams(
        db_manager,
        site_layer,
        diagram_layer,
        sg_code_field,
        output_directory,
        all_features=False,
        callback=None):
    """Downloads all SG Diagrams.

    :param db_manager: A database manager
    :type db_manager: DatabaseManager

    :param site_layer: The target layer.
    :type site_layer: QgsVectorLayer

    :param diagram_layer: Vector layer that has sg code in its field.
    :type diagram_layer: QgsVectorLayer

    :param sg_code_field: Name of the field that contains sg code
    :type sg_code_field: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str

    :param all_features: If True select all features, else only the selected
        ones.
    :type all_features: bool

    :param callback: A function to all to indicate progress. The function
        should accept params 'current' (int) and 'maximum' (int). Defaults to
        None.
    :type callback: function

    :returns: A report listing which files were downloaded and their
        download failure or success.
    :rtype: str
    """
    if callback is None:
        callback = print_progress_callback

    sg_codes_and_provinces = map_sg_codes_to_provinces(
        db_manager, site_layer, diagram_layer, sg_code_field, all_features)
    maximum = len(sg_codes_and_provinces)
    current = 0
    report = ''
    for sg_code, province in sg_codes_and_provinces.iteritems():
        current += 1
        message = 'Downloading SG Code %s from %s' % (sg_code, province)
        callback(current, maximum, message)
        try:
            report += download_sg_diagram(
                db_manager,
                sg_code,
                province,
                output_directory,
                callback)
        except Exception, e:
            report += 'Failed to download %s %s %s\n' % (sg_code, province, e)
            LOGGER.exception(e)

    return report


def point_to_rectangle(point):
    """Create a small rectangle by buffering a point.

    Useful in cases where you want to use a point as the basis for a
    QgsFeatureRequest rectangle filter.

    :param point: Point that will be buffered.
    :type point: qgis.core.QgsPoint

    :returns: A rectangle made by creating a very tiny buffer around the
        point.
    :rtype: QgsRectangle
    """
    # arbitrarily small number
    threshold = 0.00000000001
    x_minimum = point.x() - threshold
    y_minimum = point.y() - threshold
    x_maximum = point.x() + threshold
    y_maximum = point.y() + threshold
    rectangle = QgsRectangle(
        x_minimum,
        y_minimum,
        x_maximum,
        y_maximum)
    return rectangle


def diagram_directory():
    """Get the output path for writing diagrams to.

    :return: The path to the parent diagram dir. Actual diagrams should
        be written to subdirectories of this path.
    :rtype: str
    """
    settings = QSettings()
    default_path = os.path.join(os.path.expanduser('~'), 'sg-diagrams')
    output_path = settings.value(
        'sg-diagram-downloader/output_directory', default_path)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    return output_path
