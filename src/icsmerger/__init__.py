import logging
__version__ = "0.1.2"

# Configure the logging module to output diagnostic information
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(module)s %(name)s.%(funcName)s: %(message)s')