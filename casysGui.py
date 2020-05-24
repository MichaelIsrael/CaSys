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
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk, GdkX11


#class CasysGui(Gtk.Application):
class CasysGui():
    def __init__(self):
        self._logger = logging.getLogger('CasysGui')
        self._logger.debug('Creating window.')
        self._window = Gtk.Window()
        self._window.set_resizable(False)
        self._window.fullscreen()

        self._logger.debug('Creating a Gtk Grid.')
        self._grid = Gtk.Grid()
        self._grid.set_row_homogeneous(True)
        self._grid.set_column_homogeneous(True)
        self._window.add(self._grid)

        self._logger.debug('Showing window.')
        self._window.show_all()

    def prepareView(self, horizontal=1, vertical=1):
        self._logger.debug('Preparing video view.')
        if horizontal < 1 or vertical < 1:
            raise ValueError('The number of views must be bigger than 0. ({}, {}) were provided'.format(horizontal, vertical))

        xids = []

        for yIndex in range(vertical):
            for xIndex in range(horizontal):
                self._logger.debug('Creating a video area for ({}, {}).'.format(xIndex, yIndex))
                videoArea = Gtk.DrawingArea()
                self._grid.attach(videoArea, xIndex, yIndex, 1, 1)
                videoArea.show()

                xid = videoArea.get_property('window').get_xid()
                xids.append(xid)

        self._window.show_all()

        return xids

    def main(self):
        Gtk.main()
