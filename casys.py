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

import time
from casyscontrol import CasysControl
from casys_const import *
from glob import iglob
from os import path
import os
import sys
import argparse
import logging
import logging.handlers
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
	logging.basicConfig(level=args.log, format=args.logformat[0], style='{', filename=args.logfile[0])
	casys_log = logging.getLogger( 'Main' )

	casys_log.debug('Logger configured, starting logging.')
	casys_log.debug('loglevel = {}'.format(args.log))

#	smtp = logging.handlers.SMTPHandler("smtp.googlemail.com", "michael.behman@gmail.com", "michael.behman@gmail.com", "testmail", ("michael.behman@gmail.com", "MB@myGMAILspass"))

#smtp.emit("test")

	GObject.threads_init()
	Gst.init(None)

	#TODO: Catch possible exception.
	casys = CasysControl()
	casys.record()

	mainloop = GLib.MainLoop()
	#Setting timer:
	#TODO: Goto beginning of the hour first?
	GLib.timeout_add_seconds(5, cleaner, casys)
	GLib.timeout_add_seconds(FRAGMENT_TIME, deleteOld, casys)
	GLib.timeout_add_seconds(FRAGMENT_TIME, casys.fragment)

	#Main loop:
	mainloop.run()

	#Main loop stopped.
	casys_log.warning('Unexpected behavior: End of main reached.')

	#Cleaning:
	del casys

def cleaner(casys):
	logger = logging.getLogger('Cleaner')
	expireTime = time.time() - VIDEO_EXPIRE_DURATION
	logger.debug('Deleting files older than: {} ({})'.format(expireTime, time.strftime("%Y/%m/%d %H:%M:%s", time.localtime(expireTime))))
	for videoFile in os.listdir(VIDEO_STORAGE_PATH):
		if os.stat(path.join(VIDEO_STORAGE_PATH, videoFile)).st_mtime < expireTime:
			logger.info('Deleting expired files: ' + videoFile)
			#TODO: Catch OSError
			os.remove(videoFile)



def deleteOld(casys):
	logger = logging.getLogger('deleteOld')
	minimumTime = time.strftime("%Y-%m-%d-%H",time.localtime(time.time() - VIDEO_EXPIRE_DURATION))
	logger.debug('Deleting files older than: ' + minimumTime)
	for dev in casys.videoDevices:
		minimumFile = path.join(VIDEO_STORAGE_PATH, dev + ' ' + minimumTime)
		for videoFile in iglob( path.join(VIDEO_STORAGE_PATH, dev + '*')):
			if videoFile < minimumFile:
				logger.info('Deleting expired video file: ' + videoFile)
				os.remove(videoFile)
	return True


class LogParse(argparse.Action):
	def __call__(self, parser, namespace, val, option_string = None):
		val = getattr(logging, val.upper())
		setattr(namespace, self.dest, val)


"""Call the main function"""
if __name__ == "__main__":
	main()
