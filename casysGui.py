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
This is the gui of Casys.
"""

import gi
from gi.repository import GObject, Gtk, GdkX11
import logging

#class CasysGui(Gtk.Application):
class CasysGui():
	def __init__(self):
		self.__logger = logging.getLogger('CasysGui')
		self.__logger.debug('Creating window.')
		self.__window = Gtk.Window()
		self.__window.set_resizable(False)
		self.__window.fullscreen()

	def show(self):
		self.__logger.debug('Showing window.')
		self.__window.show_all()

	def prepareView(self, horizontal=1, vertical=1):
		self.__logger.debug('Preparing video view.')
		if horizontal < 1 or vertical < 1:
			raise ValueError('The number of views must be bigger than 0. ({}, {}) were provided'.format(horizontal, vertical))

		if hasattr(self, "__videoTable"):
			self.__logger.debug('Removing old view.')
			self.__window.remove(self.__videoTable)
			del self.__videoTable

		xids = []

		self.__logger.debug('Creating main table accoding to the provided numbers: ({}, {}).'.format(horizontal, vertical))
		self.__videoTable = Gtk.Table(vertical, horizontal, True)
		self.__window.add(self.__videoTable)

		#TODO: Coord?
		coord = ((0,0),(600,600))

		for yIndex in range(vertical):
			for xIndex in range(horizontal):
				self.__logger.debug('Creating a video area for ({}, {}).'.format(xIndex, yIndex))
				videoArea = Gtk.DrawingArea()
				self.__videoTable.attach(videoArea, xIndex, xIndex + 1, yIndex, yIndex + 1)
				xid = videoArea.get_property('window').get_xid()
				xids.append(xid)

		self.__window.show_all()

		return [xids, coord]

	def main(self):
		Gtk.main()
		self.run("")


