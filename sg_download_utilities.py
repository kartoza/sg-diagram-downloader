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

import  os

from qgis.core import (
    QGis,
    QgsField,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsMapLayer,
    QgsRectangle,
    QgsFeatureRequest,
    QgsSpatialIndex,
    QgsMapLayerRegistry)

import pycurl


def construct_url(sg_code=None):
    """Construct url to download sg diagram.

    :param sg_code: SG code.
    :type sg_code: str

    :returns: URL to download sg diagram.
    :rtype: str
    """
    if sg_code is None:
        return (
            'http://csg.dla.gov.za/esio/listdocument.jsp?regDivision=C0160013'
            '&Noffice=2&Erf=1234&Portion=0&FarmName=')

    base_url = 'http://csg.dla.gov.za/esio/listdocument.jsp?'
    reg_division = sg_code[:8]
    office = ''
    office_number = ''
    erf = sg_code[8:16]
    portion = sg_code[16:]
    url = base_url + 'regDivision=' + reg_division
    url += '&office=' + office
    url += '&Noffice=' + office_number
    url += '&Erf=' + erf
    url += '&Portion' + portion
    return url


def download_from_url(url, output_directory, file_name='random.tiff'):
    """Download file from a url and put it under output_directory.

    :param url: Url that gives response.
    :type url: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str
    """
    file_name = os.path.join(output_directory, file_name)
    fp = open(file_name, 'wb')
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.CONNECTTIMEOUT, 60)
    curl.setopt(pycurl.FOLLOWLOCATION, True)
    curl.setopt(pycurl.NOBODY, False)

    curl.setopt(pycurl.WRITEDATA, fp)
    curl.perform()

    curl.close()
    fp.close()


def download_sg_diagram(sg_code, output_directory):
    """Download sg diagram using sg_code and put it under output_directory.

    :param sg_code: Surveyor General code.
    :type sg_code: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str
    """
    download_page = construct_url(sg_code)
    download_link = download_page
    output_directory = os.path.join(output_directory, sg_code)
    download_from_url(download_link, output_directory)


def get_spatial_index(data_provider):
    """Create spatial index from a data provider."""
    qgs_feature = QgsFeature()
    index = QgsSpatialIndex()
    qgs_features = data_provider.getFeatures()
    while qgs_features.nextFeature(qgs_feature):
        index.insertFeature(qgs_feature)
    return index


def get_sg_codes(target_layer, diagram_layer, sg_code_field):
    """Obtains sg codes from target layer.

    :param target_layer: The target layer.
    :type target_layer: QgsVectorLayer

    :param diagram_layer: Vector layer that has sg code in its field.
    :type diagram_layer: QgsVectorLayer

    :param sg_code_field: Name of the field that contains sg code
    :type sg_code_field: str

    :returns: List of sg code
    :rtype: list
    """
    intersects = []
    sg_codes = []
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
        sg_codes.append(sg_code)

    return set(sg_codes)


def download_sg_diagrams(
        target_layer, diagram_layer, sg_code_field, output_directory):
    """Downloads all SG Diagrams.

    :param target_layer: The target layer.
    :type target_layer: QgsVectorLayer

    :param diagram_layer: Vector layer that has sg code in its field.
    :type diagram_layer: QgsVectorLayer

    :param sg_code_field: Name of the field that contains sg code
    :type sg_code_field: str

    :param output_directory: Directory to put the diagram.
    :type output_directory: str
    """

    sg_codes = get_sg_codes(target_layer, diagram_layer, sg_code_field)
    for sg_code in sg_codes:
        print sg_code
        # download_sg_diagram(sg_code, output_directory)