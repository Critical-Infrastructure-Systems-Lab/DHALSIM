import logging
import sys

logging_level = logging.INFO
logging_format = '%(asctime)s - %(levelname)s @ %(filename)s:%(lineno)d: %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging_level, format=logging_format)
logger = logging.getLogger(__name__)