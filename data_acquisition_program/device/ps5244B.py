from ctypes import *
import sys, math, time
import numpy as np
import threading, Queue

"""
Questo modulo contiene l'interfaccia con il driver di picoscope.
La classe principale e' ps5244B che contiene metodi e proprieta' per la gestione dell'oscilloscopio.
"""

class ps5244B:
    def __init__(self, logger, queue):
        # general properties
        # name of the driver
        self.LIBNAME = "ps5000a"
        # dictionary for picoscope's status codes as specified in the official documentation
        self.PICO_STATUS = {}
        self.PICO_STATUS["PICO_OK"] = 0x00000000
        self.PICO_STATUS["PICO_POWER_SUPPLY_UNDERVOLTAGE"] = 0x0000011C
        self.PICO_STATUS["PICO_TOO_MANY_SAMPLES"] = 0x0000001D
        self.UNIT_INFO_TYPES = {"DriverVersion": 0x0,
                           "USBVersion": 0x1,
                           "HardwareVersion": 0x2,
                           "VariantInfo": 0x3,
                           "BatchAndSerial": 0x4,
                           "CalDate": 0x5,
                           "KernelVersion": 0x6,
                           "DigitalHardwareVersion": 0x7,
                           "AnalogueHardwareVersion": 0x8,
                           "PicoFirmwareVersion1": 0x9,
                           "PicoFirmwareVersion2": 0xA}

        self.CHANNELS = {"A": 0, "B": 1}
        self.CHANNEL_COUPLINGS = {"DC": 1, "AC": 0}
        self.CHANNEL_RANGE = {"10mV":0,"20mV":1,"50mV":2,"100mV":3,"200mV":4,"500mV":5,"1V":6,"2V":7,"5V":8,"10V":9,"20V":10}
        self.ADC_RESOLUTION = {"8bit":0, "12bit":1, "14bit":2, "15bit":3, "16bit":4}
        self.TRIGGER_DIRECTION = {"Above":0, "Below":1, "Rising":2, "Falling":3, "RiseOrFall": 4}
        # hook for the logger (it saves to file messages from the program for subsequent checks)
        self.logger = logger
        self.q = queue

        # loading library
        self.library_OK = False
        self.lib = None
        self.logger.info("loading library "+self.LIBNAME)
        try:
            self.lib = cdll.LoadLibrary("lib"+self.LIBNAME+".so")
            self.logger.info("library loaded OK!")
            self.library_OK = True
        except:
            self.logger.error("unable to load library!")
        finally:
            self.q.put_nowait(["Library load status: "+str(self.library_OK)])

        # PicoScope handle -> this is needed by the PicoScope driver's callbacks
        self.handle = None
        self.resolution = self.ADC_RESOLUTION["12bit"]

        # Status variables
        self.UnitOpened = False
        self.user_total_samples = 0
        self.maxSamples_per_segment = 0
        self.timeIntervalNs = 0
        self.true_timebase = 0
        self.true_sample_interval = 0
        self.true_sample_rate = 0
        self.trigger_source = 0
        self.trigger_direction = 0
        self.trigger_level_mV = 0
        self.n_segments = 0
        self.timeOf_overshoot = 0
        self.overshoot = False

        # Timing variables
        self.timeOf_start = 0
        self.timeOf_end = 0

    """
        FUNDAMENTAL FUNCTIONS FOR PICOSCOPE OPERATION
        OpenUnit: opens the unit and saves the "handle"
        CloseUnit: closes the unit once one is done with it
        GetUnitInfo: obtains information from the unit (model, firmware version, etc)
        StopUnit: stops the data collection process
    """
    #This function opens the unit by calling ps5000aOpenUnit from the API
    def OpenUnit(self):
        # checking whether library was loaded OK or not
        if not self.library_OK:
            self.q.put_nowait(["Unable to open unit due to failure to load appropriate library."])
            return False

        # opening unit
        c_handle = c_int16()
        m = self.lib.ps5000aOpenUnit(byref(c_handle), None, self.resolution)
        self.handle = c_handle.value

        # checking scope status
        if m == self.PICO_STATUS["PICO_OK"]:
            self.logger.info("Unit openened correctly")
            self.q.put_nowait(["Unit opened correctly"])
            self.UnitOpened = True
            return True
        else:
            self.logger.error("Unable to open unit. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to open unit. PicoScope returned: "+str(m)])
            return False

    #This function closes the unit by calling ps5000aCloseUnit from the API
    def CloseUnit(self):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False
        m = self.lib.ps5000aCloseUnit(c_int16(self.handle))
        if m == self.PICO_STATUS["PICO_OK"]:
            self.handle = None
            self.q.put_nowait(["Unit closed correctly"])
            self.logger.info("Unit closed correctly")
            return True
        else:
            self.logger.error("Unable to close unit. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to close unit. PicoScope returned: "+str(m)])
            return False

    #This function stops the unit collecting data
    def StopUnit(self):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False
        # stopping the unit
        m = self.lib.ps5000aStop(c_int16(self.handle))
        if (m == self.PICO_STATUS["PICO_OK"]):
            self.logger.info("Unit stopped correctly")
            self.q.put_nowait(["Unit stopped correctly"])
            return True
        else:
            self.logger.error("Unable to stop unit. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to stop unit. PicoScopre returned: "+str(m)])
            return False

    #This function gets information from the unit
    def GetUnitInfo(self):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False
        # reading information
        s = create_string_buffer(256)
        requiredSize = c_int16(0)
        out = "Unit information:"
        for key in UNIT_INFO_TYPES:
            info = UNIT_INFO_TYPES[key]
            m = self.lib.ps5000aGetUnitInfo(c_int16(self.handle), byref(s), c_int16(len(s)), byref(requiredSize), c_int32(info))
            if m == self.PICO_STATUS["PICO_OK"]:
                print key, ":", s.value.decode('utf-8')
                out += key+":"+s.value.decode('utf-8')+"\r\n"
        self.logger.info(out)
        return True

    """
        PICOSCOPE SETUP RELATED FUNCTIONS
        SetChannel: sets up a channel. Mandatory args: channel, enabled.
        SetDeviceResolution: sets the device's ADC resolution.
        SetSampling: calculates sampling parameters for the scope.
        SetSimpleTrigger: sets the trigger
        MemorySegments: divides the scope's memory into segments to enable rapid capture of waveforms.
        SetNoOfCaptures: sets the number of captures for a given run.
        RunBlock: runs the scope.
        IsReady: waits until the scope has finished collecting all the data.
        GetValuesBulk: downloads the scope's memory content in the data buffer.
        SetSigGenBuiltInSimple: sets up the signal generator.
    """
    #This function sets a channel on the scope
    def SetChannel(self, channel, enabled, vrange="10mV", voffset=0.0, coupling="DC"):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False
        # checking whether channel exists
        ch_num = -1
        if channel not in self.CHANNELS:
            self.logger.error("Unknown channel: "+str(channel))
            self.q.put_nowait(["Unknown channel: "+channel])
            return False
        else:
            ch_num = self.CHANNELS[channel]
        # checking enabled or disabled
        ch_status = 0
        if enabled:
            ch_status = 1
        # checking vrange
        ch_vrange = 0
        if vrange not in self.CHANNEL_RANGE:
            self.logger.error("Unsupported voltage range: "+vrange)
            self.q.put_nowait(["Unsupported voltage range: "+vrange])
            return False
        else:
            ch_vrange = self.CHANNEL_RANGE[vrange]
        # checking coupling
        ch_coup = 0
        if coupling not in self.CHANNEL_COUPLINGS:
            self.logger.error("Unsupported coupling type: "+coupling)
            self.q.put_nowait(["Unsupported coupling type: "+coupling])
            return False
        else:
            ch_coup = self.CHANNEL_COUPLINGS[coupling]
        # everything is ready to configure the channel
        m = self.lib.ps5000aSetChannel(c_int16(self.handle), c_int32(ch_num), c_int16(ch_status), c_int32(ch_coup), c_int32(ch_vrange), c_float(voffset))
        if m == self.PICO_STATUS["PICO_OK"]:
            out = "Channel "+channel+" setup information:\r\n"
            out+= "Enabled: "+str(enabled)+"\r\n"
            out+= "Vrange: "+vrange+" -> "+str(ch_vrange)+"\r\n"
            out+= "Coupling: "+coupling+" -> "+str(ch_coup)+"\r\n"
            out+= "Voffset: "+str(voffset)+"\r\n"
            self.logger.info(out)
            self.q.put_nowait([out])
            return True
        else:
            self.logger.error("Unable to set up channel "+channel+". PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to set up channel "+channel+". PicoScope returned: "+str(m)])
            return False

    #This function sets the resolution on the scope's ADC
    def SetDeviceResolution(self, resolution):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False
        # checking resolution
        if resolution not in self.ADC_RESOLUTION:
            self.logger.error("Unsupported ADC resolution: "+resolution)
            self.q.put_nowait(["Unsupported ADC resolution: "+resolution])
            return False
        else:
            m = self.lib.ps5000aSetDeviceResolution(c_int16(self.handle), c_int32(self.ADC_RESOLUTION[resolution]))
            if m == self.PICO_STATUS["PICO_OK"]:
                self.resolution = self.ADC_RESOLUTION[resolution]
                self.logger.info("ADC resolution set at: "+resolution)
                self.q.put_nowait(["ADC resolution set at: "+resolution])
                return True
            else:
                self.logger.error("Unable to set ADC resolution at: "+resolution+". PicoScope returned: "+str(m))
                self.q.put_nowait(["Unable to set ADC resolution at: "+resolution+". PicoScope returned: "+str(m)])
                return False

    #This function calculates the "true" sampling parameters given a sample_rate / event duration and samples per division
    #The official documentation specifies the proper formulae to calculate the various parameters. These formulae depend
    #on the required ADC's resolution.
    def SetSampling(self, samples_per_division, user_sample_rate=False, user_event_duration=False):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # checking options
        sample_interval = 0
        if (not user_sample_rate) and (not user_event_duration):
            self.q.put_nowait(["Please specify a sample rate OR an event duration."])
            return False
        elif (not user_sample_rate) and (user_event_duration):
            # event duration is in seconds --> sample interval in seconds
            total_samples = 10*samples_per_division
            sample_interval = float(user_event_duration) / total_samples
        elif (user_sample_rate) and (not user_event_duration):
            # sample rate is in samples / s
            sample_interval = 1.0/user_sample_rate
        else:
            self.q.put_nowait(["Please specify a sample rate OR an event duration."])
            return False

        # helper variables
        timebase = 0
        true_timebase = 0
        true_sample_interval = 0
        true_sample_rate = 0

        # checking resolution to determine the true_sample_interval, rate and timebase
        if self.resolution == self.ADC_RESOLUTION["8bit"]:
            max_interval = 34.36
            if sample_interval < (8.0E-9):
                timebase = math.floor(math.log(sample_interval*1E9, 2))
                timebase = max(timebase, 0)
            else:
                if (sample_interval > max_interval):
                    sample_interval = max_interval
                timebase = math.floor((sample_interval*125000000)+2)
            true_timebase = int(timebase)
            if true_timebase < 3:
                true_sample_interval = (2**true_timebase)/(1.0E9)
            else:
                true_sample_interval = (true_timebase-2)/(125000000.0)
            true_sample_rate = 1.0/(true_sample_interval)
        elif self.resolution == self.ADC_RESOLUTION["12bit"]:
            max_interval = 68.72
            if sample_interval < (16.0E-9):
                timebase = math.floor(math.log(sample_interval*5E8,2)+1)
                timebase = max(timebase, 1)
            else:
                if (sample_interval > max_interval):
                    sample_interval = max_interval
                timebase = math.floor((sample_interval*62500000)+3)
            true_timebase = int(timebase)
            if true_timebase < 4:
                true_sample_interval = (2**(true_timebase-1))/(500000000.0)
            else:
                true_sample_interval = (true_timebase-3)/62500000.0
            true_sample_rate = 1.0/(true_sample_interval)
        elif (self.resolution == self.ADC_RESOLUTION["14bit"]) or (self.resolution == self.ADC_RESOLUTION["15bit"]):
            max_interval = 34.36
            if sample_interval > max_interval:
                sample_interval = max_interval
            timebase = math.floor((sample_interval*125000000)+2)
            timebase = max(timebase, 3)
            true_timebase = int(timebase)
            true_sample_interval = (true_timebase-2)/125000000.0
            true_sample_rate = 1.0/(true_sample_interval)
        elif self.resolution == self.ADC_RESOLUTION["16bit"]:
            max_interval = 68.72
            if sample_interval > max_interval:
                sample_interval = max_interval
            timebase = math.floor((sample_interval*62500000)+3)
            timebase = max(timebase, 3)
            true_timebase = int(timebase)
            true_sample_interval = (timebase-3)/62500000.0
            true_sample_rate = 1.0/(true_sample_interval)

        # logging
        out = "Timebase information\r\n"
        out+= "User sample rate: "+str(user_sample_rate/1.0E6)+" MS/s"+"\r\n"
        out+= "User sample interval: "+str(sample_interval*1.0E9)+" ns"+"\r\n"
        out+= "Nearest device parameters\r\n"
        out+= "Sample rate: "+str(true_sample_rate/1.0E6)+" MS/s"+"\r\n"
        out+= "Sample interval: "+str(true_sample_interval*1.0E9)+" ns"+"\r\n"
        out+= "System Timebase: "+str(true_timebase)+"\r\n"
        self.logger.info(out)
        self.q.put_nowait([out])

        # now to see if the total number of samples required is OK
        user_total_samples = 10*samples_per_division
        maxSamples = c_int32()
        timeIntervalNs = c_float()
        m = self.lib.ps5000aGetTimebase2(c_int16(self.handle), c_uint32(true_timebase), c_uint32(user_total_samples), byref(timeIntervalNs), byref(maxSamples), c_uint32(0))

        # checking pico response
        if m == self.PICO_STATUS["PICO_OK"]:
            self.logger.info("Sampling parameters set correctly")
            self.q.put_nowait(["Sampling parameters set correctly"])
            # saving
            self.user_total_samples = user_total_samples
            self.maxSamples_per_segment = maxSamples.value
            self.timeIntervalNs = timeIntervalNs.value
            self.true_timebase = true_timebase
            self.true_sample_interval = true_sample_interval
            self.true_sample_rate = true_sample_rate
            return True
        elif m == self.PICO_STATUS["PICO_TOO_MANY_SAMPLES"]:
            self.logger.warning("Too many samples. Try to lower samples/div or to decrease memory segmentation.")
            self.q.put_nowait(["Too many samples. Try to lower samples/div or to decrease memory segmentation."])
            return False
        else:
            self.logger.error("Unable to set up sampling parameters. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to set up sampling parameters. PicoScope returned: "+str(m)])
            return False

    #Function that sets up a trigger, the easy way :)
    def SetSimpleTrigger(self, trigger_source, trigger_level_mV, direction, delay=0, timeout_ms=100, enabled=True):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # checking trigger source
        trigSrc = None
        if trigger_source not in self.CHANNELS:
            self.logger.error("Unknown trigger source: "+trigger_source)
            self.q.put_nowait(["Unknown trigger source: "+trigger_source])
            return False
        else:
            trigSrc = self.CHANNELS[trigger_source]

        # checking trigger direction
        trigDir = None
        if direction not in self.TRIGGER_DIRECTION:
            self.logger.error("Unknown trigger direction: "+direction)
            self.q.put_nowait(["Unknown trigger direction: "+direction])
            return False
        else:
            trigDir = self.TRIGGER_DIRECTION[direction]

        # converting voltage level to ADC counts
        trigLevelADC = 0
        if (trigger_level_mV > 5000.0) or (trigger_level_mV < -5000.0):
            self.logger.error("Trigger voltage level out of range. Must lay between -5V and +5V.")
            self.q.put_nowait(["Trigger voltage level out of range. Must lay between -5V and +5V."])
            return False
        else:
            a2v = 5000.0 / 32764  # max voltage on trigger is 5V that corresponds to 32764 -> a2v = 5.0/32764
            trigLevelADC = int(trigger_level_mV / a2v)

        # checking enabled
        if enabled:
            enabled = 1
        else:
            enabled = 0

        # setting the trigger
	    print self.handle, enabled, trigSrc, trigLevelADC, trigDir, delay, timeout_ms
        m = self.lib.ps5000aSetSimpleTrigger(c_int16(self.handle), c_int16(enabled), c_int32(trigSrc), c_int16(trigLevelADC), c_int32(trigDir), c_uint32(delay), c_int16(timeout_ms))
        if m == self.PICO_STATUS["PICO_OK"]:
            out = "Trigger Setup\r\n"
            out+= "Trigger Setup"
            out+= "Source:"+str(trigger_source)
            out+= "Direction:"+str(direction)
            out+= "Level:"+str(trigger_level_mV)+"\t"+str(trigLevelADC)
            self.logger.info(out)
            self.q.put_nowait([out])
            # saving
            self.trigger_source = trigger_source
            self.trigger_direction = direction
            self.trigger_level_mV = trigger_level_mV
            return True
        else:
            self.logger.error("Unable to set the trigger. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to set the trigger. PicoScope returned: "+str(m)])
            return False

    #Function that sets up the scope's memory
    def MemorySegments(self, n_segments):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # dividing the memory into segments
        maxSamples_per_segment = c_int32()
        m = self.lib.ps5000aMemorySegments(c_int16(self.handle), c_uint32(n_segments), byref(maxSamples_per_segment))
        if m == self.PICO_STATUS["PICO_OK"]:
            out = "Memory Segmentation\r\n"
            out+= "N. of segments: "+str(n_segments)
            out+= "Samples/segment: "+str(maxSamples_per_segment.value)
            self.logger.info(out)
            self.q.put_nowait([out])
            self.maxSamples_per_segment = maxSamples_per_segment.value
            self.n_segments = n_segments
            return True
        else:
            self.logger.error("Unable to set memory segments to: "+str(n_segments)+". PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to set memory segments to: "+str(n_segments)+". PicoScope returned: "+str(m)])
            return False

    #Function that sets the number of captures for a given run
    def SetNoOfCaptures(self, n_captures):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # setting the number of captures
        m = self.lib.ps5000aSetNoOfCaptures(c_int16(self.handle), c_uint32(n_captures))
        if m == self.PICO_STATUS["PICO_OK"]:
            self.logger.info("Number of captures per run set at: "+str(n_captures))
            self.q.put_nowait(["Number of captures per run set at: "+str(n_captures)])
            return True
        else:
            self.logger.error("Unable to set number of captures per run at: "+str(n_captures))
            self.q.put_nowait(["Unable to set number of captures per run at: "+str(n_captures)])
            return False

    #Function that starts the scope in "block mode".
    """
    When in "block mode", the scope will fill each memory segment sequentially as soon as a new event is captured.
    By so doing, the "dead time" is minimized, since the scope won't have to reset the trigger each time an event is
    captured.
    """
    def RunBlock(self, preTrigger_percent):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # setting up some stuff before the run
        preTrigger_percent /= 100.0
        nOfPreTrigger_samples = int(round(self.user_total_samples*preTrigger_percent))
        nOfPostTrigger_samples = self.user_total_samples - nOfPreTrigger_samples
        timeIndisposed_ms = c_int32()

        # running the scope -> PicoScope will automatically fill each memory segment sequentially, no need to recall RunBlock for each segment
        m = self.lib.ps5000aRunBlock(c_int16(self.handle), c_uint32(nOfPreTrigger_samples), c_uint32(nOfPostTrigger_samples), c_uint32(self.true_timebase), byref(timeIndisposed_ms), c_uint32(0), c_void_p(), c_void_p())

        if m == self.PICO_STATUS["PICO_OK"]:
            self.logger.info("DATA COLLECTION STARTED")
            self.q.put_nowait(["DATA COLLECTION STARTED - "+time.strftime("%H%M%S",time.localtime())])
            self.timeOf_start = time.time()
            return True
        else:
            self.logger.info("Unable to start data collection. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to start data collection. PicoScope returned: "+str(m)])
            return False

    #Function that blocks until the scope has finished collecting data.
    def IsReady(self, run_time):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # checking scope status
        wait = True
        while wait:
            ready = c_int16()
            m = self.lib.ps5000aIsReady(c_int16(self.handle), byref(ready))
            if ready.value:
                wait = False
            if ((time.time() - self.timeOf_start) >= run_time):
                # exceeding maximum allowed run-time
                if not self.overshoot:
                    self.timeOf_overshoot = time.time()
                    self.overshoot = True

        # updating
        self.logger.info("DATA COLLECTION ENDED")
        self.q.put_nowait(["DATA COLLECTION ENDED - " + time.strftime("%H%M%S", time.localtime())])
        self.timeOf_end = time.time()

        # checking for overshoot
        if self.overshoot:
            dT = self.timeOf_end - self.timeOf_overshoot
            self.logger.warning("Exceeded expected runtime by: "+str(dT)+" seconds")
            self.q.put_nowait(["Exceeded expected runtime by: "+str(dT)+" seconds"])
            self.overshoot = False

    #Function that retrieves data from the scope
    def GetValuesBulk(self, channel):
        # checking whether the unit has been opened
        if not self.UnitOpened:
            return False

        # checking whether channel exists
        ch_num = -1
        if channel not in self.CHANNELS:
            self.logger.error("Unknown channel: " + str(channel))
            self.q.put_nowait(["Unknown channel: " +str(channel)])
            return False
        else:
            ch_num = self.CHANNELS[channel]

        # setting up the data buffer and overflow buffer
        numSamples = min(self.maxSamples_per_segment, self.user_total_samples)
        data = np.ascontiguousarray(np.zeros((self.n_segments, numSamples), dtype=np.int16))
        overflow = np.ascontiguousarray(np.zeros(self.n_segments, dtype=np.int16))

        # shaping up the array
        for i, segment in enumerate(range(0, self.n_segments)):
            self._setDataBuffer(ch_num, data[i], segment, 0)

        # getting the values from the scope and into the buffer
        user_all_samples = self.user_total_samples*self.n_segments
        n_samples_captures = self._getDataBuffer(user_all_samples, overflow)
        if n_samples_captures:
            n_samples_retrieved, n_captures_retrieved = n_samples_captures
            deltaT = self.timeOf_end - self.timeOf_start
            return (data, n_samples_retrieved, n_captures_retrieved, deltaT)
        else:
            return False

    #PRIVATE HELPER FUNCTIONS
    # this function sets the data buffer in order to retrieve data from PicoScope
    def _setDataBuffer(self, channel, data, segmentIndex, downSampleMode=0):
        dataPtr = data.ctypes.data_as(POINTER(c_int16))
        numSamples = len(data)
        m = self.lib.ps5000aSetDataBuffer(c_int16(self.handle), c_int32(channel), dataPtr, c_int32(numSamples), c_uint32(segmentIndex), c_int32(downSampleMode))
        if m == self.PICO_STATUS["PICO_OK"]:
            self.logger.info("Data buffer set OK for segment: "+str(segmentIndex))
            self.q.put_nowait(["Data buffer set OK for segment: "+str(segmentIndex)])
            return True
        else:
            self.logger.error("Unable to set data buffer for segment: "+str(segmentIndex)+". PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to set data buffer for segment: "+str(segmentIndex)+". PicoScope returned: "+str(m)])
            return False

    # this function fills up the buffer that was previously set by _setDataBuffer
    def _getDataBuffer(self, numSamples, overflow):
        # obtaining the number of available captures
        numCaptures = c_uint32()
        m = self.lib.ps5000aGetNoOfCaptures(c_int16(self.handle), byref(numCaptures))
        numCaptures = numCaptures.value

        overflowPoint = overflow.ctypes.data_as(POINTER(c_int16))
        issued_nOfSamples = numSamples
        m = self.lib.ps5000aGetValuesBulk(c_int16(self.handle), byref(c_int32(numSamples)), c_int32(0), c_int32(numCaptures-1), c_int32(1), c_int32(0), overflowPoint)
        if m == self.PICO_STATUS["PICO_OK"]:
            out = "Data Retrieve Report\r\n"
            out+= "Issued number of captures: "+str(self.n_segments)+"\r\n"
            out+= "Actual number of captures: "+str(numCaptures)+"\r\n"
            out+= "Issued number of samples: "+str(issued_nOfSamples)+"\r\n"
            out+= "Actual number of samples: "+str(numSamples)+"\r\n"
            self.logger.info(out)
            self.q.put_nowait([out])
            return [numSamples, numCaptures]
        else:
            self.logger.error("Unable to retrieve data from the scope. PicoScope returned: "+str(m))
            self.q.put_nowait(["Unable to retrieve data from the scope. PicoScope returned: "+str(m)])
            return False

    # FUNCTION TO RUN PICOSCOPE
    """
    This function will read a "run file". This file may be written by the user of by the graphical control program.
    it contains the values of the various parameters in order to set up and run a data collection session.
    """
    def run(self, run_file):
        # opening the run file
        f = open(run_file)
        data = f.read()
        f.close()
        # reading the parameters
        data = data.split("\n")
        data.pop()
        # converting strings to variables with their values
        for line in data:
            exec line

        # opening the unit
        if not self.OpenUnit():
            sys.exit(1)

        # setting channels
        if not self.SetChannel(channel=channel_name, enabled=True, vrange=channel_range):
            sys.exit(1)
        if channel_name == "A":
            self.SetChannel(channel="B", enabled=False)
        elif channel_name == "B":
            self.SetChannel(channel="A", enabled=False)
        else:
            sys.exit(1)

        # setting resolution
        if not self.SetDeviceResolution(resolution):
            sys.exit(1)

        # setting timebase
        if not self.SetSampling(samples_per_division, user_sample_rate=sample_rate, user_event_duration=event_duration):
            sys.exit(1)

        # setting trigger
        if not self.SetSimpleTrigger(trigger_source, trigger_level_mV, direction=trigger_direction, timeout_ms=trigger_timeout_ms):
            sys.exit(1)

        # setting memory segments
        if not self.MemorySegments(n_segments):
            sys.exit(1)

        # now the number of captures needs to be partitioned between runs since the scope's memory is segmented
        self.q.put_nowait(["n_captures:"+str(n_captures)+"\t"+"n_segments:"+str(n_segments)])
        n_runs = int(float(n_captures) / n_segments)
        nOf_captures = []
        for i in range(0,n_runs,1):
            nOf_captures.append(n_segments)
        leftover = n_captures - (n_runs*n_segments)
        if leftover > 0:
            nOf_captures.append(leftover)
        #print leftover,nOf_captures

        # now the PicoScope is run until all the required events have been captured OR until the execution time limit
        # has been reached. For instance, if a run time of 100s and a number of 10 events are specified, the program
        # will terminate upon whichever of the two conditions is satisfied first. Since the program does not have
        # control while the scope blocks upon waiting for an event, an "overshoot" controller is implemented. This
        # will check the timestamp at which the event occurred and it will discard the event if it occurred at a later
        # time than the allowed maximum one.
        outputs = []
        total_time = 0
        total_captures = 0
        run_index = 0
        remaining_time = run_time
        # the file "run_BlockTimes" contains two timestamps for each block of memory. A first timestamp indicates
        # the time at which the scope started the data collection, while a second timestamp indicates the time at which
        # the memory segments had been filled. When the scope is run with just 1 memory segment (useful when the
        # event count is really low), the timestamp coincides with the time of arrival of each pulse.
        block_time_file = open("run_BlockTimes.txt","w")
        for n_c in nOf_captures:
            # setting up the run
            if not self.SetNoOfCaptures(n_c):
                sys.exit(1)
            self.logger.info("Setting up run: "+str(run_index))
            self.logger.info("Signals to capture in this run: "+str(n_c))
            self.logger.info("Remaining time: "+str(remaining_time))
            self.q.put_nowait(["Setting up run: "+str(run_index)])
            self.q.put_nowait(["Signals to capture in this run: "+str(n_c)])
            self.q.put_nowait(["Remaining time: "+str(remaining_time)])
            # running the block
            if not self.RunBlock(preTrigger_percent):
                sys.exit(1)
            # now to wait until this block completes
            self.IsReady(remaining_time)
            block_time_file.write(str(self.timeOf_start)+"\t"+str(self.timeOf_end)+"\r\n")
            self.q.put_nowait(["GetPressure","."])
            # getting the values
            self.q.put_nowait(["Downloading block data (please wait since this may take a while)..."])
            output = self.GetValuesBulk(channel=channel_name)
            if not output:
                sys.exit(1)
            outputs.append(output)

            # updating counters
            total_time += output[3]
            total_captures += output[2]
            run_index += 1
            remaining_time -= output[3]

            if (total_time >= run_time) or (total_captures >= n_captures):
                self.q.put_nowait(["Data collection terminated"])
                self.q.put_nowait(["Total time:"+str(total_time)+"/"+str(run_time)])
                self.q.put_nowait(["Total captures:"+str(total_captures)+"/"+str(n_captures)])
                break;
        # closing this file
        block_time_file.close()
        # returning the output
        return outputs

    # SIGNAL GENERATOR FUNCTION --> WARNING: UNTESTED and not available in the main program.
    def SetSigGenBuiltInSimple(self, frequency, offset_voltage, pktopk):
        waveType = 0 # 0 = Sine
        m = self.lib.ps5000aSetSigGenBuiltIn(c_int16(self.handle), c_int32(offset_voltage*1000000), c_int32(pktopk*1000000), c_int16(waveType), c_float(frequency), c_float(frequency), c_float(0), c_float(0), c_uint32(0), c_uint32(0), c_uint32(1), c_uint32(0), c_uint32(0), c_uint32(0), c_int16(0))
        if m == self.PICO_STATUS["PICO_OK"]:
            print "Signal generator set up correctly."
            print "Outputting sine wave @",pktopk,"+",offset_voltage," | f =",frequency
            return True
        else:
            print "Unable to set up signal generator. PicoScope returned: "+str(m)
            return False