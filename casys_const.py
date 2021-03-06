NAME = 'Casys'
VERSION = 1.0
CONFIG_FILE = '@config'
EPILOG = """Author: Michael Israel (Behman)
E-mail: michael.behman@gmail.com
"""
DESCRIPTION = """CCTV cameras monitoring and recording System
Version {0}""".format(VERSION)

CONTINUE_ON_EXCEPTION = False

DEFAULT_LOG_LEVEL = "info"
LOG_LEVEL_LIST = ['debug', 'info', 'warn', 'error', 'fatal'] 
LOG_MAX_FILE = 10 * 1024 * 1024 # 10 MB
LOG_BACK_COUNT = 5

LOG_MAIL_HOST = "localhost"
LOG_MAIL_FROM = "log@casys"
LOG_MAIL_TO = "michael.behman@gmail.com"
LOG_MAIL_SUBJECT = "Casys Critical error"
LOG_MAIL_CRED = None
LOG_MAIL_ENCODING = 'utf-32'

VIDEO_DEV_FILES_PATTERN = '/dev/video*'
VIDEO_STORAGE_PATH = './videos'
VIDEO_EXPIRE_DURATION = 24 * 60 * 60 #1 day
EXTENSION = '.ogv'
FRAGMENT_TIME = 60 * 60 #1 hour
