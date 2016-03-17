import base64
import os
import sys

from System import System
from Ldap import Ldap
from Logger import Logger
from pytcos.Config import Config


class Launcher(Logger, Config):
    def __init__(self, ldap_url=None, hashed_dn=None):
        # self.LOG is filled and needed by Logger.log()
        self.LOG = []

        self.ENTRY = {}

        self.HASHED_DN = hashed_dn

        self.DN = self.getDn()

        if ldap_url:
            self.LDAP_URL = ldap_url
        else:
            s = System()
            self.LDAP_URL = s.getLdapUrl()

        if self.LDAP_URL:
            self.ENTRY = self.getEntry()

    def getDn(self):
        if self.HASHED_DN:
            hashed_string = self.HASHED_DN
        elif len(sys.argv) >= 2:
            hashed_string = sys.argv[1]
        else:
            e = "No Application DN passed"
            self.log(3, e)
        try:
            dn_encode = base64.b16decode(hashed_string)
            return dn_encode
        except TypeError:
            return hashed_string

    def getEntry(self):
        entry = {}

        l = Ldap()
        entry = l.getNismapentry(self.DN, self.LDAP_URL)
        entry.update(l.getGroupOfUniqueNamesInfo(self.DN, self.LDAP_URL))

        if entry:
            return entry
        else:
            e = "Unable to get application entries (entry={}): " + \
                "DN: " + str(self.DN) + \
                ", LDAP_URL: " + str(self.LDAP_URL)

            e_user = "Anwendung nicht gefunden!" + "\n\n" + \
                     "Der Anwendungseintrag hat sich geaendert." + "\n" + \
                     "Melden Sie sich neu an, " + \
                     "damit die geaenderten Einstellungen wirksam werden." + "\n\n" + \
                     "Details:" + "\n" + \
                     "DN: " + str(self.DN) + "\n" + \
                     "LDAP_URL: " + str(self.LDAP_URL)

            self.log(2, e)
            os.system("zenity --error --text '" + e_user + "'")

    def getAppInfo(self):
        info = {}

        l = Ldap()
        info = l.getGroupOfUniqueNamesInfo(self.DN, self.LDAP_URL)

        if info:
            return info

        else:
            # do something about the missing stuff
            return {}
