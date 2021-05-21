import logging
import sys


def get_logger(logging_level: str):
    """
    Gets a python3 logger, sets the format and logging level

    :param logging_level: logging level of logger
    """
    switcher = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
                'error': logging.ERROR, 'critical': logging.CRITICAL}

    log_level = switcher.get(logging_level)
    py3_logger = logging.getLogger('py3_logger')
    # Configure logger level
    py3_handler = logging.StreamHandler(stream=sys.stdout)
    logging_format = logging.Formatter('%(asctime)s - %(levelname)s @ %(filename)s: %(message)s')
    py3_handler.setFormatter(logging_format)
    py3_logger.addHandler(py3_handler)
    # Set level of logger
    py3_logger.setLevel(log_level)
    return py3_logger
