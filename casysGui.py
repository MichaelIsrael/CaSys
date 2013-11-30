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

class CasysGui():
	def __init__(self):
		self.window = Gtk.Window()
		self.window.set_resizable(False)
		self.window.fullscreen()

	def show(self):
		self.window.show_all()

	def prepareView(self, number=1):
		if hasattr(self, "__videoTable"):
			self.window.remove(self.__videoTable)
			del self.__videoTable
		xids = []
		self.__videoTable = Gtk.Table(1, 1, True)
		self.window.add(self.__videoTable)
		videoArea = Gtk.DrawingArea()
		self.__videoTable.attach(videoArea, 0, 1, 0, 1)
		xid = videoArea.get_property('window').get_xid()
		xids.append(xid)
		return xids



