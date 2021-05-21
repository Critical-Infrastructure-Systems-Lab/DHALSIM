import logging
import sys


def get_logger(logging_level: str):
    switcher = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
                'error': logging.ERROR, 'critical': logging.CRITICAL}

    log_level = switcher.get(logging_level)

    logging_format = '%(asctime)s - %(levelname)s @ %(filename)s: %(message)s'
    logging.basicConfig(stream=sys.stdout, format=logging_format, datefmt='%H:%M:%S')
    logging.getLogger('py3_logger').setLevel(log_level)
    return logging.getLogger('py3_logger')
