#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# TEXT VERSION OF THE GUI

import Queue, os, time, threading
import scope as PicoDevice

"""
import wx, Queue, wxevents, os, time, threading
import scope as PicoDevice
import script as RuShieldScript
"""

def Header():
    return time.strftime("%d%h%Y_%H%M%S",time.localtime())+"[PicoScope] >: "

ansi_colors = {'background':{}, 'foreground':{}, 'textatt':{}}
ansi_colors['background']['black'] = 40
ansi_colors['background']['red'] = 41
ansi_colors['background']['green'] = 42
ansi_colors['background']['yellow'] = 43
ansi_colors['background']['blue'] = 44
ansi_colors['background']['magenta'] = 45
ansi_colors['background']['cyan'] = 46
ansi_colors['background']['white'] = 47

ansi_colors['foreground']['black'] = 30
ansi_colors['foreground']['red'] = 31
ansi_colors['foreground']['green'] = 32
ansi_colors['foreground']['yellow'] = 33
ansi_colors['foreground']['blue'] = 34
ansi_colors['foreground']['magenta'] = 35
ansi_colors['foreground']['cyan'] = 36
ansi_colors['foreground']['white'] = 37

ansi_colors['textatt']['reset'] = 0
ansi_colors['textatt']['bold'] = 1
ansi_colors['textatt']['blink'] = 5
ansi_colors['textatt']['reverse'] = 7

fillst = ""
for i in range(0,128,1):
    fillst += "-"


def PUT(row, col, text, bcolor="black", tcolor="white", tatt="reset", fill=False):
    fillout = ""
    if fill:
        for j in range(col+1,131-len(text),1):
            fillout += chr(32)
    return chr(27)+"["+str(row)+";"+str(col)+"H"+chr(27)+"["+str(ansi_colors['textatt'][tatt])+";"+str(ansi_colors['foreground'][tcolor])+";"+str(ansi_colors['background'][bcolor])+"m"+text+fillout+chr(27)+"[0m"

def SETCURSOR(row,col):
    return chr(27)+"["+str(row)+";"+str(col)+"H"

def PRINTGOOD(text, prog):
    print SETCURSOR(42,1)+text+SETCURSOR(42,130)+"|\r\n"+SETCURSOR(44,1)+chr(27)+"[K"+"$RuShield ("+str(prog)+"):",

"""
This module contains the text conversion of the GUI program
"""

# MAIN WINDOW SPECIFICATION
class MainFrame:
    def __init__(self):
        self.entry_number = 0
        # drawing the main window in a telnet mode, 130x45 window size
        st = chr(27)+"[2J"+chr(27)+"[1;1H"+"+"
        for i in range(1,129,1):
            st += "-"
        st += "+"
        for i in range(2,44,1):
            st += chr(27)+"["+str(i)+";1H"+"|"+chr(27)+"["+str(i)+";130H"+"|"
        st += chr(27)+"[44;1H"+"+"
        for i in range(1,129,1):
            st += "-"
        st += "+"
        print st
        # drawing the buttons and stuff
        print PUT(2,2,"RUTHERFORD SCATTERING - RuShield Interface","blue","red","bold",False)
        print PUT(1,44,"+")
        print PUT(2,44,"|")
        print PUT(2,45,"Arduino Board @ ")

        a = open("./cfg.txt","r")
        data = a.read()
        a.close()
        data = data.split("\n")
        com_port = data[0].split("COM = ")[1]
        speed_port = data[1].split("SPEED = ")[1]
        print PUT(2,45,"Arduino Board @ COM: "+com_port+" SPEED: "+speed_port+" bps STATUS: ")
        print PUT(2,113,"trying...","green","red","blink")

        print PUT(3,1,"+","black","white","reset")
        print PUT(3,130,"+","black","white","reset")
        print PUT(3,2,fillst,"black","white","reset")
        print PUT(3, 44, "+")
        # drawing the MOTOR section
        print PUT(4,2,"MOTOR ROTATION CONTROL","red","white","reset")
        print PUT(5,2,"DESCRIPTION","black","magenta","reset")
        print PUT(5,25,"VAR","black","magenta","reset")
        print PUT(5,35,"STATUS","black","magenta","reset")
        print PUT(6,2,"Motor CALIBRATION")
        print PUT(6,25,"MCAL")
        print PUT(6,35,"not calibrated","black","red","bold")
        print PUT(7,2,"Motor POWER")
        print PUT(7,25,"MPOW")
        print PUT(7,35,"off","black","red","bold")
        print PUT(8,2,"Motor STEP ANGLE")
        print PUT(8,25,"MSTEP")
        print PUT(8,35,"0.9 deg","black","yellow","reset")
        print PUT(9,2,"Motor ROTATION DIR")
        print PUT(9,25,"MRDIR")
        print PUT(9,35,"-","black","yellow","reset")
        print PUT(10,2,"Motor HOME POS")
        print PUT(10,25,"MHPOS")
        print PUT(10,35,"-","black","yellow","reset")

        # pressure section
        print PUT(12,2,"VACUUM CHAMBER","red","white","reset")
        print PUT(13,2,"DESCRIPTION","black","magenta","reset")
        print PUT(13,25,"VAR","black","magenta","reset")
        print PUT(13,35,"STATUS","black","magenta","reset")
        print PUT(14,2,"Pressure Gauge")
        print PUT(14,25,"-")
        print PUT(14,35,"0","black","yellow","reset")
        print PUT(15,2,"Data collection")
        print PUT(15,25,"PDC")
        print PUT(15,35,"idle","black","yellow","reset")

        # source section
        print PUT(17,2,"SOURCE INFORMATION","red","white","reset")
        print PUT(18,2,"Source POSITION")
        print PUT(18,25,"-")
        print PUT(18,35,"calibrate first!","black","red","bold")
        print PUT(19,2,"Source LEFT position")
        print PUT(19,25,"-")
        print PUT(19,35,"-","black","yellow","reset")
        print PUT(20,2,"Source RIGHT position")
        print PUT(20,25,"-")
        print PUT(20,35,"-","black","yellow","reset")
        print PUT(21,2,"Source STATUS")
        print PUT(21,25,"-")
        print PUT(21,35,"idle","black","yellow","reset")
        print PUT(22,2,"Source ANGLE")
        print PUT(22,25,"-")
        print PUT(22,35,"-","black","yellow","reset")
        print PUT(24,2,"LEFT","blue","white","bold")
        print PUT(24,45,"RIGHT","blue","white","bold")

        # drawing the PICOSCOPE section
        print PUT(4,70,"PICOSCOPE CHANNEL SETTINGS","red","white","reset")
        print PUT(5,70,"DESCRIPTION","black","magenta","reset")
        print PUT(5,95,"VAR","black","magenta","reset")
        print PUT(5,105,"STATUS","black","magenta","reset")
        print PUT(6,70,"input CHANNEL")
        print PUT(6,95,"ICH")
        print PUT(6,105,"A","black","yellow","reset")
        print PUT(7,70,"voltage RANGE")
        print PUT(7,95,"VRANGE")
        print PUT(7,105,"+/- 5V","black","yellow","reset")
        print PUT(8,70,"ADC RESOLUTION")
        print PUT(8,95,"ARES")
        print PUT(8,105,"12 bit","black","yellow","reset")

        print PUT(10,70,"PICOSCOPE TRIGGER SETTINGS","red","white","reset")
        print PUT(11,70,"trigger SOURCE")
        print PUT(11,95,"TCH")
        print PUT(11,105,"A","black","yellow","reset")
        print PUT(12,70,"trigger LEVEL")
        print PUT(12,95,"TLEV")
        print PUT(12,105,"+ 500 mV","black","green","reset")
        print PUT(13,70,"trigger DIRECTION")
        print PUT(13,95,"TDIR")
        print PUT(13,105,"Falling","black","cyan","reset")
        print PUT(14,70,"PRETRIGGER fraction")
        print PUT(14,95,"PTFR")
        print PUT(14,105,"0.4","black","yellow","reset")

        print PUT(16,70,"PICOSCOPE SAMPLES AND MEMORY SETTINGS","red","white","reset")
        print PUT(17,70,"Sample RATE")
        print PUT(17,95,"SRATE")
        print PUT(17,105,"200 MS/s","black","yellow","reset")
        print PUT(18,70,"Samples/div")
        print PUT(18,95,"SDIV")
        print PUT(18,105,"500","black","yellow","reset")
        print PUT(19,70,"# of memory segments")
        print PUT(19,95,"MEMSEG")
        print PUT(19,105,"1","black","yellow","reset")
        print PUT(20,70,"MAX data collect. TIME")
        print PUT(20,95,"DCTIME")
        print PUT(20,105,"0h 0m 0s","black","cyan","reset")
        print PUT(21,70,"MAX # of events")
        print PUT(21,95,"DCEVS")
        print PUT(21,105,"0","black","cyan","reset")

        print PUT(23,70,"DATA OUTPUT PATH","red","white","reset")
        print PUT(24,70,"please input a valid path","black","yellow","reset")

        # straight line to divide the setup section from the running and command sections
        print PUT(25,1,"+")
        print PUT(25,130,"+")
        print PUT(25,2,fillst)

        # data collection control
        print PUT(26,2,"DATA COLLECTION RUN STATUS","red","white","reset","True")
        print PUT(27,2,"STARTED @")
        print PUT(27,25,"please start a run","black","yellow","reset")
        print PUT(28,2,"TIME completion")
        print PUT(28,25," 0%","green","red","reset",True)
        print PUT(29,2,"EVENT completion")
        print PUT(29,25," 0%","green","red","reset",True)
        print PUT(30,2,"ENDED @")
        print PUT(30,25,"please start a run","black","yellow","reset")
        print PUT(31,1,"+")
        print PUT(31,130,"+")
        print PUT(31,2,fillst)

        # scrolling region
        print chr(27)+"[32;42r"

        print PUT(43,1,"+")
        print PUT(43, 130, "+")
        print PUT(43,2,fillst)

        # command prompt
        print chr(27)+"[44;1H"+chr(27)+"[K"
        print PUT(44,1,"$RuShield (0): ")
        print SETCURSOR(44, 15),

    def Destroy(self):
        # basically it just exits
        print chr(27)+"[2J"+chr(27)+"[1;1H"+chr(27)+"[0m",

    def Refresh(self, sysinst):
        # redraws the values on the screen
        if sysinst.sysvar['MCAL']['value'] == 2:
            print PUT(6, 35, "calibrated    ","black","green","bold")
        elif sysinst.sysvar['MCAL']['value'] == 1:
            print PUT(6, 35, "calibrating...","green","red","blink")
        elif sysinst.sysvar['MCAL']['value'] == 0:
            print PUT(6, 35, "not calibrated", "black", "red", "bold")

        if sysinst.sysvar['MPOW']['value'] == "off":
            print PUT(7, 35, "off           ", "black", "red", "bold")
        elif sysinst.sysvar['MPOW']['value'] == "on":
            print PUT(7, 35, "on            ", "black", "green", "bold")
        elif sysinst.sysvar['MPOW']['value'] == "powering":
            print PUT(7, 35, "powering up...", "green", "red", "blink")

        print PUT(8, 35, str(sysinst.sysvar['MSTEP']['value'])+" deg", "black", "yellow", "reset")

        if sysinst.sysvar['MRDIR']['value'] == "LEFT":
            print PUT(9, 35, "LEFT ", "black", "yellow", "reset")
        elif sysinst.sysvar['MRDIR']['value'] == "RIGHT":
            print PUT(9, 35, "RIGHT", "black", "yellow", "reset")

        if sysinst.sysvar['MHPOS']['value'] == "LEFT":
            print PUT(10, 35, "LEFT ", "black", "yellow", "reset")
        elif sysinst.sysvar['MHPOS']['value'] == "RIGHT":
            print PUT(10, 35, "RIGHT", "black", "yellow", "reset")

        print PUT(14, 25, str(sysinst.sysvar['PVAL']['value'])+"    ")

        if sysinst.sysvar['PDC']['value'] == "off":
            print PUT(15, 35, "idle       ", "black", "yellow", "reset")
        elif sysinst.sysvar['PDC']['value'] == "on":
            print PUT(15, 35, "sampling...", "green", "red", "blink")

        if sysinst.sysvar['SPOS']['value'] < 0:
            print PUT(18, 35, "calibrate first!", "black", "red", "bold")
        else:
            print PUT(18, 35, str(sysinst.sysvar['SPOS']['value']), "blue", "white", "bold")

        if sysinst.sysvar['SLEFT']['value'] < 0:
            print PUT(19, 35, "-", "black", "yellow", "reset")
        else:
            print PUT(19, 35, str(sysinst.sysvar['SLEFT']['value']), "black", "yellow", "reset")

        if sysinst.sysvar['SRIGHT']['value'] < 0:
            print PUT(20, 35, "-", "black", "yellow", "reset")
        else:
            print PUT(20, 35, str(sysinst.sysvar['SRIGHT']['value']), "black", "yellow", "reset")

        if sysinst.sysvar['SSTAT']['value'] == 0:
            print PUT(21, 35, "idle", "black", "yellow", "reset")
        else:
            print PUT(21, 35, "rotating...", "green", "red", "blink")

        print PUT(6, 105, sysinst.sysvar['ICH']['value'], "black", "yellow", "reset", True)
        print PUT(7, 105, "+/- "+sysinst.sysvar['VRANGE']['value'], "black", "yellow", "reset", True)
        print PUT(8, 105, sysinst.sysvar['ARES']['value'], "black", "yellow", "reset", True)

        print PUT(11, 105, sysinst.sysvar['TCH']['value'], "black", "yellow", "reset", True)
        if sysinst.sysvar['TLEV']['value'] >= 0:
            print PUT(12, 105, str(sysinst.sysvar['TLEV']['value'])+" mV", "black", "green", "reset", True)
        elif sysinst.sysvar['TLEV']['value'] < 0:
            print PUT(12, 105, str(sysinst.sysvar['TLEV']['value']) + " mV", "black", "red", "reset", True)

        print PUT(13, 105, sysinst.sysvar['TDIR']['value'], "black", "cyan", "reset", True)
        print PUT(14, 105, str(sysinst.sysvar['PTFR']['value']), "black", "yellow", "reset", True)
        print PUT(17, 105, sysinst.sysvar['SRATE']['value'], "black", "yellow", "reset", True)
        print PUT(18, 105, str(sysinst.sysvar['SDIV']['value']), "black", "yellow", "reset", True)
        print PUT(19, 105, str(sysinst.sysvar['MEMSEG']['value']), "black", "yellow", "reset", True)
        print PUT(20, 105, sysinst.sysvar['DCTIME']['value'], "black", "cyan", "reset", True)
        print PUT(21, 105, str(sysinst.sysvar['DCEVS']['value']), "black", "cyan", "reset", True)


        print PUT(24, 70, str(sysinst.sysvar['OUT']['value']), "blue", "white", "reset", True)

        if sysinst.sysvar['ARDUINOSTAT']['value']==0:
            print PUT(2, 113, "FAIL", "black", "red", "bold", True)
        elif sysinst.sysvar['ARDUINOSTAT']['value']==1:
            print PUT(2, 113, "OK", "black", "green", "bold", True)
        elif sysinst.sysvar['ARDUINOSTAT']['value']==2:
            print PUT(2, 113, "connecting...", "green", "red", "blink", True)

        # computing the source position and various stuff
        if sysinst.sysvar['MCAL']['value'] == 2:
            center = abs(sysinst.sysvar['SLEFT']['value'] - sysinst.sysvar["SRIGHT"]['value'])/2
            shift = (center-sysinst.sysvar['SPOS']['value'])*0.9

            # scrivo il numero deg
            if shift < 0:
                # questo vuol dire che siamo "dopo" di center.
                if sysinst.sysvar['SLEFT']['value'] < sysinst.sysvar['SRIGHT']['value']:
                    # vuol dire che siamo nella zona di destra degli angoli positivi
                    shift *= -1
                # altrimenti zona di sinistra degli angoli negativi
            elif shift > 0:
                # siamo dopo il center
                if sysinst.sysvar['SLEFT']['value'] < sysinst.sysvar['SRIGHT']['value']:
                    # siamo nella zona di sinistra degli angoli negativi
                    shift *= -1

            print PUT(22, 35, str(shift) + " deg", "black", "yellow", "reset")

            # cleaning the bar
            st = ""
            for j in range(0,50,1):
                st += chr(32)
            print PUT(23,2,st)

            # il segno dipende dal fatto che io stia ruotando verso destra o verso sinistra
            # se sto ruotando verso destra, a prescindere dallo shift, devo disegnare la barra verso destra perche'
            # mi indica il mio spostamento. verso destra ci sono poi gli angoli positivi perche' assumo sia tipo
            # l'asse orientato delle ascisse (per convenzione)

            # per rappresentare pero' devo fare attenzione perche'
            # se ad esempio SLEFT = 320 e spos = 200, non sono a destra, ma sono a sinistra perche' la sinistra e' maggiore.
            # potrei rappresentare di meno
            # ad esempio uno shift di +/- 60 attorno al centro

            wh = int(25.0 * sysinst.sysvar['SPOS']['value'] / center)
            if wh < 3:
                wh = 3
            if (sysinst.sysvar['SLEFT']['value'] > sysinst.sysvar['SRIGHT']['value']):
                # la sinistra e' maggiore quindi incrementando il numero di step, vado verso sinistra
                wh = 50 - wh
            # altrimenti nell'altro caso sono gia a posto
            if wh < 25:
                st = "^"
                for j in range(wh, 25, 1):
                    st += "-"
                st += "+"
                print PUT(23, wh-1, st, "green", "white", "reset")
            elif wh == 25:
                print PUT(23, 25, "+", "blue", "white", "bold")
            else:
                st = "+"
                for j in range(25, wh, 1):
                    st += "-"
                st += "^"
                print PUT(23, 25, st, "green", "white", "reset")


class RuShield:
    # when the program is run, this method is executed first.
    def __init__(self):
        # instantiating the MainFrame object (specified above)
        self.frame = MainFrame()

        # properties
        self.q = Queue.PriorityQueue(-1) # questa e' la coda condivisa con il thread di arduino, da questo lato si SCRIVE

        self.i_q = Queue.PriorityQueue(-1) # questa e' la coda condivisa con altra roba, da questo lato si LEGGE

        # picoscope interface
        self.ps_input_queue = None
        self.ps_output_queue = None
        self.ps_worker = None

        # system variables
        self.sysvar = {}
        self.sysvar['MCAL'] = {'value': 0, 'type': "int"}
        self.sysvar['MPOW'] = {'value': "off", 'type': "string"}
        self.sysvar['MSTEP'] = {'value': "0.9", 'type': "float"}
        self.sysvar['MRDIR'] = {'value': "LEFT", 'type': "string"}
        self.sysvar['MHPOS'] = {'value': "LEFT", 'type': "string"}
        self.sysvar['PDC'] = {'value': "off", 'type': "string"}
        self.sysvar['ICH'] = {'value': "A", 'type': "string"}
        self.sysvar['VRANGE'] = {'value': "5V", 'type': "string"}
        self.sysvar['ARES'] = {'value': "12bit", 'type': "string"}
        self.sysvar['TCH'] = {'value': "A", 'type': "string"}
        self.sysvar['TLEV'] = {'value': 500.0, 'type': "float"}
        self.sysvar['TDIR'] = {'value': "Falling", 'type': "string"}
        self.sysvar['PTFR'] = {'value': 0.4, 'type': "float"}
        self.sysvar['SRATE'] = {'value': "200 MS/s", 'type': "string"}
        self.sysvar['SDIV'] = {'value': 500, 'type': "int"}
        self.sysvar['MEMSEG'] = {'value': 1, 'type': "int"}
        self.sysvar['DCTIME'] = {'value': "0h 0m 0s", 'type': "string"}
        self.sysvar['DCEVS'] = {'value': 0, 'type': "int"}

        self.sysvar['SPOS'] = {'value': -1, 'type': "int"} # source position
        self.sysvar['SPOS_BAR'] = {'value': 0, 'type': "int"} # source position graphic bar
        self.sysvar['SLEFT'] = {'value': 0, 'type': "int"} # source left position
        self.sysvar['SRIGHT'] = {'value': 0, 'type': "int"} # source right position
        self.sysvar['SSTAT'] = {'value': 0, 'type': "int"} # source status

        self.sysvar['OUT'] = {'value': "please specify a path", 'type': "string"}
        self.sysvar['ARDUINOSTAT'] = {'value': 2, 'type': "int"}
        self.sysvar['PVAL'] = {'value': 0, 'type': "int"} # pressure value



        # options for the various variables
        self.varopt = {}
        self.varopt['MPOW'] = {"off":"turn power off","on":"turn power on"}
        self.varopt['MSTEP'] = {"any":"any value from 0.9 deg up"}
        self.varopt['MRDIR'] = {"LEFT":"set rotation towards LEFT","RIGHT":"set rotation towards RIGHT"}
        self.varopt['MHPOS'] = {"LEFT":"set source HOME position to LEFT","RIGHT":"set source HOME position to RIGHT"}
        self.varopt['PDC'] = {"off":"stop sampling the pressure.","on":"start sampling the pressure"}
        self.varopt['ICH'] = {"A":"set sampling on channel A","B":"set sampling on channel B"}
        self.varopt['VRANGE'] = {"10mV":"set voltage range to +/- 10mV","20mV":"","50mV":"","100mV":"","200mV":"","500mV":"","1V":"","2V":"","5V":"","10V":"","20V":""}
        self.varopt['ARES'] = {"8bit":"set ADC resolution to 8 bits","12bit":"","14bit":"","15bit":"","16bit":""}
        self.varopt['TCH'] = {"A":"set trigger source to channel A","B":"set trigger source to channel B"}
        self.varopt['TLEV'] = {"any":"any value, in millivolts, from -5000 to +5000"}
        self.varopt['TDIR'] = {"Falling":"set trigger direction to Falling","Rising":"set trigger direction to Rising"}
        self.varopt['PTFR'] = {"any":"pre trigger fraction, any value from 0.1 to 0.9"}
        self.varopt['SRATE'] = {"any":"any value from 0 to 200, in S/s, kS/s or MS/s"}
        self.varopt['SDIV'] = {"any":"number of samples for each division."}
        self.varopt['MEMSEG'] = {"any":"how many pieces the scope's memory is segmented into."}
        self.varopt['DCTIME'] = {"any":"running time in hours, minutes and seconds."}
        self.varopt['DCEVS'] = {"any":"how many events to capture in the run."}

        # test vari
        self.varopt['MCAL'] = {"any":""}
        self.varopt['SPOS'] = {"any":""}
        self.varopt['SLEFT'] = {"any":""}
        self.varopt['SRIGHT'] = {"any":""}

        self.command_active = False
        self.which_command = ""



    # this function starts the PicoScope worker thread. A worker thread is required since PicoScope runs on an
    # entirely different process, thus a bridge is required between PicoScope process and the main process where
    # the GUI's main loop is executed.
    def StartPSworker(self):
        self.ps_worker = PicoDevice.PicoScope_WorkerThread(self.ps_output_queue, self.frame)
        self.ps_worker.start()

    # this function generates a "run file" for the picoscope process, by collecting all the values of the various properties.
    def PicoScopeStart(self, e):
        # generating the runfile
        runfile_path = self.current_path+"/run"
        f = open(runfile_path,"w")
        # obtaining the run time
        run_time = self.spin_dict["RUN_TIME_1_spin"].GetValue()*3600
        run_time+= self.spin_dict["RUN_TIME_2_spin"].GetValue()*60
        run_time+= self.spin_dict["RUN_TIME_3_spin"].GetValue()
        f.write("run_time = "+str(run_time)+"\n")
        # obtaining the n_captures
        f.write("n_captures = "+str(self.spin_dict["N_CAPTURES_spin"].GetValue())+"\n")
        # obtaining the n_segments
        f.write("n_segments = "+str(self.spin_dict["N_SEGMENTS_spin"].GetValue())+"\n")
        # obtaining the channel name
        f.write('channel_name = "'+self.combo_dict["CHANNEL_NAME_combo"].GetStringSelection()+'"\n')
        # obtaining the channel range
        f.write('channel_range = "'+self.combo_dict["CHANNEL_RANGE_combo"].GetStringSelection()+'"\n')
        # obtaining the resolution
        f.write('resolution = "'+self.combo_dict["RESOLUTION_combo"].GetStringSelection()+'"\n')
        # obtaining samples per division
        f.write("samples_per_division = "+str(self.spin_dict["SAMPLESDIV_spin"].GetValue())+"\n")
        # obtaining sample rate
        sample_rate_dict = {'S/s':1,'kS/s':1000,'MS/s':1000000,'GS/s':1000000000}
        multiplier = sample_rate_dict[self.combo_dict["SRMULTIPLIER_combo"].GetStringSelection()]
        sample_rate = multiplier*(self.spin_dict["SAMPLERATE_spin"].GetValue())
        f.write("sample_rate = "+str(sample_rate)+"\n")
        # event duration always false
        f.write("event_duration = False\n")
        # obtaining the trigger source
        f.write('trigger_source = "'+self.combo_dict["TRIGGER_SOURCE_combo"].GetStringSelection()+'"\n')
        # obtaining the trigger level
        f.write("trigger_level_mV = "+str(float(self.text_dict["TRIGGER_text"].GetValue()))+"\n")
        # obtaining the trigger direction
        f.write('trigger_direction = "'+self.combo_dict["TRIGGER_DIRECTION_combo"].GetStringSelection()+'"\n')
        # trigger timeout always zero
        f.write("trigger_timeout_ms = 0\n")
        # obtaining trigger percent
        f.write("preTrigger_percent = "+str(float(self.text_dict["PRETRIGGER_text"].GetValue()))+"\n")
        f.close()
        self.text_dict["LOG_OUTPUT_text"].AppendText(Header()+"run file written correctly at "+runfile_path)
        # signalling the process to begin data collection
        self.ps_input_queue.put_nowait(["StartRun", self.current_path, runfile_path])

    # sets the rotation angle
    def SetAngle(self, e):
        v_angle = float(self.text_dict["STEP_ANGLE_text"].GetValue())
        if (v_angle < 0):
            v_angle = 0
        elif (v_angle > 360.):
            v_angle = 360.
        steps = int(v_angle/0.9)
        self.slider_dict["STEP_ANGLE_slider"].SetValue(steps)
        if self.script_mode:
            self.script_thread.my_queue.put_nowait(["proceed"])

    # sets the trigger
    def SetTrigger(self, e):
        v_trig = int(self.text_dict["TRIGGER_text"].GetValue())
        if (v_trig < -5000):
            v_trig = -5000
        elif (v_trig > 5000):
            v_trig = 5000
        self.slider_dict["TRIGGER_slider"].SetValue(v_trig)
        if self.script_mode:
            self.script_thread.my_queue.put_nowait(["proceed"])

    # sets the trigger slider (it's just a graphic thing)
    def SliderTrigger(self, e):
        v_trig = self.slider_dict["TRIGGER_slider"].GetValue()
        self.frame.text_ctrl_4.SetValue(str(v_trig))
        if self.script_mode:
            self.script_thread.my_queue.put_nowait(["proceed"])

    # issues the rotate command to arduino
    def RotateSource(self, e):
        # rotates
        v_step = self.slider_dict["STEP_ANGLE_slider"].GetValue()
        print v_step
        if v_step > 0:
            self.q.put_nowait([1,["Rotate", v_step]])

    # resets the program
    def Reset(self, e):
        self.text_dict["LOG_OUTPUT_text"].SetValue("");
        self.q.put_nowait([0,["Reset"]])

    # sets the output save path
    def SetPath(self, e):
        self.current_path = self.text_dict["OUTPUT_PATH_text"].GetValue()
        os.system("mkdir "+self.current_path)
        self.text_dict["LOG_OUTPUT_text"].AppendText(Header()+"saving files in root directory: "+self.current_path+"\n")
        if self.script_mode:
            self.script_thread.my_queue.put_nowait(["proceed"])

    # toggles the pressure data collection ON or OFF.
    def DataCollection(self, e):
        self.text_dict["OUTPUT_PATH_text"].SetValue(self.base_path)
        self.current_path = self.text_dict["OUTPUT_PATH_text"].GetValue()+"/"+str(self.labels_dict["MOTOR_POSITION_label"].GetLabel())+"_"+time.strftime("%d%h%Y_%H%M%S",time.localtime())
        os.system("mkdir "+self.current_path)
        self.text_dict["OUTPUT_PATH_text"].SetValue(self.current_path)
        self.q.put_nowait([1,["ToggleDataLogging", self.current_path]])

    # Parks the source to the specified HOME position
    def ParkSource(self, e):
        self.q.put_nowait([1,["ParkSource"]])

    # Centers the source
    def CenterSource(self, e):
        self.q.put_nowait([1,["CenterSource"]])

    # Sets the slider for the angle of rotation (just graphics)
    def SliderRot(self, e):
        # this sets the value
        v = self.slider_dict["STEP_ANGLE_slider"].GetValue()
        # v is in STEPS
        v_deg = 0.9*v
        self.text_dict["STEP_ANGLE_text"].SetValue(str(v_deg))
        if self.script_mode:
            self.script_thread.my_queue.put_nowait(["proceed"])

    # changes the home position
    def ChangeHOME(self, e):
        self.q.put_nowait([1,["ChangeHOME",self.radio_dict["MOTOR_HOME_radio"].GetSelection()]])

    # changes the rotation direction
    def ChangeDIR(self, e):
        self.q.put_nowait([1,["ChangeDIR",self.radio_dict["MOTOR_DIRECTION_radio"].GetSelection()]])

    # Issues the power up command to arduino
    def PowerUP(self, e):
        # powers up the motor
        self.button_dict["MOTOR_POWER_ENABLE_button"].Disable()
        self.q.put_nowait([1,["PowerUP"]])

    # Issues the power down command to arduino
    def PowerDOWN(self, e):
        # powers down the motor
        self.button_dict["MOTOR_POWER_DISABLE_button"].Disable()
        self.q.put_nowait([1, ["PowerDOWN"]])

    # Calibrates the source
    def CalibrateSource(self, e):
        # performs the calibration
        self.sysvar['MCAL']['value'] = 1
        # sends request to arduino
        self.q.put_nowait([0,["Calibrate"]])

    # When the user exits the program, a "Stop" command is issued to each process and thread so that they exit normally.
    def OnClose(self, e):
        # terminating arduino thread
        self.q.put_nowait([0,["Stop"]])
        # stopping picoscope worker
        self.ps_worker.my_queue.put_nowait(["Stop"])
        # stopping picoscope process
        self.ps_input_queue.put_nowait(["StopProcess"])
        self.frame.Destroy()

    # When data arrives, this function takes care of it
    def OnUpdate(self, e):
        # when data arrives
        messages = e.GetValue()
        for message in messages:
            if message[0] == "StatusBar":
                # updating the status bar
                self.frame.frame_statusbar.SetStatusText(message[1], 0)
            elif message[0] == "LogOutput":
                # adding messages to the log
                self.frame.text_ctrl_1.AppendText(message[1])
            else:
                if "button" in message[0]:
                    if type(message[1])==type(True):
                        # boolean -> enables / disables button
                        if message[1]:
                            self.button_dict[message[0]].Enable()
                        else:
                            self.button_dict[message[0]].Disable()
                    else:
                        # changes the label
                        self.button_dict[message[0]].SetLabel(message[1])
                elif "label" in message[0]:
                    self.labels_dict[message[0]].SetLabel(message[1])
                elif "radio" in message[0]:
                    if type(message[1])==type(True):
                        if message[1]:
                            self.radio_dict[message[0]].Enable()
                        else:
                            self.radio_dict[message[0]].Disable()
                    else:
                        self.radio_dict[message[0]].SetSelection(message[1])
        # posting layout
        self.frame.sizer_26.Layout()
        self.frame.sizer_54.Layout()
        self.frame.sizer_55.Layout()
        self.frame.sizer_31.Layout()
        self.frame.sizer_33.Layout()

    # When arduino completes a task
    def OnArduinoTaskDone(self, e):
        # check script mode
        print "received arduino task done"
        if self.script_mode:
            # disabling all the buttons and stuff while in script mode
            for i in self.button_dict:
                self.button_dict[i].Disable()
            for i in self.radio_dict:
                self.radio_dict[i].Disable()
            for i in self.slider_dict:
                self.slider_dict[i].Disable()
            for i in self.spin_dict:
                self.spin_dict[i].Disable()
            for i in self.combo_dict:
                self.combo_dict[i].Disable()
            # unpausing the script
            self.script_thread.my_queue.put_nowait(["proceed"])

    # When picoscope completes a task
    def OnPicoTaskDone(self, e):
        # check script mode
        print "received picoscope task done"
        if self.script_mode:
            # disabling all the buttons and stuff while in script mode
            for i in self.button_dict:
                self.button_dict[i].Disable()
            for i in self.radio_dict:
                self.radio_dict[i].Disable()
            for i in self.slider_dict:
                self.slider_dict[i].Disable()
            for i in self.spin_dict:
                self.spin_dict[i].Disable()
            for i in self.combo_dict:
                self.combo_dict[i].Disable()
            # unpausing the script
            self.script_thread.my_queue.put_nowait(["proceed"])

    def MainLoop(self):
        # initial drawing
        self.frame.Refresh(self)
        print SETCURSOR(44, 1) + chr(27) + "[K" + "$RuShield (" + str(self.frame.entry_number + 1) + "):",
        # now to start
        while True:
            if self.command_active:
                # a command has been issued before and now it needs to complete
                prio, data = self.i_q.get()
                # now to process the response
                k = 1
                for message in data:
                    part_0, part_1 = message
                    if part_0 in self.sysvar:
                        # i have to modify the value of a system var
                        self.sysvar[part_0]['value'] = part_1
                    elif part_0 == "SCROLL":
                        # it's a text message
                        print PRINTGOOD(part_1, self.frame.entry_number+k),
                        k += 1
                # done with this task
                self.i_q.task_done()
                self.command_active = False
                self.frame.entry_number += k
                # refreshing
                self.frame.Refresh(self)
            else:
                command = raw_input()
                # now to do stuff
                print SETCURSOR(42,1)+"| "+str(self.frame.entry_number)+": "+command+SETCURSOR(42,130)+"|"+"\r\n"+SETCURSOR(44,1)+chr(27)+"[K"+"$RuShield ("+str(self.frame.entry_number+1)+"):",
                # devo interpretare il comando
                # sintassi: comando+arg1+altri args
                args = False
                if chr(32) in command:
                    cmd, args = command.split(chr(32),1)
                else:
                    cmd = command
                # check
                if cmd == "bye":
                    # exits from the program
                    self.OnClose(0)
                    print PRINTGOOD("sending the stop signal to all the threads and processes...",self.frame.entry_number+1),
                    break;
                elif cmd == "?":
                    # displays help
                    help_text = ShowHelp()
                    print PRINTGOOD(help_text,self.frame.entry_number+1)
                elif cmd == "set":
                    # getting the other commands
                    if chr(32) not in args:
                        # only "var" was specified -> displaying help for this command
                        args = args.upper()
                        if args not in self.sysvar:
                            print PRINTGOOD("no such system parameter <"+args+">",self.frame.entry_number+1),
                        else:
                            print PRINTGOOD(self.ShowVARinfo(args), self.frame.entry_number+1),
                    else:
                        var, value = args.split(chr(32),1)
                        var = var.upper()
                        if var in self.sysvar:
                            # the var is a system var, let's see if it's available
                            if var in self.varopt:
                                # available to be set-up, let's see if the value is corrected
                                if (value in self.varopt[var]) or ("any" in self.varopt[var]):
                                    # all ok, now to do a little cheking on the values and set up
                                    # assigning the correct type
                                    if self.sysvar[var]['type'] == "int":
                                        try:
                                            self.sysvar[var]['value'] = int(value)
                                        except:
                                            print PRINTGOOD("invalid data format.", self.frame.entry_number+1)
                                    elif self.sysvar[var]['type'] == "float":
                                        try:
                                            self.sysvar[var]['value'] = float(value)
                                        except:
                                            print PRINTGOOD("invalid data format.", self.frame.entry_number + 1)
                                    elif self.sysvar[var]['type'] == "bool":
                                        try:
                                            self.sysvar[var]['value'] = bool(value)
                                        except:
                                            print PRINTGOOD("invalid data format.", self.frame.entry_number + 1)
                                    else:
                                        self.sysvar[var]['value'] = str(value)
                                    print PRINTGOOD("OK!", self.frame.entry_number+1)
                                else:
                                    print PRINTGOOD("unsupported option for this VAR.", self.frame.entry_number+1)
                            else:
                                print PRINTGOOD("this VAR is not available.", self.frame.entry_number+1)
                        else:
                            print PRINTGOOD("no such system parameter <"+var+">", self.frame.entry_number+1),
                elif cmd == "out":
                    if not args:
                        print PRINTGOOD("specify an output path after <out> command.", self.frame.entry_number + 1),
                    else:
                        self.sysvar['OUT']['value'] = str(args)
                        print PRINTGOOD("OK!", self.frame.entry_number+1)
                elif cmd == "cal":
                    # starts the calibration process!
                    self.CalibrateSource(0)
                    self.command_active = True
                    self.sysvar['MCAL']['value']=1
                    # ok
                elif cmd == "rot":
                    pass
                elif cmd == "dcs":
                    pass
                else:
                    print PRINTGOOD("unrecognized command <"+cmd+">", self.frame.entry_number+1),

                # refreshing the screen
                self.frame.Refresh(self)

                # resetto il cursore
                print SETCURSOR(44,1)+chr(27)+"[K"+"$RuShield ("+str(self.frame.entry_number+1)+"):",

                # doing the next
                self.frame.entry_number += 1

    def ShowVARinfo(self, var):
        out = "ALLOWED values for var <" + var + ">\r\n"
        if var not in self.varopt:
            out += "this VAR is not available.\r\n"
        else:
            values = self.varopt[var]
            for j in values:
                out += j + " : " + values[j] + " | type = "+ self.sysvar[var]['type'] + "\r\n"
        return out

    # end of class RuShield

def ShowHelp():
    out = "LIST OF COMMANDS\r\n"
    out+= "? : displays this help.\r\n"
    out+= "set VAR value : sets the VAR parameter to the desired value.\r\n"
    out+= "out output_path: sets the output path to this value.\r\n"
    out+= "cal : does the calibration.\r\n"
    out+= "rot : does the rotation.\r\n"
    out+= "dcs : starts the data collection.\r\n"
    out+= "bye : exits the program."
    return out

