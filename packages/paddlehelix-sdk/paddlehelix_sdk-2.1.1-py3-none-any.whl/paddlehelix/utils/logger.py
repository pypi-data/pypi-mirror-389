import os
import sys
import logging
from termcolor import colored

def create_logger(output_dir=None, log_file='log.txt', name=''):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    fmt = '[%(asctime)s %(name)s]: %(levelname)s %(message)s'
    color_fmt = colored('[%(asctime)s %(name)s]', 'green') + ': %(levelname)s %(message)s'

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter(fmt=color_fmt, datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(console_handler)

    # create file handlers
    if output_dir is not None:
        file_handler = logging.FileHandler(os.path.join(output_dir, log_file), mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(file_handler)

    return logger

