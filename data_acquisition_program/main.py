import textint, arduino, scope, sys, threading, multiprocessing

# starting the picoscope process

#print "Starting PicoScope working process..."
PS = scope.PicoScope_Process()
PS.start()


# checking whether text or GUI is requested
#print "Starting in TEXT mode..."
GUI = textint.RuShield()
GUI.ps_input_queue = PS.q_in
GUI.ps_output_queue = PS.q_out
GUI.StartPSworker()

# instantiating arduino
#print "Starting ARDUINO serial back-end..."
ARD = arduino.Arduino(GUI.i_q, GUI.q)
ARD.start()

# mainloop
GUI.MainLoop()

# checking that all threads have ended
ARD.join()
GUI.ps_worker.join()
PS.join()

# end
print "All done."