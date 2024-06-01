import logging
__version__ = "0.2.1"

# Configure the logging module to output diagnostic information
    # CRITICAL (50): A very serious error that may prevent the program from continuing to run.
    # ERROR (40): A more serious problem that has prevented the program from performing a function.
    # WARNING (30): An indication that something unexpected happened, or there may be some problem in the near future (e.g., 'disk space low'). The software is still working as expected.
    # INFO (20): Confirmation that things are working as expected.
    # DEBUG (10): Detailed information, typically of interest only when diagnosing problems.
    # NOTSET (0) which is used to capture all levels of log.
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(module)s %(name)s.%(funcName)s: %(message)s')
