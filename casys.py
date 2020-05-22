#!/usr/bin/env python3
#
# Copyright 2013-2014 Michael Israel
#
# This file is part of Casys.
#
# Casys is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Casys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Casys.  If not, see <http://www.gnu.org/licenses/>.Copyright.
"""
Casys is a basic CCTV camera system. It is designed originally to be ran on a Raspberry Pi
board (or any other board that runs GNU/Linux). Casys detects connected Video Cameras through
the V4L2 interface and records their outputs.
"""

from casysControl import CasysControl
from casys_const import *
from casysGui import CasysGui

import os
import argparse
import sys
from glob import iglob
from queue import Queue
from time import strftime, localtime, time, sleep
from io import IOBase
from tempfile import TemporaryFile

import logging
from logging.handlers import RotatingFileHandler, SMTPHandler, QueueHandler, QueueListener

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib


def main():
    """The main function:
It parses the arguments and initialized the logger.
"""

    #Parsing arguments.
    parser = argparse.ArgumentParser(description=DESCRIPTION, fromfile_prefix_chars='@',
            formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False, epilog=EPILOG)

    grp_log = parser.add_argument_group( 'Logger arguments' );
    grp_log.add_argument('-l', '--log', action=LogParse, default=DEFAULT_LOG_LEVEL,
            choices=LOG_LEVEL_LIST + [x.upper() for x in LOG_LEVEL_LIST],
            metavar='lvl', help='set log level {}'.format(LOG_LEVEL_LIST))
    grp_log.add_argument('--logformat', nargs=1, help='set the logger format', metavar='fmt')
    grp_log.add_argument('--logfile', nargs=1, help='specify the log file', metavar='file')

    grp_inf = parser.add_argument_group( 'Informational arguments' );
    grp_inf.add_argument('-h', '--help', action='help', help='show this help message and exit')
    grp_inf.add_argument('-v', '--version', action='version', version='%(prog)s {0}'.format(VERSION))

    arg_list = sys.argv
    arg_list[0] = CONFIG_FILE
    args = parser.parse_args(arg_list)

    #Configuring logger
    logging.logThreads = 0
    logging.logProcesses = 0
    logRoot = logging.getLogger()
    logRoot.setLevel(logging.DEBUG)

    # Log file.
    logFile = RotatingFileHandler(args.logfile[0], maxBytes=LOG_MAX_FILE, backupCount=LOG_BACK_COUNT)
    logRoot.addHandler(logFile)

    # Start of session
    logRoot.info("========================================================================================================================")
    logRoot.info("                                        New session started (%s)" % strftime("%Y/%m/%d %H:%M:%S", localtime()))
    logRoot.info("========================================================================================================================")

    # Setting up format and level.
    logFile.setLevel(args.log)
    logFileFmt = logging.Formatter(args.logformat[0], style='{')
    logFile.setFormatter(logFileFmt)


    sys.stderr = StdToLog("StdErr", logging.ERROR)
    sys.stdout = StdToLog("StdOut", logging.WARN)

    # Log mail.
    logSMTP = SMTPHandler(LOG_MAIL_HOST, LOG_MAIL_FROM, LOG_MAIL_TO, LOG_MAIL_SUBJECT, LOG_MAIL_CRED, timeout=15)
    #TODO: What about exceptions?
    logSMTP.setLevel(logging.CRITICAL)

    #TODO:formatter
    SMTPFmt = SMTPFormatter(args.logformat[0], style='{')
    logSMTP.setFormatter(SMTPFmt)

    SMTPqueue = Queue(-1)
    logQueueHandler = QueueHandler(SMTPqueue)
    logQueueListener = QueueListener(SMTPqueue, logSMTP)
    logQueueHandler.setLevel(logging.CRITICAL)
    logRoot.addHandler(logQueueHandler)
    del logRoot

    casys_log = logging.getLogger( 'Main' )
    casys_log.debug('Logger configured. Starting SMTP queue listener.')
    logQueueListener.start()
    casys_log.debug('loglevel = {}'.format(args.log))

    casys_log.info("Basic initialization.")

    casys_log.debug("Checking the videos' directory.")
    try:
        CheckVideoDirectory()
    except:
        casys_log.critical("An exception was raised while setting videos' directory", exc_info=True)
        
    casys_log.debug("Initilizing GObject and Gst.")
    GObject.threads_init()
    Gst.init(None)

    casys_log.debug("Creating the CasysControl object.")
    casys = CasysControl()
    casys_log.debug("Starting to record.")
    casys.record()

    #Setting timer:
    #TODO: Goto beginning of the hour first?
    casys_log.debug("Adding cleanup and fragmentation timers.")
    GLib.timeout_add_seconds(5, cleaner, casys)
    GLib.timeout_add_seconds(FRAGMENT_TIME, casys.Fragment)

    #Initialize and show Gui.
    casys_log.debug("Initializing the casys gui.")
    gui = CasysGui()
    casys_log.debug("Showing the Gui.")
    gui.show()
    casys_log.debug('Preparing video view for the found cameras.')
    num = len(casys)
    #TODO: Better view.
    [xids,coord] = gui.prepareView(num, 1)

    sleep(1.5)
    casys.connect(xids)
    #sleep(1.5)

    #Main loop:
    casys_log.debug("Running the GLib Mainloop.")
    mainloop = GLib.MainLoop()
    mainloop.run()

    #Main loop stopped.
    casys_log.warning('Unexpected behavior: End of main reached.')

    #Cleaning:
    logQueueListener.stop()
    del casys


def cleaner(casys):
    logger = logging.getLogger('Cleaner')
    expireTime = time() - VIDEO_EXPIRE_DURATION
    logger.debug('Deleting files older than: {} ({})'.format(expireTime, strftime("%Y/%m/%d %H:%M:%S", localtime(expireTime))))
    try:
        for videoFile in os.listdir(VIDEO_STORAGE_PATH):
            videoFile = os.path.join(VIDEO_STORAGE_PATH, videoFile)
            if os.stat(videoFile).st_mtime < expireTime:
                logger.info('Deleting expired files: ' + videoFile)
                try:
                    os.remove(videoFile)
                except OSError:
                    logger.exception("Failed to clean videos' directory.")
                finally:
                    return True
    except FileNotFoundError:
        logger.exception("An error occured while running cleaner")
    finally:
        return True

def CheckVideoDirectory():
    logger = logging.getLogger('CheckVideoDirectory')
    logger.debug("Attempting to create a 'dummy' file in the videos' directory")
    try:
        TmpFile = TemporaryFile(dir=VIDEO_STORAGE_PATH)
        TmpFile.close()
    except FileNotFoundError:
        logger.info("Video directory does not exist. Creating it, and reruning the check.")
        os.mkdir(VIDEO_STORAGE_PATH, 0o755)
        CheckVideoDirectory()
    except PermissionError:
        logger.info("No write permission for the video directory. Attempting to fix, and reruning the check.")
        os.chmod(VIDEO_STORAGE_PATH, 0o755)
        CheckVideoDirectory()




class LogParse(argparse.Action):
    def __call__(self, parser, namespace, val, option_string = None):
        val = getattr(logging, val.upper())
        setattr(namespace, self.dest, val)


class SMTPFormatter(logging.Formatter):
    def format(self, record):
        """
        Overriding the format function to force encoding. Otherwise an exception could be throwen
        """
        result = logging.Formatter.format(self, record)
        if isinstance(result, str):
            result = result.encode(LOG_MAIL_ENCODING)
        return result


class StdToLog(IOBase):
    def __init__(self, name, level):
        self.logger = logging.getLogger(name)
        self.level = level

    def write(self, msg):
        if msg != "\n":
            self.logger.log(self.level, msg)

def main_wrapper():
    """
    Wrapper for the main function to report uncaught exceptions and re-run main() if CONTINUE_ON_EXCEPTION == True.
    """
    try: main()
    except:
        logger = logging.getLogger("main_wrapper")
        logger.critical("Uncaught exception", exc_info=True)
    finally:
        if(CONTINUE_ON_EXCEPTION):
            main_wrapper()
        

"""Call the main function"""
if __name__ == "__main__":
    main_wrapper()
