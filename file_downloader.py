# coding=utf-8
"""
InaSAFE Disaster risk assessment tool developed by AusAid -
  **IS Utilities implementation.**

Contact : ole.moller.nielsen@gmail.com

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'akbargumbira@gmail.com'
__revision__ = '$Format:%H$'
__date__ = '16/03/2014'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')


from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import QgsBlockingNetworkRequest


class FileDownloader:
    """The blueprint for downloading file from url using QGIS networking."""

    def __init__(self, manager, url, output_path, progress_dialog=None):
        """Constructor of the class.

        :param manager: QgsNetworkAccessManager instance (kept for API compatibility).
        :type manager: QgsNetworkAccessManager

        :param url: URL of file.
        :type url: str

        :param output_path: Output path.
        :type output_path: str

        :param progress_dialog: Progress dialog widget (not used with blocking request).
        :type progress_dialog: QWidget

        """
        self.manager = manager  # kept for API compatibility
        self.url = url
        self.output_path = output_path
        self.progress_dialog = progress_dialog

    def download(self):
        """Download the file using QgsBlockingNetworkRequest.

        :returns: Tuple of (success, error_message). Success is True if download
            succeeded, otherwise False with an error message.
        :rtype: tuple

        :raises: IOError - when cannot create output_path
        """
        request = QNetworkRequest(QUrl(self.url))
        blocking_request = QgsBlockingNetworkRequest()

        error_code = blocking_request.get(request)

        if error_code != QgsBlockingNetworkRequest.NoError:
            error_msg = blocking_request.errorMessage()
            return False, error_msg

        reply = blocking_request.reply()
        content = reply.content()

        try:
            with open(self.output_path, 'wb') as f:
                f.write(content.data())
        except IOError as e:
            raise IOError(str(e))

        return True, None
