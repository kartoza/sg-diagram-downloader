# coding=utf-8
"""
Custom logging setup.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

import os
import sys
import logging
from datetime import date
import getpass
from tempfile import mkstemp, gettempdir

third_party_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'third_party'))
if third_party_path not in sys.path:
    sys.path.append(third_party_path)

# Sentry imports are optional - only import if Sentry is enabled
SENTRY_AVAILABLE = False
SentryHandler = None
Client = None

if not os.environ.get('SG_DOWNLOADER_SENTRY_DISABLED'):
    try:
        # pylint: disable=F0401
        # noinspection PyUnresolvedReferences
        from raven.handlers.logging import SentryHandler  # noqa
        # noinspection PyUnresolvedReferences
        from raven import Client  # noqa
        # pylint: enable=F0401
        SENTRY_AVAILABLE = True
    except ImportError:
        pass

LOGGER = logging.getLogger('SG-Downloader')

__author__ = 'tim@kartoza.com'
__revision__ = '$Format:%H$'
__date__ = '29/01/2011'
__copyright__ = 'Copyright 2012, Australia Indonesia Facility for '
__copyright__ += 'Disaster Reduction'


def log_file_path():
    """Get SG Downloader log file path.

    :return: Log file path.
    :rtype: str
    """
    try:
        log_temp_dir = temp_dir('logs')
        path = os.path.join(log_temp_dir, 'sg-diagram-downloader.log')
        return path
    except Exception:
        # Fallback to simple temp directory if custom temp_dir fails
        return os.path.join(gettempdir(), 'sg-diagram-downloader.log')


class QgsLogHandler(logging.Handler):
    """A logging handler that will log messages to the QGIS logging console."""

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level=level)

    def emit(self, record):
        """Try to log the message to QGIS if available, otherwise do nothing.

        :param record: logging record containing the info to be logged.
        :type record: logging.LogRecord
        """
        try:
            from qgis.core import QgsMessageLog, Qgis
            # Format the message
            msg = self.format(record)

            # Map Python log levels to QGIS log levels
            if record.levelno >= logging.ERROR:
                level = Qgis.Critical
            elif record.levelno >= logging.WARNING:
                level = Qgis.Warning
            else:
                level = Qgis.Info

            QgsMessageLog.logMessage(msg, 'SG Diagram Downloader', level=level)

        except ImportError:
            # Not running in QGIS environment
            pass
        except Exception:
            # Don't let logging errors crash the application
            pass


def add_logging_handler_once(logger, handler):
    """A helper to add a handler to a logger, ensuring there are no duplicates.

    :param logger: Logger that should have a handler added.
    :type logger: logging.logger

    :param handler: Handler instance to be added. It will not be added if an
        instance of that Handler subclass already exists.
    :type handler: logging.Handler

    :returns: True if the logging handler was added, otherwise False.
    :rtype: bool
    """
    class_name = handler.__class__.__name__
    for existing_handler in logger.handlers:
        if existing_handler.__class__.__name__ == class_name:
            return False

    logger.addHandler(handler)
    return True


def setup_logger(sentry_url=None, log_file=None):
    """Run once when the module is loaded and enable logging.

    :param sentry_url: Optional url to sentry api for remote logging.
        Consult your sentry instance for the client instance url.
    :type sentry_url: str

    :param log_file: Optional full path to a file to write logs to.
    :type log_file: str

    Borrowed heavily from this:
    http://docs.python.org/howto/logging-cookbook.html

    Use this to first initialise the logger in your __init__.py::

       import custom_logging
       custom_logging.setup_logger('http://path to sentry')

    You would typically only need to do the above once ever as the
    safe model is initialised early and will set up the logger
    globally so it is available to all packages / subpackages as
    shown below.

    In a module that wants to do logging then use this example as
    a guide to get the initialised logger instance::

       # The LOGGER is initialised in sg_utilities.py by init
       import logging
       LOGGER = logging.getLogger('QGIS')

    Now to log a message do::

       LOGGER.debug('Some debug message')

    .. note:: The file logs are written to the user tmp dir e.g.:
       /tmp/23-08-2012/timlinux/logs/qgis.log

    """
    try:
        logger = logging.getLogger('QGIS')
        logger.setLevel(logging.DEBUG)
        default_handler_level = logging.DEBUG

        # create formatter that will be added to the handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Create file handler with fallback
        try:
            path = log_file if log_file else log_file_path()
            file_handler = logging.FileHandler(path)
            file_handler.setLevel(default_handler_level)
            file_handler.setFormatter(formatter)
            add_logging_handler_once(logger, file_handler)
        except Exception:
            # If file logging fails, continue without it
            pass

        # create console handler with a higher log level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        add_logging_handler_once(logger, console_handler)

        # QGIS log handler
        qgis_handler = QgsLogHandler()
        qgis_handler.setFormatter(formatter)
        add_logging_handler_once(logger, qgis_handler)

        # Sentry handler - this is optional
        # It will only log if raven is available and Sentry is not disabled.
        # To disable Sentry, set the environment variable:
        #   SG_DOWNLOADER_SENTRY_DISABLED=1
        # This is useful for debugging to avoid hangs from Sentry connections.
        if SENTRY_AVAILABLE and sentry_url:
            try:
                client = Client(sentry_url)
                sentry_handler = SentryHandler(client)
                sentry_handler.setFormatter(formatter)
                sentry_handler.setLevel(logging.ERROR)
                if add_logging_handler_once(logger, sentry_handler):
                    logger.debug('Sentry logging enabled')
            except Exception as e:
                logger.debug('Failed to initialize Sentry: %s' % str(e))
        else:
            logger.debug('Sentry logging disabled')

    except Exception:
        # If logger setup fails completely, don't crash the plugin
        pass


def temp_dir(sub_dir='work'):
    r"""Obtain the temporary working directory for the operating system.

    :param sub_dir: Optional argument which will cause an additional
        subdirectory to be created.
    :type sub_dir: str

    :returns: Path to the temporary folder placed in the system temp dir.
    :rtype: str
    """
    try:
        user = getpass.getuser().replace(' ', '_')
    except Exception:
        user = 'unknown'

    current_date = date.today()
    date_string = current_date.isoformat()

    # Use system temp directory
    try:
        handle, filename = mkstemp()
        os.close(handle)
        new_directory = os.path.dirname(filename)
        os.remove(filename)
    except Exception:
        new_directory = gettempdir()

    temp_path = os.path.join(
        new_directory, date_string, user, sub_dir)

    if not os.path.exists(temp_path):
        try:
            # Ensure that the dir is world writable
            # Umask sets the new mask and returns the old
            old_mask = os.umask(0o000)
            os.makedirs(temp_path, 0o777)
            # Reinstate the old mask for tmp
            os.umask(old_mask)
        except Exception:
            # If we can't create the directory, use system temp
            temp_path = gettempdir()

    return temp_path
