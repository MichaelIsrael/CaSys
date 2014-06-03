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
from gi.repository import Gst, GObject, GstVideo

GObject.threads_init()
Gst.init(None)

class CasysControl:
	def __init__(self):
		self.__logger = logging.getLogger('CasysControl')
		self.__logger.debug('Initializing a CasysControl object.')
		self.__deviceList = self.CasysDevicesList()
		self.update()


	def update(self):
		self.__logger.debug('Finding new available camera devices.')
		for devFile in iglob(VIDEO_DEV_FILES_PATTERN):
			if devFile in self.__deviceList:
				self.__logger.debug('Skipping {}. (already added)'.format(devFile))
				continue

			self.__logger.debug('New camera detected on: {}.'.format(devFile))

			casysDev = self.CasysDevice(devFile)

			try:
				casysDev.CreatePipeline()
			except (CreateElementError, AddToPipelineError, LinkingElementsError):
				self.__logger.exception('An error was encountered while creating a CasysDevice for ' +  devFile)
				del casysDev
				continue

			self.__deviceList.append(casysDev)

		self.__logger.debug("{} new camera devices were detected.".format(len(self.__deviceList)))


	def __getitem__(self, key):
		return self.__deviceList[key]


	def __contains__(self, key):
		return key in self.__deviceList


	def getNumberOfDevices(self):
		return len(self.__deviceList)


	def connect(self, device, xid):
		if device:
			if type(device) is self.CasysDevice:
				device.connectGui(xid)
			else:
				# Possibly propagated exceptions: ValueError, TypeError
				self.__deviceList[device].connectGui(xid)
		else:
			self.__logger.debug("Attempting to connect all devices.")
			xidIndex = 0
			for dev in self.__deviceList:
				dev.connectGui(xid[xidIndex])
				xidIndex += 1


	def Fragment(self, device = None):
		"""
		Fragmenting the recorded video file.
		"""
		if device:
			if type(device) is self.CasysDevice:
				device.Fragment()
			else:
				# Possibly propagated exceptions: ValueError, TypeError
				self.__deviceList[device].Fragment()
		else:
			self.__logger.debug("Attempting to start recording for all devices.")
			for dev in self.__deviceList:
				dev.Fragment()
		return True


	def record(self, device=None):
		"""
		Start video recording from the detected Cameras to files.
		"""
		if device:
			if type(device) is self.CasysDevice:
				device.Start()
			else:
				# Possibly propagated exceptions: ValueError, TypeError
				self.__deviceList[device].Start()
		else:
			self.__logger.debug("Attempting to start recording for all devices.")
			for dev in self.__deviceList:
				dev.Start()

	'''
	def stream(self, coo):
#((x1,y1),(x2,y2)) = coo
		xi = Gst.ElementFactory.make('ximagesrc', None)
		if xi is None:
			print("ERROR 0")
		conv = Gst.ElementFactory.make('videoconvert', None)
		if conv is None:
			print("ERROR 1")
		enc = Gst.ElementFactory.make('x264enc', None)
		if enc is None:
			print("ERROR 2")
		rtp = Gst.ElementFactory.make('rtph264pay', None)
		if rtp is None:
			print("ERROR 3")
		udp = Gst.ElementFactory.make('udpsink', None)
		if udp is None:
			print("ERROR 4")

		"""
		xi.set_property("startx", x1)
		xi.set_property("starty", y1)
		xi.set_property("endx", x2)
		xi.set_property("endy", y2)
		"""
		xi.set_property("xid", coo)

		udp.set_property("host", "127.0.0.1")
		udp.set_property("port", 5000)

		self.pipe = Gst.Pipeline()
		if self.pipe is None:
			print("ERROR 5")

		if not self.pipe.add(xi):
			print("ERROR 6")
		if not self.pipe.add(conv):
			print("ERROR 7")
		if not self.pipe.add(enc):
			print("ERROR 8")
		if not self.pipe.add(rtp):
			print("ERROR 9")
		if not self.pipe.add(udp):
			print("ERROR 10")

		test = Gst.ElementFactory.make('videotestsrc', None)
		self.pipe.add(test)
		test.link(enc)

		if not xi.link(conv):
			print("ERROR 11")
		if not conv.link(enc):
			print("ERROR 12")

		"""
		if not test.link(enc):
			print("ERROR 12.5")
			"""

		if not enc.link(rtp):
			print("ERROR 13")
		if not rtp.link(udp):
			print("ERROR 14")

		self.pipe.set_state(Gst.State.PLAYING)
		print("DONE!")
		'''

	def __del__(self):
		self.__logger.debug('Deleting the CasysControl object.')
		del self.__deviceList
		del self.__logger


	def __iter__(self):
		self.__logger.debug('Iterator of the device list.')
		return iter(self.__deviceList)




	class CasysDevicesList(list):
		def __init__(self):
			#self.__logger = logging.getLogger('CasysDeviceList')
			self.__names = []
			self.__paths = []
			list.__init__(self)


		def __getitem__(self, key):
			if type(key) is str:
				if key in self.__names:
					return list.__getitem__(self, self.__names.index(key))
				elif key in self.__paths:
					return list.__getitem__(self, self.__paths.index(key))
				else:
					raise KeyError("CasysDeviceList does not contain an element {}.".format(key))

			elif type(key) is int:
				return list.__getitem__(self, key)

			else:
				raise TypeError("Indeces of a CasysDevicesList can only be integers or strings")


		def __contains__(self, element):
			if type(element) is str:
				if element in self.__names or element in self.__paths:
					return True
			elif type(element) is CasysControl.CasysDevice:
				if element.DevicePath in self.__paths:
					return True
			return False


		def append(self, element):
			if type(element) is not CasysControl.CasysDevice:
				raise TypeError('A CasysDeviceList can only hold elements of type CasysDevice. No support for {}.'.format(type(element)))
			self.__names.append(element.DeviceName)
			self.__paths.append(element.DevicePath)
			list.append(self, element)



	class CasysDevice:
		def __init__(self, devFile):
			#TODO: Check existance of rely on creator?
			self.__logger = logging.getLogger('CasysDevice ' + str(devFile))
			self.__logger.debug('Initializing a new instance of CasysDevice')
			self.DevicePath = devFile
			self.DeviceName = path.basename(devFile)
		
		def CreatePipeline(self):
			#Creating Gstreamer elements.
			self.__logger.debug('Creating pipeline-elements.')

			camera = Gst.ElementFactory.make('v4l2src', 'Camera' + self.DeviceName)
			if camera is None:
				self.__logger.critical('Failed to create element: camera (v4l2src)')
				raise CreateElementError('v4l2src')

			clock = Gst.ElementFactory.make('clockoverlay', 'Clock' + self.DeviceName)
			if clock is None:
				self.__logger.critical('Failed to create element: clockoverlay')
				Gst.Object.unref(camera)
				raise CreateElementError('clockoverlay')

			title = Gst.ElementFactory.make('textoverlay', 'Title' + self.DeviceName)
			if title is None:
				self.__logger.critical('Failed to create element: textoverlay')
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				raise CreateElementError('textoverlay')

			tee = Gst.ElementFactory.make('tee', 'Tee' + self.DeviceName)
			if tee is None:
				self.__logger.critical('Failed to create element: tee')
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				raise CreateElementError('tee')

			queue = Gst.ElementFactory.make('queue', 'FileQueue' + self.DeviceName)
			if queue is None:
				self.__logger.critical('Failed to create element: queue')
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				raise CreateElementError('queue')

			encoder = Gst.ElementFactory.make('theoraenc', 'Encoder' + self.DeviceName)
			if encoder is None:
				self.__logger.critical('Failed to create element: encoder (theoraenc)')
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				raise CreateElementError('theoraenc')

			mux = Gst.ElementFactory.make('oggmux', 'Mux' + self.DeviceName)
			if mux is None:
				self.__logger.critical('Failed to create element: mux (oggmux)')
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				raise CreateElementError('oggmux')

			outfile = Gst.ElementFactory.make('filesink', 'File' + self.DeviceName)
			if outfile is None:
				self.__logger.critical('Failed to create element: outfile (filesink)')
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				raise CreateElementError('filesink')


			#Configuring elements.
			camera.set_property('device', self.DevicePath)
			title.set_property('text', self.DeviceName)
			title.set_property('valignment', "top")
			title.set_property('halignment', "right")
			outfile.set_property('location', self.__createFileName())

			#Creating the pipeline.
			self.__logger.debug('Creating pipeline.')
			self.__pipeline = Gst.Pipeline()

			if self.__pipeline is None:
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				raise CreateElementError('Pipeline')

			self.__pipeline.set_name('Pipeline' + self.DeviceName)

			#Getting the bus.
			self.__logger.debug('Getting the bus of this pipeline.')
			bus = self.__pipeline.get_bus()
			bus.set_name("Bus" + self.DeviceName)

			#Connecting the bus to the handler.
#FIXME: the following causes problems
			bus.add_signal_watch()
			bus.connect('message', self.__message_handler)

			#Adding the elements to the pipeline.
			self.__logger.debug('Adding the elements to the pipeline.')
			if not self.__pipeline.add(camera):
				self.__logger.critical("Failed to add element 'camera' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("v4l2src")

			if not self.__pipeline.add(clock):
				self.__logger.critical("Failed to add element 'clock' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("clockoverlay")

			if not self.__pipeline.add(title):
				self.__logger.critical("Failed to add element 'title' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("textoverlay")

			if not self.__pipeline.add(tee):
				self.__logger.critical("Failed to add element 'tee' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("tee")

			if not self.__pipeline.add(queue):
				self.__logger.critical("Failed to add element 'queue' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("queue")

			if not self.__pipeline.add(encoder):
				self.__logger.critical("Failed to add element 'encoder' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("theoraenc")

			if not self.__pipeline.add(mux):
				self.__logger.critical("Failed to add element 'mux' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("oggmux")

			if not self.__pipeline.add(outfile):
				self.__logger.critical("Failed to add element 'outfile' to the pipeline.")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise AddToPipelineError("filesink")


			#Linking the elements.
			self.__logger.debug('Linking the elements.')
			if not camera.link(clock):
				self.__logger.critical("Failed to link elements: Camera and Clock")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("v4l2src", "clockoverlay")

			self.__logger.debug('Linking the elements.')
			if not clock.link(title):
				self.__logger.critical("Failed to link elements: Clock and Title")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("clockoverlay", "textoverlay")

			if not title.link(tee):
				self.__logger.critical("Failed to link elements: Clock and Tee")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("clockoverlay",  "tee")


			if not tee.link(queue):
				self.__logger.critical("Failed to link elements: Tee and Queue")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("tee", "queue")

			if not queue.link(encoder):
				self.__logger.critical("Failed to link elements: Queue and Encoder")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("queue", "theoraenc")

			if not encoder.link(mux):
				self.__logger.critical("Failed to link elements: Encoder and Mux")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("theoraenc", "oggmux")

			if not mux.link(outfile):
				self.__logger.critical("Failed to link elements: Mux and OutFile")
				Gst.Object.unref(camera)
				Gst.Object.unref(clock)
				Gst.Object.unref(title)
				Gst.Object.unref(tee)
				Gst.Object.unref(queue)
				Gst.Object.unref(encoder)
				Gst.Object.unref(mux)
				Gst.Object.unref(outfile)
				Gst.Object.unref(self.__pipeline)
				raise LinkingElementsError("oggmux", "filesink")



		def __message_handler(self, bus, msg):
			#TODO: Another logger with name BUS amd device?
			msg_name = msg.get_structure().get_name()
			self.__logger.debug("A {} message is received, calling the apropriate handler".format(msg_name))

			if msg_name == 'GstMessageNewClock':
				self.__logger.info("GstMessage {}: New clock is selected for {} with value {}".format(msg.seqnum, msg.src.get_name(), msg.parse_new_clock().get_time()))

			elif msg_name == 'GstMessageStreamStatus':
				[typ, own] = msg.parse_stream_status()
				self.__logger.info("GstMessage {}: stream Status received from {}: Type = {}, owner = {}.".format(msg.seqnum, msg.src.get_name(), typ.value_nick, own.get_name()))

			elif msg_name == 'GstMessageStateChanged':
				[old, new, pending] = msg.parse_state_changed()
				self.__logger.info("GstMessage {}: State of {} changed from {} to {} (Pending: {})".format(msg.seqnum, msg.src.get_name(), old.value_nick, new.value_nick, pending.value_nick))

			elif msg_name == 'GstMessageAsyncDone':
				self.__logger.info("GstMessage {}: Async-done received from {} at {}".format(msg.seqnum, msg.src.get_name(), msg.parse_async_done()))

			elif msg_name == 'GstMessageWarning':
				[gerr, debug] = msg.parse_warning()
				self.__logger.warning("GstMessage {}: WARNING {} from {}: {}\n->{}".format(msg.seqnum, msg.src.get_name(), gerr.code, gerr.message, debug))

			elif msg_name == 'GstMessageStreamStart':
				self.__logger.info("GstMessage {}: Stream-Start received from {}".format(msg.seqnum, msg.src.get_name()))

			elif msg_name == 'GstMessageQOS':
				#TODO: Implement.
				self.__logger.info("GstMessage {}: QOS of {}".format(msg.seqnum, msg.src.get_name()))

			else:
				mstruct = msg.get_structure()
				num = mstruct.n_fields()
				errMsg = """Unhandled GstMessage number {} from element {} of bus {}
		Structure analysis:
		  Name = {}
		  Number of fields = {}""".format(msg.seqnum, msg.src.get_name(), bus.get_name(), msg.get_structure().get_name(), num)
				for i in range(num):
					f = mstruct.nth_field_name(i)
					val = mstruct.get_value(f)
					errMsg += "\n    #{} - {} = {}".format(i, f, val)
				self.__logger.fatal(errMsg)



		def connectGui(self, xid):
			self.__logger.debug("Connecting to XID: " + str(xid))

			self.__logger.debug("Geting the tee element from the pipeline")
			tee = self.__pipeline.get_by_name('Tee' + self.DeviceName)
			if tee is None:
				raise KeyError('Tee' + self.DeviceName + ' was not found in the pipeline of device: ' + self.DeviceName)

			padt = tee.get_request_pad('src_%u')

			self.__logger.debug("Creating necessary elements")
			queue = Gst.ElementFactory.make('queue', 'GuiQueue' + self.DeviceName)

			sink = Gst.ElementFactory.make('xvimagesink', 'imgsink' + self.DeviceName)
			sink.set_property("sync", 0)
			sink.set_property('force-aspect-ratio', True)

			self.__logger.debug("Adding new elements to the pipeline.")
			self.__pipeline.add(sink)
			self.__pipeline.add(queue)

			self.__logger.debug("Linking the new elements.")
			tee.link(queue)
			queue.link(sink)

			self.__logger.debug("Connecting the video to the corresponding xid")
			sink.set_window_handle(xid)

			self.__logger.debug("Setting the whole pipeline to playing.")
			self.__pipeline.set_state(Gst.State.PLAYING)


		def Stop(self):
			self.__logger.debug('Stoping device.')
			if hasattr(self, "__pipeline"):
				self.__pipeline.set_state(Gst.State.NULL)


		def Start(self):
			self.__logger.debug("Playing device.")
			self.__pipeline.set_state(Gst.State.PLAYING)


		def Fragment(self):
			self.__logger.debug("Fragmenting video files")
			outfile = self.__pipeline.get_by_name('File' + self.DeviceName)
			NewName = self.__createFileName() 
			self.Stop()
			outfile.set_property('location', NewName)
			self.Start()


		def __del__(self):
			self.__logger.debug('Deleting the CasysDevice')
			self.Stop()
			if hasattr(self, "__pipeline"):
				Gst.Object.unref(self.__pipeline)


		def __createFileName(self):
			current_time = strftime("%Y-%m-%d-%H",localtime())
			self.__logger.debug( "Creating a new file name at '" + current_time + "'.")
			for index in self.__counter():
				filename = path.join( VIDEO_STORAGE_PATH, self.DeviceName + ' ' + current_time + index + EXTENSION)
				if path.exists(filename):
					self.__logger.warning("File "  + filename + " already exists.")
				else:
					self.__logger.debug( 'Using: ' + filename)
					return filename


		def __counter(self):
			yield ''
			i = 0
			while True:
				yield '_' + str(i)
				i  += 1


class CasysError(Exception):
	pass

class CreateElementError(CasysError):
	def __init__(self, Name=None):
		self.__name = str(Name)
	
	def __str__(self):
		if self.__name is None:
			return "Error occured while creating an element."
		else:
			return "Error occured while creating element {}.".format(self.__name)

class AddToPipelineError(CasysError):
	def __init__(self, Name=None):
		self.__name = str(Name)

	def __str__(self):
		if self.__name is None:
			return "Error occured while adding an element to the pipeline."
		else:
			return "Error occured while adding element '{}' to the pipeline.".format(self.__name)

class LinkingElementsError(CasysError):
	def __init__(self, SourceElement=None, DestinationElement=None):
		self.__srcElement = str(SourceElement)
		self.__destElement = str(DestinationElement)

	def __str__(self):
		if self.__srcElement is None and self.__destElement is None:
			return "Error occured while linking two elements."
		elif self.__srcElement is None and self.__destElement is not None:
			return "Error occured while linking to source {}.".format(self.__srcElement)
		elif self.__srcElement is not None and self.__destElement is None:
			return "Error occured while linking to destination {}.".format(self.__destElement)
		else:
			return "Error occured while linking source {} to destination {}.".format(self.__srcElement, self.__destElement)

