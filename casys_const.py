NAME = 'Casys'
VERSION = 1.0
CONFIG_FILE = '@config'
DEFAULT_LOG_LEVEL = "info"
LOG_LEVEL_LIST = ['debug', 'info', 'warn', 'error', 'fatal'] 
EPILOG = """Author: Michael Israel (Behman)
E-mail: michael.behman@gmail.com
"""
DESCRIPTION = """CCTV cameras monitoring and recording System
Version {0}""".format(VERSION)

VIDEO_DEV_FILES_PATTERN = '/dev/video*'
VIDEO_STORAGE_PATH = './videos'
VIDEO_EXPIRE_DURATION = 24 * 60 * 60 #1 day
EXTENSION = '.ogv'

FRAGMENT_TIME = 60 * 60 #1 hour
