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
from casysabstraction import CasysObject, CasysBaseError

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, GstVideo


GObject.threads_init()
Gst.init(None)


class CasysControl(CasysObject):
    def __init__(self):
        super().__init__()
        self.__logger = logging.getLogger('CasysControl')
        self.__logger.debug('Initializing a CasysControl object.')
        self.__deviceList = CasysDevicesList()
        self.update()

    def update(self):
        self.__logger.debug('Finding new available camera devices.')
        for devFile in iglob(VIDEO_DEV_FILES_PATTERN):
            if devFile in self.__deviceList:
                self.__logger.debug('Skipping {}. (already added)'.format(devFile))
                continue

            self.__logger.debug('New camera detected on: {}.'.format(devFile))

            casysDev = CasysDevice(devFile)

            try:
                casysDev.CreatePipeline()
            except (CreateElementError, AddToPipelineError, LinkingElementsError):
                self.__logger.critical('An error was encountered while creating a CasysDevice for ' + devFile, exc_info=True)
                del casysDev
                continue

            self.__deviceList.append(casysDev)

        self.__logger.debug("Currently {} detected camera devices.".format(len(self.__deviceList)))

    def __getitem__(self, key):
        return self.__deviceList[key]

    def __contains__(self, key):
        return key in self.__deviceList

    def __len__(self):
        return len(self.__deviceList)

    def connect(self, xid, device=None):
        if device:
            if type(device) is CasysDevice:
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

    def Fragment(self, device=None):
        """
        Fragmenting the recorded video file.
        """
        if device:
            if type(device) is CasysDevice:
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
            if type(device) is CasysDevice:
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
# ((x1,y1),(x2,y2)) = coo
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

    def free(self):
        pass


class CasysDevicesList(list, CasysObject):
    def __init__(self):
        super().__init__()
        # self.__logger = logging.getLogger('CasysDeviceList')
        self.__names = []
        self.__paths = []

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
        elif type(element) is CasysDevice:
            if element.DevicePath in self.__paths:
                return True
        return False

    def append(self, element):
        if type(element) is not CasysDevice:
            raise TypeError('A CasysDeviceList can only hold elements of type CasysDevice. No support for {}.'.format(type(element)))
        self.__names.append(element.DeviceName)
        self.__paths.append(element.DevicePath)
        list.append(self, element)

    def free(self):
        pass


class CasysDevicePipeline(CasysObject):
    def __init__(self, name):
        super().__init__()
        self._name = name
        self._logger = logging.getLogger('Casys.Pipeline.' + str(name))

        self._logger.info("Creating a new instance of CasysDevicePipeline.")
        self._logger.debug("Creating GstPipeline")
        self._gstpipeline = Gst.Pipeline.new(name)
        if not self._gstpipeline:
            self._logger.critical("Failed to Create GstPipeline")
            raise CreateElementError("pipeline")

    def free(self):
        self._logger.info("Freeing object.")
        Gst.Object.unref(self._pipeline)

    def get_bus(self):
        return self._gstpipeline.get_bus()

    def set_state(self, *args, **kwargs):
        return self._gstpipeline.set_state(*args, **kwargs)

    def add_element(self,
                    element_type,
                    element_name,
                    link_to_last=False,
                    **properties):
        self._logger.info("Adding new element {} ({}: {}).".format(
                element_name, element_type, properties))
        element = Gst.ElementFactory.make(
            element_type, element_name)

        for key, value in properties.items():
            try:
                element.set_property(key, value)
            except TypeError:
                raise CreateElementError(element_type) from None

        if not self._gstpipeline.add(element):
            raise AddToPipelineError(element_type)

        try:
            last = self._last_element
        except AttributeError:
            pass
        else:
            if not last.link(element):
                raise LinkingElementsError(last, element)
        finally:
            self._last_element = element

        return element


class CasysDevice(CasysObject):
    def __init__(self, devFile):
        super().__init__()
        # TODO: Check existance or rely on creator?
        self.__logger = logging.getLogger('CasysDevice ' + str(devFile))
        self.__logger.debug('Initializing a new instance of CasysDevice')
        self.DevicePath = devFile
        self.DeviceName = path.basename(devFile)

    def CreatePipeline(self):
        # Creating Gstreamer elements.
        self.__logger.debug('Creating pipeline-elements.')
        self._pipeline = CasysDevicePipeline('Pipeline_' + self.DeviceName)
        self._pipeline.add_element('v4l2src',
                                   'Camera_'+self.DeviceName,
                                   device=self.DevicePath,
                                   )
        self._pipeline.add_element('clockoverlay', 'Clock_'+self.DeviceName)
        self._pipeline.add_element('textoverlay',
                                   'Title_'+self.DeviceName,
                                   text=self.DeviceName,
                                   valignment="top",
                                   halignment="right",
                                   )
        self._pipeline.add_element('tee', 'Tee_'+self.DeviceName)
        self._pipeline.add_element('queue', 'FileQueue_'+self.DeviceName)
        self._pipeline.add_element('matroskamux', 'Mux_'+self.DeviceName)
        self._pipeline.add_element('filesink',
                                   'File_'+self.DeviceName,
                                   location=self.__createFileName(),
                                   )

        # Getting the bus.
        self.__logger.debug('Getting the bus of this pipeline.')
        bus = self._pipeline.get_bus()
        bus.set_name("Bus_"+self.DeviceName)

        # Connecting the bus to the handler.
        # FIXME: the following causes problems
        # bus.add_signal_watch()
        bus.connect('message', self.__message_handler)

    def __message_handler(self, bus, msg):
        # TODO: Another logger with name BUS amd device?
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
            self.__logger.warning("GstMessage {}: WARNING {} from {}: {}\n->{}".format(msg.seqnum, gerr.code, msg.src.get_name(), gerr.message, debug))

        elif msg_name == 'GstMessageStreamStart':
            self.__logger.info("GstMessage {}: Stream-Start received from {}".format(msg.seqnum, msg.src.get_name()))

        elif msg_name == 'GstMessageQOS':
            # TODO: Implement.
            self.__logger.info("GstMessage {}: QOS of {}".format(msg.seqnum, msg.src.get_name()))

        elif msg_name == 'GstMessageError':
            [gerr, debug] = msg.parse_error()
            self.__logger.critical("GstMessage {}: Error {} in {}:\n{}\n  -->{}".format(msg.seqnum, gerr.code, msg.src.get_name(), gerr.message, debug))

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
        # TODO
        """
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
        self._pipeline.set_state(Gst.State.PLAYING)
        """

    def Stop(self):
        self.__logger.debug('Stoping device.')
        try:
            self._pipeline.set_state(Gst.State.NULL)
        except AttributeError:
            pass

    def Start(self):
        self.__logger.debug("Playing device.")
        self._pipeline.set_state(Gst.State.PLAYING)

    def Fragment(self):
        self.__logger.debug("Fragmenting video files")
        # TODO
        """
        outfile = self.__pipeline.get_by_name('File' + self.DeviceName)
        NewName = self.__createFileName()
        self.Stop()
        outfile.set_property('location', NewName)
        self.Start()
        """

    def free(self):
        self.__logger.debug('Deleting the CasysDevice')
        self.Stop()
        try:
            self._pipeline.free()
        except AttributeError:
            pass

    def __createFileName(self):
        current_time = strftime("%Y-%m-%d-%H", localtime())
        self.__logger.debug("Creating a new file name at '" + current_time + "'.")
        for index in self.__counter():
            filename = path.join(VIDEO_STORAGE_PATH, self.DeviceName + ' ' + current_time + index + EXTENSION)
            if path.exists(filename):
                self.__logger.warning("File " + filename + " already exists.")
            else:
                self.__logger.debug('Using: ' + filename)
                return filename

    def __counter(self):
        yield ''
        i = 0
        while True:
            yield '_' + str(i)
            i += 1


class CreateElementError(CasysBaseError):
    def __init__(self, Name=None):
        self.__name = str(Name)

    def __str__(self):
        if self.__name is None:
            return "Error occured while creating an element."
        else:
            return "Error occured while creating element {}.".format(self.__name)


class AddToPipelineError(CasysBaseError):
    def __init__(self, Name=None):
        self.__name = str(Name)

    def __str__(self):
        if self.__name is None:
            return "Error occured while adding an element to the pipeline."
        else:
            return "Error occured while adding element '{}' to the pipeline.".format(self.__name)


class LinkingElementsError(CasysBaseError):
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
