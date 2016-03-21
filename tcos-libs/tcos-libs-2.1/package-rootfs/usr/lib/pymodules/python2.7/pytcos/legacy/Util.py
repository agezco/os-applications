import commands
import os
import re
import sys
import time
import types

from Logger import Logger
from Config import Config
from Launcher import Launcher

class Util(Logger,Config):
    def __init__(self):
        # self.LOG is filled and needed by Logger.log()
        self.LOG = []

    # private
    #
    def __getFileObject(self, filename, mode="r"):
        f = None
        try:
            if os.path.exists(filename) and mode != "r":
                os.rename(filename, filename + ".tcos-old")
            f = open(filename, mode)
        except IOError, (errno, strerror):
            if errno == 2 and mode != "r":
                try:
                    os.mkdir(os.path.dirname(filename))
                    f = open(filename, mode)
                except:
                    e = "Unable to get writable file object(" + \
                        str(sys.exc_info()[0]) + "): " + \
                        "filename: " + str(filename) + \
                        ", mode: " + str(mode)
                    self.log(2, e)
                    raise
            else:
                e = "Unable to get file object(" + \
                    str(sys.exc_info()[0]) + "): " + \
                    "filename: " + str(filename) + \
                    ", mode: " + str(mode)
                self.log(2, e)
                raise
        except:
            e = "Unable to get file object(" + \
                str(sys.exc_info()[0]) + "): " + \
                "filename: " + str(filename) + \
                ", mode: " + str(mode)
            self.log(2, e)
            raise

        return f

    def __closeFileObject(self, file_object):
        try:
            file_object.close()
        except:
            e = "Unable to close file object(" + \
                str(sys.exc_info()[0]) + "): " + \
                "file_object: " + str(file_object)
            self.log(2, e)

    # public
    #
    def isMountpoint(self, mountpoint):
        m = self.__getFileObject("/proc/mounts")
        is_mountpoint = False
        for line in m.readlines():
            if line.split()[1] == mountpoint:
                is_mountpoint = True
                break
        self.__closeFileObject(m)
        return is_mountpoint

    def isMounted(self, device):
        m = self.__getFileObject("/proc/mounts")
        is_mounted = False
        for line in m.readlines():
            if line.split()[0] == device:
                is_mounted = True
                break
        self.__closeFileObject(m)
        return is_mounted

    def isRunning(self, program):
        if commands.getstatusoutput("pidof -x " + program)[0] == 0:
            return True
        else:
            return False

    def mount(self, source, destination, options=None):
        if self.isMountpoint(destination):
            e = "Destination already mounted: " + \
                "source: " + str(source) + \
                ", destination: " + str(destination) + \
                ", options: " + str(options)
            self.log(2, e)
            return False

        if not os.path.isdir(destination):
            try:
                os.makedirs(destination)
            except:
                e = "Unable to create destinaton dir(" + \
                    str(sys.exc_info()[0]) + "): " + \
                    "source: " + str(source) + \
                    ", destination: " + str(destination) + \
                    ", options: " + str(options)
                self.log(2, e)
                return False

        if options:
            option_cmd = "-o " + str(options) + " "
        else:
            option_cmd = ""

        ret_val = os.system("mount " + option_cmd + source + " " + destination)

        if ret_val != 0:
            e = "Unable to mount: " + \
                "source: " + str(source) + \
                ", destination: " + str(destination) + \
                ", options: " + str(options)
            self.log(2, e)
            return False
        else:
            return True


    def getPrimaryScreenDimensions(self, geometrystring=True, withouttaskbar=True):
        x = os.getenv('firstscreenWidth')
        y = os.getenv('firstscreenHeigth')
        if x == "" or y == "":
            return False
        if withouttaskbar == True:
            if commands.getoutput("pidof mate-panel"):
                panel_auto_hide = commands.getoutput("dconf read /org/mate/panel/toplevels/top/auto_hide")
                if panel_auto_hide == True:
                    panel_size = 0
                else:
                    panel_size = int(commands.getoutput("dconf read /org/mate/panel/toplevels/top/size"))
                    panel_size += 1 # we need the absolute value pixels
            else:
                panel_size = 0
            y = int(y)-int(panel_size)

        # should we return a string or a dict?
        if geometrystring == True:
            screen_geometry = str(x) + "x" + str(y) + "+0+" + str(panel_size) # e.g. 1920x1065+0+25
        else:
             screen_geometry = int(x), int(y), 0, int(panel_size)
        return screen_geometry

    def getSecondaryScreenDimensions(self, geometrystring=True):
        x = os.getenv('secondscreenWidth')
        y = os.getenv('secondscreenHeigth')
        if x == "" or y == "":
            return False
        #
        # CAVEAT: How should we know the y-offset?
        #

        # should we return a string or a dict?
        if geometrystring == True:
            # FIX ME: have offsets here depending on first screens resolution
            screen_geometry = str(x) + "x" + str(y)
        else:
             screen_geometry = int(x), int(y)
        return screen_geometry


    def getFullscreenDimensions(self, geometrystring=True):
        screen_geometry = ""
        xwininfo_cmd = "/usr/bin/xwininfo -root"
        if commands.getoutput("pidof mate-panel"):
            panel_auto_hide = commands.getoutput("dconf read /org/mate/panel/toplevels/top/auto_hide")
            if panel_auto_hide == True:
                panel_size = 0
            else:
                panel_size = int(commands.getoutput("dconf read /org/mate/panel/toplevels/top/size"))
                panel_size += 1 # we need the absolute value pixels
        else:
            panel_size = 0

        try:
            xrootwininfo = os.popen(xwininfo_cmd)
            width, height, xoffset, yoffset = re.search(
                    "-geometry ([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9])",
                    xrootwininfo.read()).groups()
            xrootwininfo.close()

            height = str(int(height) - panel_size)
            yoffset = str(int(yoffset) + panel_size)
            if geometrystring == True:
                screen_geometry = width + "x" + height + "+" + xoffset + "+" + yoffset
            else:
                screen_geometry = int(width), int(height), int(xoffset), int(yoffset)
        except:
            e = "Unable to get xrootwininfo(" + str(sys.exc_info()[0]) + "): " + \
                "xwininfo_cmd: " + str(xwininfo_cmd) + \
                ", panel_auto_hide: " + str(panel_auto_hide) + \
                ", panel_size: " + str(panel_size)
            self.log(3, e)
        return screen_geometry

    def getScreenDepth(self):
        screen_depth = ""
        xwininfo_cmd = "/usr/bin/xwininfo -root"
        try:
            xrootwininfo = os.popen(xwininfo_cmd)
            screen_depth = re.search(
                    'Depth: ([0-9]+)',
                    xrootwininfo.read()).groups()
            xrootwininfo.close()

        except:
            e = "Unable to get xrootwininfo(" + str(sys.exc_info()[0]) + "): " + \
                "xwininfo_cmd: " + str(xwininfo_cmd)
            self.log(3, e)

        return screen_depth

    def getDictionaryFromFile(self, filename, delimiter="="):
        entry_dict = {}
        f = self.__getFileObject(filename)
        for line in f.readlines():
            k, v = line.strip().split(delimiter)
            entry_dict[k] = v
        self.__closeFileObject(f)
        return entry_dict

    def writeDictionaryToFile(self, entry_dict, filename, delimiter="=", quote='"'):
        if type(entry_dict) != types.DictType:
            e = "No dictionary passed(TypeError): " + \
                "entry_dict: " + str(entry_dict)
            self.log(2, e)
            return

        try:
            f = self.__getFileObject(filename,"w")
            f.write("# TCOS modified by: " + \
                    os.path.abspath(sys.argv[0]) + \
                    " at: " + time.asctime()  + "\n")
            keys = entry_dict.keys()
            keys.sort()
            for key in keys:
                if entry_dict[key] != None:
                    f.write(key + delimiter + quote + entry_dict[key] + quote + "\n")
            self.__closeFileObject(f)
        except:
            e = "Unable to write dictionary to file(" + \
                str(sys.exc_info()[0]) + "): " + \
                "entry_dict: " + str(entry_dict) + \
                ", filename: " + str(filename)
            self.log(2, e)

    def symlinkSave(self, source, destination):
        try:
            if os.path.exists(destination):
                os.rename(destination, destination + ".tcos-old")
            os.symlink(source, destination)
        except:
            e = "Unable to symlink file(" + \
                str(sys.exc_info()[0]) + "): " + \
                "source: " + str(source) + \
                ", destination: " + str(destination)
            self.log(2, e)

    def unifyList(self, list):
        # Fastest order preserving
        # see: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
        set = {}
        return [set.setdefault(e,e) for e in list if e not in set]

    def shellQuote(self, arg):
        # Everything is safely quoted inside a ''-quoted string, except a ' itself,
        # which can be written as '\'' (a backslash-escaped ' outside of the
        # ''-quoted string)
        return "'" + arg.replace("'", "'\\''") + "'"

    def shellQuoteList(self, args):
        return " ".join([self.shellQuote(arg) for arg in args])

    def mergeWithLdap(self, target, source=None):
        '''
        merges two ENTRY dicts where source values win over the one's from target

        options = dict()
        # Key -> Config name, list: 0 -> default value additional, 1-> non-ldap data
        options = {
            'Config.Option1': { 'value': 'bla', params: ['real_bla', 'another_bla']},
            'Config.Option3': { 'value': 'wurst' }
            }
        l = tcos.Launcher()
        l.mergeWithLdap(OPTIONS)
        '''
        if not source:
            launcher = Launcher(hashed_dn=sys.argv[1])
            source = launcher.ENTRY

        for k in source.keys():
            if k in target:
                target[k]['value'] = source[k]
            else:
                target[k] = {'value': source[k], 'params': []}