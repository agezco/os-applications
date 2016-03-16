import os
import sys
import syslog

from pytcos.Config import Config

class Logger(Config):
    def __init__(self):
        self.LOG = []

    def log(self, log_level, log_string):
        # remap our log levels:
        # 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR
        # according to syslog
        SYSLOG_LEVEL = [(7, "DEBUG"), (6, "INFO"), (4, "WARNING"), (3, "ERROR")]
        log_level_syslog = SYSLOG_LEVEL[log_level][0]
        log_level_string = SYSLOG_LEVEL[log_level][1]

        # prepare error string
        e = os.path.basename(sys.argv[0]) + ": " + \
            "[" + log_level_string + "] in: " + \
            self.__class__.__name__ + "." + \
            sys._getframe(1).f_code.co_name + "(): " + \
            log_string

        # add error string to self.LOG
        self.LOG.append(self.__class__.__name__ + "." + \
                     sys._getframe(1).f_code.co_name + "(): " + \
                     log_string)

        # write error to stderr and syslog
        sys.stderr.write(e + "\n")
        syslog.syslog(log_level_syslog, e)