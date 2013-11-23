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

from casys_const import VIDEO_DEV_FILES_PATTERN, EXTENSION, VIDEO_STORAGE_PATH
import logging
from glob import iglob
from os import path
from time import localtime, strftime
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

class CasysControl:
	__logger = logging.getLogger('CasysControl')
	pipelines = {}
	videoDevices = {}

	def __init__(self):
		self.__logger.debug('Initializing a CasysControl object.')
		for devFile in iglob(VIDEO_DEV_FILES_PATTERN):
			self.videoDevices[path.basename(devFile)] = devFile
		#TODO: Create appropriate exception.
		if len(self.videoDevices) == 0:
			raise Exception
		for dev in self.videoDevices:
			self.__logger.debug('Camera detected on: ' +  self.videoDevices[dev])

			#TODO: Check for errors and log more:

			#Creating Gstreamer elements.
			camera = Gst.ElementFactory.make('v4l2src', 'Camera' + dev)
			clock = Gst.ElementFactory.make('clockoverlay', 'Clock' + dev)
			encoder = Gst.ElementFactory.make('theoraenc', 'Encoder' + dev)
			mux = Gst.ElementFactory.make('oggmux', 'Mux' + dev)
			outfile = Gst.ElementFactory.make('filesink', 'File' + dev)

			#Configuring elements.
			camera.set_property('device', self.videoDevices[dev])
			outfile.set_property('location', self.__createFileName(dev))

			#Creating the pipeline.
			self.pipelines[dev] = Gst.Pipeline()

			#Adding the elements to the pipeline.
			self.pipelines[dev].add(camera)
			self.pipelines[dev].add(encoder)
			self.pipelines[dev].add(mux)
			self.pipelines[dev].add(clock)
			self.pipelines[dev].add(outfile)

			#Linking the elements.
			camera.link(clock)
			clock.link(encoder)
			encoder.link(mux)
			mux.link(outfile)

			#Unreferencing elements.
			Gst.Object.unref(camera)
			Gst.Object.unref(clock)
			Gst.Object.unref(encoder)
			Gst.Object.unref(mux)
			Gst.Object.unref(outfile)


	def fragment(self):
		self.__logger.debug("Fragmenting video files")
		for dev in self.pipelines:
			self.pipelines[dev].set_state(Gst.State.NULL)
			outfile = self.pipelines[dev].get_by_name('File' + dev)
			outfile.set_property('location', self.__createFileName(dev))
			self.pipelines[dev].set_state(Gst.State.PLAYING)
		return True

	def __createFileName(self, suffix):
		current_time = strftime("%Y-%m-%d-%H",localtime())
		self.__logger.debug( "Creating file name for '" + suffix + "' at '" + current_time + "'")
		for index in self.__counter():
			filename = path.join( VIDEO_STORAGE_PATH, suffix + ' ' + current_time + index + EXTENSION)
			if path.exists(filename):
				self.__logger.warning(filename + " already exists")
			else:
			 	self.__logger.debug( 'Using: ' + filename)
			 	return filename

	def __counter(self):
		yield ''
		i = 0
		while True:
			yield '_' + str(i)
			i  += 1


	def record(self, device=None):
		"""
		Start video recording from the detected Cameras to files.
		"""
		#starting the pipelines.
		if device:
			if device not in self.videoDevices.values():
				self.__logger.error('Device ' + device + ' was not detected.')
				raise ValueError
			self.__logger.debug("Attempting to start recording for " + device + " only.")
			self.pipelines[device].set_state(Gst.State.PLAYING)
		else:
			self.__logger.debug("Attempting to start recording for all devices.")
			for dev in self.pipelines:
				self.__logger.debug("Recording for device " + dev + ".")
				self.pipelines[dev].set_state(Gst.State.PLAYING)

	def __del__(self):
		self.__logger.debug('Deleting the CasysControl object.')
		#pipe1.set_state(Gst.State.READY)
		for dev in self.pipelines:
			Gst.Object.unref(self.pipelines[dev])


	def __iter__(self):
		return self

	def __next__(self):
		self.__logger.error('__next__() called for iteration. Not implemented yet.')
		raise NotImplementedError
		raise StopIteration
