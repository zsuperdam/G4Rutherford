import threading, serial, time, Queue, sys, os

"""
This module specifies the "Arduino Thread" that will run along the main process in the main thread, sending commands
through the serial port to arduino and waiting for the board's response.
The arduino board provides for:
1. controlling the source position by rotating the stepper motor.
2. measuring the chamber pressure by sampling the voltage on the vacuum gauges via the internal arduino's ADC.
"""

def Header():
    return time.strftime("%d%h%Y_%H%M%S",time.localtime())+"[Arduino] >: "

# Since this is a Thread, we implement and extend the "threading.Thread" class.
class Arduino(threading.Thread):
    def __init__(self, parent, q):
        threading.Thread.__init__(self)
        self._parent = parent
        self._q = q
        # reading cfg file and serial port
        # the cfg.txt file contains the COM port address (Unix style, like /dev/ttyACM0) and the COM port baud rate
        # the speed must be set at 9600 bps
        a = open("cfg.txt","r")
        data = a.read().split("\n")
        data.pop()
        a.close()
        for line in data:
            exec line
        self.COM = COM
        self.SPEED = SPEED
        # self.S is the handle for the serial port.
        self.S = None
        self._lock = threading.Lock()
        self._data_collection = False
        self._data_collection_timer = None
        self._data_collection_file = None
        self._last_value = 0
        self._timeOf_last = 0
        skip = False
        try:
            self.S = serial.Serial(COM, SPEED)
        except:
            #print "cannot connect to device at com:",COM," speed:",SPEED
            message = []
            message.append(["ARDUINOSTAT", 0])
            message.append(["SCROLL", "Arduino does not respond on the specified COM. Please exit the program."])
            self._parent.put_nowait([0, message])
            skip = True

        if not skip:
            # the program will write a zero byte to arduino, signalling that the pc requires a connection. Arduino's internal
            # program will then set the board to a "need calibration" state.
            time.sleep(1.0)
            self.S.write(chr(0))
            time.sleep(1.0)
            self.S.read(self.S.in_waiting)
            # various flags
            self._motor_enabled = False
            self._motor_calib = False

            # all ready with arduino, posting events to main window
            message = []
            message.append(["ARDUINOSTAT", 1])
            message.append(["SCROLL", "Arduino reports OK, please begin calibration."])
            self._parent.put_nowait([0, message])

    # commands to arduino are encoded as six bits bytes
    def _CMDencode(self, first, second):
        b0 = bin(first)[::-1][:-2][::-1]
        b1 = bin(second)[::-1][:-2][::-1]
        while len(b0)<2:
            b0 = '0'+b0
        while len(b1)<4:
            b1 = '0'+b1
        n = b0+b1
        exec "n = 0b"+n
        return chr(n)

    # converts bits into true and false boolean values
    def _BinToBool(self, byte):
        print ord(byte)
        b = bin(ord(byte))[::-1][:-2][::-1]
        while len(b)<8:
            b = '0'+b
        sequence = []
        for i in range(0,len(b),1):
            if b[7-i] == '0':
                sequence.append(False)
            else:
                sequence.append(True)
        return sequence

    # convertes bytes into 256base integers.
    def _B256ToInt(self, MSB, LSB):
        return (MSB*256)+LSB

    # acquires lock to write on the serial port, then releases it
    def _timing_function(self):
        self._lock.acquire()
        self.S.write(self._CMDencode(0,9))
        self._lock.release()

    # when the user enables the pressure sampling, this function will fire automatically each second, prompting
    # arduino to sample its adc.
    def _data_collection_worker(self, ADC_conv):
        # this function is called when data collection is on
        if (time.time() - self._timeOf_last) >= 1.0:
            self._timeOf_last = time.time()
            if abs(ADC_conv - self._last_value) > 8:
                self._data_collection_file.write(str(self._timeOf_last)+"\t"+str(ADC_conv)+"\r\n")
                self._last_value = ADC_conv
            # starting the timer
            self._data_collection_timer = threading.Timer(1.0, self._timing_function)
            self._data_collection_timer.start()
        # all done

    # this method runs the thread, until a "Stop" event is captured on the internal queue.
    def run(self):
        _go = True
        while _go:
            # checking the queue
            try:
                prio, message = self._q.get_nowait()
                if message[0] == "Stop":
                    # halts everything
                    # forces arduino to reset by closing, opening and then closing again the serial connection.
                    self._lock.acquire()
                    self.S.close()
                    time.sleep(1.0)
                    self.S.open()
                    self.S.close()
                    self._lock.release()
                    _go = False
                    continue;
                elif message[0] == "Calibrate":
                    # performs calibration sending arduino the proper command.
                    self._lock.acquire()
                    self.S.write(self._CMDencode(0,6))
                    self._lock.release()
                    # now to wait for response when calibration has finished
                elif message[0] == "PowerUP":
                    # powers up the motor
                    self._lock.acquire()
                    self.S.write(self._CMDencode(0,0))
                    self._lock.release()
                elif message[0] == "PowerDOWN":
                    # powers down the motor
                    self._lock.acquire()
                    self.S.write(self._CMDencode(0,1))
                    self._lock.release()
                elif message[0] == "ChangeHOME":
                    # changes home position (0 = LEFT, 1 = RIGHT)
                    if message[1] == 0:
                        # change to LEFT
                        self._lock.acquire()
                        self.S.write(self._CMDencode(0,5))
                        self._lock.release()
                    elif message[1] == 1:
                        # change to RIGHT
                        self._lock.acquire()
                        self.S.write(self._CMDencode(0,4))
                        self._lock.release()
                elif message[0] == "ChangeDIR":
                    # changes rotation direction (0 = LEFT, 1 = RIGHT)
                    if message[1] == 0:
                        # change to LEFT
                        self._lock.acquire()
                        self.S.write(self._CMDencode(0,3))
                        self._lock.release()
                    elif message[1] == 1:
                        # change to RIGHT
                        self._lock.acquire()
                        self.S.write(self._CMDencode(0,2))
                        self._lock.release()
                elif message[0] == "ParkSource":
                    # rotates the source until it hits a microswitch in the desired "HOME" position.
                    self._lock.acquire()
                    self.S.write(self._CMDencode(0,7))
                    self._lock.release()
                elif message[0] == "CenterSource":
                    # rotates the source until it reaches the center point between the LEFT and RIGHT HOME positions.
                    # WARNING: this is not a "real center" position, and it changes everytime the calibration changes.
                    # true center is obtainable by measuring the beam profile.
                    self._lock.acquire()
                    self.S.write(self._CMDencode(0,8))
                    self._lock.release()
                elif message[0] == "ToggleDataLogging":
                    # enables/disables pressure data collection and saves the output to a "run_Pressure" file.
                    if not self._data_collection:
                        # arduino is not taking data --> need to start
                        path = message[1]+"/run_Pressure_"
                        # now to add a number
                        listpath = os.listdir(message[1])
                        next_pindex = -1
                        for pressfile in listpath:
                            if pressfile.startswith("run_Pressure_"):
                                pindex = pressfile.split("run_Pressure_")[1]
                                pindex = int(pindex.split(".txt")[0])
                                if pindex > next_pindex:
                                    next_pindex = pindex
                        next_pindex += 1
                        path += str(next_pindex)+".txt"
                        self._data_collection_file = open(path,"w")
                        self._data_collection = True
                        self._lock.acquire()
                        self.S.write(self._CMDencode(0,9))
                        self._lock.release()
                    else:
                        # stop
                        self._data_collection_file.close()
                        self._data_collection = False
                elif message[0] == "Reset":
                    # Resets the whole program
                    self._motor_calib = False
                    if self._data_collection:
                        self._data_collection = False
                        self._data_collection_file.close()
                    self._lock.acquire()
                    self.S.close()
                    time.sleep(1.0)
                    self.S.open()
                    time.sleep(1.0)
                    self.S.close()
                    time.sleep(1.0)
                    self.S.open()
                    self._lock.release()
                elif message[0] == "Rotate":
                    # now to rotate the arm the specified number of steps
                    # the number of steps is encoded this way:
                    b = bin(message[1])[::-1][:-2][::-1]
                    #print message[1],b
                    while len(b) < 10:
                        b = '0' + b
                    # reading chunks
                    first_4 = ''
                    for i in range(0,4,1):
                        first_4 += b[i]
                    second_4 = ''
                    for i in range(4,8,1):
                        second_4 += b[i]
                    third_4 = ''
                    for i in range(8,10,1):
                        third_4 += b[i]
                    while len(third_4)<4:
                        third_4 = '0' + third_4
                    #print b
                    # now converting
                    exec "first = 0b"+first_4
                    exec "second = 0b"+second_4
                    exec "third = 0b"+third_4
                    self._lock.acquire()
                    self.S.write(self._CMDencode(1,first))
                    self.S.write(self._CMDencode(2,second))
                    self.S.write(self._CMDencode(3,third))
                    #print first, second, third
                    self._lock.release()
                self._q.task_done()
            except Queue.Empty as e:
                pass
            #
            # checking the serial port for incoming messages from arduino
            #
            self._lock.acquire()
            if (self.S.in_waiting >= 10):
                # a response is present
                message = []
                status_byte = self._BinToBool(self.S.read())
                if (status_byte[0]) and (not self._motor_enabled):
                    # motor was switched on
                    self._motor_enabled = True
                    message.append(["SCROLL","Arduino reports motor power ON!"])
                    message.append(["MPOW", "on"])
                    # all done for this
                elif (not status_byte[0]) and (self._motor_enabled):
                    # motor was switched off
                    self._motor_enabled = False
                    message.append(["SCROLL","Arduino reports power OFF!"])
                    message.append(["MPOW", "off"])
                    # all done for this
                # the other status
                if (status_byte[1]) and (not self._motor_calib):
                    # calibration completed
                    self._motor_calib = True
                    # now to signal the textgui
                    message.append(["SCROLL","Arduino reports calibration OK!"])
                    message.append(["MCAL", 2])
                    # all ok
                if status_byte[2]:
                    # right microswitch
                    message.append(["SCROLL", "Arduino reports RIGHT microswitch was HIT"])
                if status_byte[3]:
                    # left microswitch
                    message.append(["SCROLL", "Arduino reports LEFT microswith was HIT"])
                if (status_byte[4]) and (not status_byte[5]):
                    # home position is RIGHT
                    message.append(["SCROLL", "Arduino reports HOME position is RIGHT"])
                    message.append(["MHPOS", "RIGHT"])
                elif (not status_byte[4]) and (status_byte[5]):
                    # home position is LEFT
                    message.append(["SCROLL", "Arduino reports HOME position is LEFT"])
                    message.append(["MHPOS", "LEFT"])
                if (status_byte[6]) and (not status_byte[7]):
                    # rotation direction is RIGHT
                    message.append(["SCROLL", "Arduino reports ROT direction is RIGHT"])
                    message.append(["MRDIR", "RIGHT"])
                elif (not status_byte[6]) and (status_byte[7]):
                    # rotation direction is LEFT
                    message.append(["SCROLL", "Arduino reports ROT direction is LEFT"])
                    message.append(["MRDIR", "LEFT"])
                # getting the other bytes that signal the board status
                source_position = self._B256ToInt(ord(self.S.read()), ord(self.S.read()))
                HOME_RIGHT_position = self._B256ToInt(ord(self.S.read()), ord(self.S.read()))
                HOME_LEFT_position = self._B256ToInt(ord(self.S.read()), ord(self.S.read()))
                ADC_value = self._B256ToInt(ord(self.S.read()), ord(self.S.read()))
                SYSTEM_FAILURE = ord(self.S.read())

                # checking data collection
                if self._data_collection:
                    self._data_collection_worker(ADC_value)

                # sending data
                angled = source_position*0.9
                message.append(["SPOS", source_position])
                message.append(["SRIGHT", HOME_RIGHT_position])
                message.append(["SLEFT", HOME_LEFT_position])
                message.append(["PVAL", ADC_value])

                # checking system failure
                # system failure occurs when a command that was issued by the user didn't get executed in a reasonable
                # amount of time. For instance, if the user rotates the source, but the rotation is not completed after
                # a certain amount of time has passed, the program assumes that there's something wrong mechanically,
                # thus instructs the user to check the chamber. (It may happen that the source gets trapped with cables, that
                # a microswitch is defective, etc).
                if SYSTEM_FAILURE==1:
                    # a system failure occurred --> so disabling everything
                    message.append(["SCROLL","Arduino reports a system FAILURE occurred (mechanical problem inside the chamber)."])

                # sending the event over
                self._parent.put_nowait([0, message])

            # releasing the lock on the serial port
            self._lock.release()

            # waiting a little bit to avoid excessive cpu usage.
            time.sleep(0.001)
