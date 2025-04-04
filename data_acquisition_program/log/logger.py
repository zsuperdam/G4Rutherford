import time
"""
The session logger provides for a facility to save to disk a log where events are recorded for subsequent analysis.
"""
class SessionLogger:
    def __init__(self):
        #filename = "PicoScopeLog_"+time.strftime("%d%b%Y_%H%M%S",time.localtime())+".txt"
        filename = "PicoScopeLog.txt"
        self.f = open(filename, "w")

    def _getDate(self, type):
        if type==0:
            return time.strftime("%d%b%Y_%H%M%S",time.localtime())
        else:
            return time.strftime("%H%M%S",time.localtime())

    def start(self):
        out = self._getDate(1)+">: START LOG"+"\r\n"
        self.f.write(out)

    def end(self):
        out = self._getDate(1)+">: END LOG"+"\r\n"
        self.f.write(out)
        self.f.close()

    def info(self, message):
        self._writeLog("INFO", message)

    def error(self, message):
        self._writeLog("ERROR", message)

    def warning(self, message):
        self._writeLog("WARNING", message)

    def _writeLog(self, prefix, message):
        out = self._getDate(1)+"."+prefix+" >: "+message
        self.f.write(out+"\r\n")
