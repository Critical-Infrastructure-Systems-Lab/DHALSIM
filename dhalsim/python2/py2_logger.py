import logging
import sys

logging_level = logging.INFO
logging_format = '%(asctime)s - %(levelname)s @ %(filename)s: %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging_level, format=logging_format, datefmt='%H:%M:%S')
logger = logging.getLogger('py2_logger')
