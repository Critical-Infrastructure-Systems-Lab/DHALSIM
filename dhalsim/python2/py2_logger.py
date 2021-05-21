import logging
import sys


def get_logger(logging_level):
    """
    Gets a python2 logger, sets the format and logging level

    :param logging_level: logging level of logger
    """
    switcher = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
                'error': logging.ERROR, 'critical': logging.CRITICAL}

    log_level = switcher.get(logging_level)
    py2_logger = logging.getLogger('py2_logger')
    # Configure logger level
    py2_handler = logging.StreamHandler(stream=sys.stdout)
    logging_format = logging.Formatter('%(asctime)s - %(levelname)s @ %(filename)s: %(message)s')
    py2_handler.setFormatter(logging_format)
    py2_logger.addHandler(py2_handler)
    # Set level of logger
    py2_logger.setLevel(log_level)
    return py2_logger
