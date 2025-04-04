import multiprocessing, threading, Queue
from log import logger
from device import ps5244B as PicoScope
import sys, os, time

def Header():
    return time.strftime("%d%h%Y_%H%M%S",time.localtime())+"[PicoScope] >: "

"""
This module implements the PicoScope process. It runs the picoscope in a completely separate process from the main one.
Proper communication and synchronization is ensured via Queues.
"""
class PicoScope_Process(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        # doing stuff here
        self.q_out = multiprocessing.Queue()
        self.q_in = multiprocessing.Queue()
        self.output_path = None
        self.runfile_path = None
        self.log = None
        # all set

    def run(self):
        _go = True
        while _go:
            # listens
            data = self.q_in.get()
            if data[0] == "StopProcess":
                # terminates the process
                _go = False
                continue;
            elif data[0] == "StartRun":
                # logger
                self.log = logger.SessionLogger()
                # starts the scope
                output_path = data[1]
                runfile_path = data[2]
                # starting
                self.log.start()
                ps = PicoScope.ps5244B(self.log, self.q_out)
                output = ps.run(runfile_path)
                # when here the picoscope has finished doing its thing
                self.q_out.put_nowait(["downloading data from the scope (this may take a while, be patient...)"])
                # output handling
                for i in range(0, len(output), 1):
                    #fname_MCA = open(output_path+"/"+"run_" + str(i) + "_MCA.txt", "w")
                    self.q_out.put_nowait(["downloading data for run #"+str(i)+"..."])
                    for segment in range(0, len(output[i][0]), 1):
                        fname = "run_" + str(i) + "_segment_" + str(segment) + ".txt"
                        #max_value = 0
                        f = open(fname, "w")
                        for n in range(0, len(output[i][0][segment]), 1):
                            f.write(str(output[i][0][segment][n]) + "\r\n")
                            #if (output[i][0][segment][n] > max_value):
                            #    max_value = output[i][0][segment][n]
                        f.close()
                        # compressing segment file
                        os.system("zip "+output_path+"/"+fname+".zip "+fname)
                        # removing segment file to free up space
                        os.system("rm "+fname)
                        # saving value as MCA
                        # fname_MCA.write(str(max_value) + "\r\n")
                    # closing MCA file
                    # fname_MCA.close()
                # done with the scope for now
                ps.StopUnit()
                ps.CloseUnit()
                self.q_out.put_nowait(["DONE"])
                self.log.end()
                # moving the txt files in the appropriate folder
                os.system("mv PicoScopeLog.txt "+output_path+"/")
                os.system("mv run_BlockTimes.txt "+output_path+"/")
                os.system("mv run_Pressure_*.txt "+output_path+"/")
                # done


# worker thread to be run inside the GUI that reads the process' output queue
class PicoScope_WorkerThread(threading.Thread):
    def __init__(self, process_output_queue, parent):
        threading.Thread.__init__(self)
        self.PS_output_queue = process_output_queue
        self.my_queue = Queue.Queue()
        self._parent = parent

    def run(self):
        _go = True
        while _go:
            # thread-thread control queue
            try:
                data = self.my_queue.get_nowait()
                if data[0] == "Stop":
                    # stops the WorkerThread
                    _go = False
                    continue;
                self.my_queue.task_done()
            except Queue.Empty as err:
                pass
            # process-thread event queue
            try:
                data = self.PS_output_queue.get(timeout=1)
                # should receive stuff to pass to parent as update events
                # check if final one
                if data[0] == "DONE":
                    # the scope finished, so posting the task done event
                    message = []
                    message.append(["SCROLL", "PicoScope finished."])
                    self._parent.i_q.put_nowait([0, message])
                else:
                    # stuff to pass to the log output
                    message = []
                    message.append(["SCROLL", Header()+data[0]])
                    self._parent.i_q.put_nowait([0, message])
                # all done
            except:
                pass
            # done
