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

__author__ = "ismail@kartoza.com"
__revision__ = "$Format:%H$"
__date__ = "30/05/2014"
__copyright__ = ""

import os
import re

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsMessageLog,
    QgsProject,
    QgsRectangle,
    QgsSpatialIndex,
    Qgis,
)

from qgis.PyQt.QtCore import QSettings, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import QgsBlockingNetworkRequest

from urllib.parse import urlparse
from .definitions import BASE_URL
from .file_downloader import FileDownloader
from .sg_exceptions import (
    DownloadException,
    DatabaseException,
    UrlException,
    InvalidSGCodeException,
    ParseException,
    NotInSouthAfricaException,
)
from .custom_logging import LOGGER

# pylint: disable=F0401
# noinspection PyUnresolvedReferences
from bs4 import BeautifulSoup

TAG = "SG-Downloader"


def log_message(message, level=Qgis.Info):
    """Log a message to QGIS message log and to the log file.

    :param message: The message to log.
    :type message: str

    :param level: The log level (Qgis.Info, Qgis.Warning, Qgis.Critical).
    :type level: Qgis.MessageLevel
    """
    # Log to QGIS message log
    QgsMessageLog.logMessage(message, TAG, level)

    # Also log to file via the Python logger
    if level == Qgis.Critical:
        LOGGER.error(message)
    elif level == Qgis.Warning:
        LOGGER.warning(message)
    else:
        LOGGER.info(message)


# pylint: enable=F0401

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SG_DIAGRAM_SQLITE3 = os.path.join(DATA_DIR, "sg_diagrams.gpkg")
PROVINCES_LAYER_PATH = SG_DIAGRAM_SQLITE3 + "|layername=provinces"
PROVINCE_NAMES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "Northern Cape",
    "North West",
    "Western Cape",
]


def write_log(log, log_path):
    """Write log to file.

    :param log: Log text to write
    :type log: str

    :param log_path: Log file path.
    :type log_path: str

    :raises IOError: If file cannot be written
    """
    try:
        with open(log_path, "a") as f:
            f.write(log)
    except IOError as e:
        LOGGER.error("Failed to write log to %s: %s" % (log_path, str(e)))
        raise


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
            "province='%s' AND region_code='%s'" % (province, region_code)
        )

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
    if type(value) == str:
        value = str(value)

    # False if value is not a string or value is not True
    if type(value) != str or not value:
        return False
    # Regex to check for the presence of an SG 21 digit code e.g.
    # C01900000000026300000
    # I did a quick scan of all the unique starting letters from
    # Gavin's test dataset and came up with OBCFNT
    prefixes = "OBCFNT"
    sg_code_regex_string = "^[%s][A-Z0-9]{4}[0-9]{16}$" % prefixes
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
    log_message("Constructing URL for sg_code=%s, province=%s" % (sg_code, province_name))
    LOGGER.info("Constructing url for %s %s" % (sg_code, province_name))

    if not is_valid_sg_code(sg_code):
        log_message("Invalid SG code: %s" % sg_code, Qgis.Warning)
        raise InvalidSGCodeException

    if sg_code is None or province_name is None:
        log_message("Missing sg_code or province_name", Qgis.Warning)
        raise UrlException()

    if province_name not in PROVINCE_NAMES:
        log_message('Province "%s" not in valid provinces: %s' % (province_name, PROVINCE_NAMES), Qgis.Warning)
        raise NotInSouthAfricaException

    base_url = BASE_URL + "esio/listdocument.jsp?"
    reg_division = sg_code[:8]
    log_message("Regional division: %s" % reg_division)

    try:
        record = get_office(db_manager, reg_division, province_name)
        log_message("Office record: %s" % str(record))
    except DatabaseException as e:
        log_message("Database error getting office: %s" % str(e), Qgis.Critical)
        raise DatabaseException

    if not record:
        log_message("No office record found for region=%s, province=%s" % (reg_division, province_name), Qgis.Warning)
        raise DatabaseException

    office, office_number, typology = record
    log_message("Office: %s, Office Number: %s, Typology: %s" % (office, office_number, typology))

    erf = sg_code[8:16]
    portion = sg_code[16:]
    url = base_url + "regDivision=" + reg_division
    url += "&office=" + office
    url += "&Noffice=" + office_number
    url += "&Erf=" + erf
    url += "&Portion=" + portion

    log_message("Constructed SG diagram URL: %s" % url)
    LOGGER.info("Constructed URL: %s" % url)
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
    file_name = url_query.split("&")[0].split("/")[-1]

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
    LOGGER.info("Download file %s from %s" % (filename, url))
    file_path = os.path.join(output_directory, filename)
    if os.path.exists(file_path) and use_cache:
        LOGGER.info("File %s exists, not downloading" % file_path)
        return file_path

    # Download Process (uses QgsBlockingNetworkRequest internally)
    downloader = FileDownloader(None, url, file_path)
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


def fetch_url_content(url):
    """Fetch content from a URL using QGIS networking.

    :param url: URL to fetch.
    :type url: str

    :returns: Response content as bytes.
    :rtype: bytes

    :raises: ParseException if the request fails.
    """
    LOGGER.info("fetch_url_content: Fetching URL: %s" % url)
    request = QNetworkRequest(QUrl(url))
    blocking_request = QgsBlockingNetworkRequest()

    error_code = blocking_request.get(request)
    LOGGER.info("fetch_url_content: Request completed with error_code: %s" % error_code)

    if error_code != QgsBlockingNetworkRequest.NoError:
        error_msg = blocking_request.errorMessage()
        LOGGER.error("fetch_url_content: Request failed: %s" % error_msg)
        raise ParseException(error_msg)

    reply = blocking_request.reply()
    content = reply.content().data()
    LOGGER.info("fetch_url_content: Received %d bytes" % len(content))
    return content


def parse_download_page(download_page_url):
    """Parse download_page_url to get list of download links.

    :param download_page_url: Url to download page.
    :type download_page_url: str

    :returns: List of urls to download the diagrams.
    :rtype: list

    :raises ParseException: If the page cannot be fetched or parsed.
    """
    log_message("Parsing download page: %s" % download_page_url)
    LOGGER.info("Parsing download page: %s" % download_page_url)

    download_urls = []
    url_prefix = BASE_URL + "esio/"
    try:
        html = fetch_url_content(download_page_url)
        download_page_soup = BeautifulSoup(html, "html.parser")
        urls = download_page_soup.find_all("a")
        log_message("Found %d links on download page" % len(urls))

        for url in urls:
            full_url = url["href"]
            if full_url[0:2] == "./":
                full_url = full_url[2:]
            full_url = url_prefix + full_url
            download_urls.append(str(full_url))
            log_message("Found diagram download URL: %s" % full_url)
            LOGGER.debug("Parsed download URL: %s" % full_url)

        log_message("Total download URLs found: %d" % len(download_urls))
        LOGGER.info("Found %d download URLs" % len(download_urls))
        return download_urls
    except ParseException:
        raise
    except KeyError as e:
        log_message("HTML parsing error - missing href attribute: %s" % str(e), Qgis.Warning)
        raise ParseException("Invalid HTML structure in download page")
    except Exception as e:
        log_message("Error parsing download page: %s" % str(e), Qgis.Critical)
        LOGGER.exception("Failed to parse download page")
        raise ParseException(str(e))


def download_sg_diagram(db_manager, sg_code, province_name, output_directory, callback=None):
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

    report = "Downloading documents for %s in %s\n" % (sg_code, province_name)

    try:
        download_page = construct_url(db_manager, sg_code, province_name)
        report += download_page
    except (InvalidSGCodeException, DatabaseException, UrlException, NotInSouthAfricaException) as e:
        report += "\nFailed: Downloading SG code %s for province %s because of %s\n" % (
            sg_code,
            province_name,
            e.reason,
        )
        return report
    try:
        download_links = parse_download_page(download_page)
    except ParseException as e:
        report += "Failed: Downloading SG code %s for province %s because of %s\n" % (sg_code, province_name, e.reason)
        return report

    output_directory = os.path.join(output_directory, sg_code)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    count = 0
    total = len(download_links)
    if total == 0:
        report += "No documents found for %s in %s" % (sg_code, province_name)

    for download_link in download_links:
        count += 1
        message = "[%s - %s] Downloading file %s of %s" % (sg_code, province_name, count, total)
        callback(count, total, message)
        try:
            file_path = download_from_url(download_link, output_directory)
            if file_path is not None:
                report += "Success: File %i of %i : %s saved to %s\n" % (count, total, download_link, file_path)
            else:
                report += "Failed: File %i of %i : %s \n" % (count, total, download_link)
        except DownloadException as e:
            message = "Failed to download %s for %s in %s because %s" % (
                download_link,
                sg_code,
                province_name,
                e.reason,
            )
            LOGGER.exception(message)
            report += "Failed: File %i of %i : %s \n" % (count, total, download_link)

    message = "Downloads completed for %s in %s" % (sg_code, province_name)
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


# Cache for provinces layer to avoid reloading for every point lookup
_provinces_layer_cache = {"layer": None, "checked": False, "valid": False}


def _get_provinces_layer():
    """Get the provinces layer, using cache to avoid repeated loading attempts.

    :returns: Tuple of (layer, is_valid)
    :rtype: tuple
    """
    from qgis.core import QgsVectorLayer

    # Return cached result if already checked
    if _provinces_layer_cache["checked"]:
        return _provinces_layer_cache["layer"], _provinces_layer_cache["valid"]

    _provinces_layer_cache["checked"] = True

    # First check if the GeoPackage file exists
    if not os.path.exists(SG_DIAGRAM_SQLITE3):
        log_message("GeoPackage not found at %s" % SG_DIAGRAM_SQLITE3, Qgis.Warning)
        return None, False

    # Check if provinces layer exists in the GeoPackage using sqlite
    # This avoids GDAL/OGR errors from trying to load an invalid layer
    try:
        import sqlite3

        conn = sqlite3.connect(SG_DIAGRAM_SQLITE3)
        cursor = conn.cursor()
        cursor.execute("SELECT column_name FROM gpkg_geometry_columns WHERE table_name='provinces'")
        row = cursor.fetchone()
        conn.close()

        if not row:
            log_message("No provinces layer found in GeoPackage", Qgis.Info)
            return None, False

        geom_column = row[0]
        if geom_column != "geom":
            log_message("Provinces layer has wrong geometry column: %s (expected geom)" % geom_column, Qgis.Warning)
            return None, False

    except Exception as e:
        log_message("Error checking GeoPackage structure: %s" % str(e), Qgis.Warning)
        return None, False

    # Now safe to load the layer
    provinces_layer = QgsVectorLayer(PROVINCES_LAYER_PATH, "provinces", "ogr")

    if not provinces_layer.isValid():
        log_message("Could not load provinces layer from %s" % PROVINCES_LAYER_PATH, Qgis.Warning)
        return None, False

    log_message("Provinces layer loaded with %d features" % provinces_layer.featureCount())
    _provinces_layer_cache["layer"] = provinces_layer
    _provinces_layer_cache["valid"] = True
    return provinces_layer, True


def province_for_point(db_manager, centroid):
    """Determine which province a point falls into.

    Typically you will get the centroid of a parcel or a click position
    on the map and then call this function with it.

    :param db_manager: A database manager (used as fallback for province lookup)
    :type db_manager: DatabaseManager

    :param centroid: Point at which lookup should occur.
    :type centroid: QgsPointXY

    :returns: Province Name
    :rtype: str
    """
    from qgis.core import QgsPointXY, QgsGeometry

    # Get cached provinces layer
    provinces_layer, is_valid = _get_provinces_layer()

    if not is_valid:
        # Fallback: use coordinate-based province lookup
        return _province_for_point_db_fallback(db_manager, centroid)

    # Create a point geometry for the centroid
    if isinstance(centroid, QgsPointXY):
        point_geom = QgsGeometry.fromPointXY(centroid)
    else:
        # Handle QgsPoint (3D) by converting to QgsPointXY
        point_geom = QgsGeometry.fromPointXY(QgsPointXY(centroid.x(), centroid.y()))

    # Find which province contains the point
    for feature in provinces_layer.getFeatures():
        if feature.geometry().contains(point_geom):
            # Try common field names for province
            for field_name in ["province", "PROVINCE", "name", "NAME", "provname", "PROVNAME"]:
                idx = provinces_layer.fields().indexFromName(field_name)
                if idx >= 0:
                    return feature.attributes()[idx]
            # If no known field found, return the first attribute
            if feature.attributes():
                return str(feature.attributes()[0])

    return None


def _province_for_point_db_fallback(db_manager, centroid):
    """Fallback method to determine province using simple bounding box lookup.

    This is used when the provinces vector layer cannot be loaded.
    Uses a simple coordinate-based lookup based on known SA province boundaries.

    :param db_manager: Database manager (not used in this simple implementation)
    :param centroid: Point to lookup
    :returns: Province name or None
    """
    from qgis.core import QgsPointXY

    # Get coordinates
    if isinstance(centroid, QgsPointXY):
        x, y = centroid.x(), centroid.y()
    else:
        x, y = centroid.x(), centroid.y()

    # Simple bounding box based province detection for South Africa
    # These are approximate boundaries in EPSG:4326 (WGS84)
    # This is a rough fallback - proper spatial lookup is preferred
    province_bounds = {
        "Western Cape": (17.5, -34.5, 23.5, -31.0),
        "Eastern Cape": (23.5, -34.0, 30.5, -30.5),
        "Northern Cape": (16.5, -32.0, 24.5, -26.5),
        "Free State": (24.0, -30.5, 30.0, -26.5),
        "KwaZulu-Natal": (28.5, -31.5, 33.0, -27.0),
        "Gauteng": (27.0, -26.5, 29.0, -25.0),
        "Mpumalanga": (28.5, -27.0, 32.0, -24.0),
        "Limpopo": (26.5, -25.0, 31.5, -22.0),
        "North West": (22.5, -28.0, 28.0, -24.5),
    }

    for province, (min_x, min_y, max_x, max_y) in province_bounds.items():
        if min_x <= x <= max_x and min_y <= y <= max_y:
            return province

    return None


def map_sg_codes_to_provinces(db_manager, site_layer, parcels_layer, sg_code_field, all_features=False):
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

    LOGGER.info(
        "map_sg_codes_to_provinces called with sg_code_field=%s, all_features=%s" % (sg_code_field, all_features)
    )
    LOGGER.info(
        "site_layer: %s, parcels_layer: %s"
        % (site_layer.name() if site_layer else None, parcels_layer.name() if parcels_layer else None)
    )

    sg_code_index = parcels_layer.fields().indexFromName(sg_code_field)
    if sg_code_index == -1:
        message = 'Field "%s" not found' % sg_code_field
        raise Exception(message)

    parcels_provider = parcels_layer.dataProvider()
    site_crs = site_layer.crs()
    parcel_crs = parcels_layer.crs()
    province_crs = QgsCoordinateReferenceSystem(4326)

    site_parcel_transformer = QgsCoordinateTransform(site_crs, parcel_crs, QgsProject.instance())

    province_transformer = QgsCoordinateTransform(parcel_crs, province_crs, QgsProject.instance())

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
    if message is None:
        message = ""
    print("%d of %d %s" % (current, maximum, message))


def download_sg_diagrams(
    db_manager, site_layer, diagram_layer, sg_code_field, output_directory, all_features=False, callback=None
):
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

    LOGGER.info("Starting download_sg_diagrams")
    sg_codes_and_provinces = map_sg_codes_to_provinces(
        db_manager, site_layer, diagram_layer, sg_code_field, all_features
    )
    LOGGER.info("Found %d SG codes to download: %s" % (len(sg_codes_and_provinces), sg_codes_and_provinces))
    maximum = len(sg_codes_and_provinces)
    current = 0
    report = ""
    for sg_code, province in sg_codes_and_provinces.items():
        current += 1
        message = "Downloading SG Code %s from %s" % (sg_code, province)
        callback(current, maximum, message)
        try:
            report += download_sg_diagram(db_manager, sg_code, province, output_directory, callback)
        except Exception as e:
            report += "Failed to download %s %s %s\n" % (sg_code, province, e)
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
    rectangle = QgsRectangle(x_minimum, y_minimum, x_maximum, y_maximum)
    return rectangle


def diagram_directory():
    """Get the output path for writing diagrams to.

    :return: The path to the parent diagram dir. Actual diagrams should
        be written to subdirectories of this path.
    :rtype: str
    """
    settings = QSettings()
    default_path = os.path.join(os.path.expanduser("~"), "sg-diagrams")
    output_path = settings.value("sg-diagram-downloader/output_directory", default_path)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    return output_path
