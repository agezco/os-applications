import ldapurl
import os
import re
import sys

from pytcos.tcosmodules.Logger import Logger
from pytcos.tcos.Config import Config

class System(Logger,Config):
    def __init__(self):
        # self.LOG is filled and needed by Logger.log()
        self.LOG = []

    def getMac(self, iface="autodetect"):
        if iface == "autodetect":
            try:
                import netifaces as ni
                iface = ni.gateways()['default'][2][1]
            except:
                self.log(3, 'Couldn\'t autodetect iface, Fallback to eth0.')
                iface = 'eth0'
        # get mac via sysfs
        f_name = '/sys/class/net/' + iface + '/address'
        try:
            f = open(f_name)
            mac = f.read().strip()
            f.close()
            return mac
        except IOError, (errno, strerror):
            e = "I/O error(" + str(errno) + ")" + ": " + \
                str(strerror) + ": " + \
                str(f_name)
            self.log(3, e)
        except:
            e = "Unexpected error: " + str(sys.exc_info()[0])
            self.log(3, e)

    def getUsername(self):
        # get login name
        # ioctr trouble with gdm PostLogin
        #username = os.getlogin()
        username = os.getenv("USER")
        if username:
            return username
        else:
            e = "Unable to get user login name"
            self.log(3, e)

    def getCmdlineParam(self, param, cmdline="/proc/cmdline"):
        # read cmdline
        try:
            f = open(cmdline)
            c_data = f.read()
            # parse cmdline
            try:
                value = re.search(param + "=(.*?)[ \n]", c_data).group(1)
                return value
            except AttributeError:
                return ""
            except:
                e = "Unable to get " + \
                    "parameter: " + param + " in cmdline: " + \
                    str(cmdline) + ": " + \
                    str(c_data)
                self.log(3, e)
            f.close()
        except IOError, (errno, strerror):
            e = "I/O error(" + str(errno) + ")" + ": " + \
                str(strerror) + ": " + \
                str(cmdline)
            self.log(3, e)
        except:
            e = "Unexpected error: " + str(sys.exc_info()[0])
            self.log(3, e)

    def isLocalBoot(self):
        root_device = self.getCmdlineParam("root")
        if root_device.startswith("/dev/") and Util().isMounted(root_device):
            return True
        else:
            return False

    def getLdapUrl(self):
        ldap_url = self.getCmdlineParam("ldapurl")
        if self.isLocalBoot() and Util().isRunning("slapd"):
            lurl = ldapurl.LDAPUrl(ldap_url)
            ldap_url = ldap_url.replace(lurl.urlscheme + "://" + lurl.hostport,
                                        "ldap://127.0.0.1")
        return ldap_url

    def getNfsroot(self):
        return self.getCmdlineParam("nfsroot")

    def getNfsrootServer(self):
        return self.getNfsroot().split(':')[0]

    def getNfsrootPath(self):
        return self.getNfsroot().split(':')[1]

    def getNfshome(self):
        return self.getCmdlineParam("nfshome")

    def getNfshomeServer(self):
        return self.getNfshome().split(':')[0]

    def getNfshomePath(self):
        return self.getNfshome().split(':')[1]