import base64
import os
import sys
import types


from pytcos.tcosmodules.Logger import Logger
from pytcos.tcos.Config import Config

class Desktop(Logger,Config):
    def __init__(self, client_dn=None, user_dn=None, ldap_url=None):
        # self.LOG is filled and needed by Logger.log()
        self.LOG = []

        # set self.LDAP_URL
        if ldap_url:
            self.LDAP_URL = ldap_url
        else:
            self.LDAP_URL = System().getLdapUrl()

        # set self.CLIENT_DN
        if client_dn:
            self.CLIENT_DN = client_dn
        else:
            mac = System().getMac()
            self.CLIENT_DN = Ldap().getClientDn(mac, self.LDAP_URL)

        # set self.USER_DN
        if user_dn:
            self.USER_DN = user_dn
        else:
            username = System().getUsername()
            self.USER_DN = Ldap().getUserDn(username, self.LDAP_URL)

    def getDesktopFileEntries(self, desktop_filename):
        entries = {}
        try:
            f = open(desktop_filename)
            for line in f:
                split_data = line.split("=", 1)
                if len(split_data) == 2:
                    entries[split_data[0]] = split_data[1].strip()
            return entries
        except IOError, (errno, strerror):
            e = "I/O error(" + str(errno) + ")" + ": " + \
                str(strerror) + ": " + \
                str(desktop_filename)
            self.log(1, e)
            return {}

    def getMergedDesktopFileEntries(self, app_dn, app_dn_info_dict, merge_desktop_filename):
        # Prefer "description" as "name"
        app_name = app_dn_info_dict.get("description", None)
        app_comment = app_dn_info_dict.get("name", None)

        if not app_name:
            app_name = app_comment

        app_schema = app_dn_info_dict.get("schema", None)
        # if there is a General.custom_icon set up within the xml, override the icon setting
        try:
            l = Ldap()
            app_icon_custom =  l.getNismapentry(app_dn, self.LDAP_URL).get('General.custom_icon')
        except IOError, e:
            print "*** error: " + e


        if app_schema and app_dn:
            app_path = "/opt/" + app_schema
            app_tryexec = app_path + "/tcos/launcher"
            app_exec = app_tryexec + " " + base64.b16encode(app_dn)
            app_icon = app_path + "/tcos/launcher.icon"
        else:
            app_path = None
            app_tryexec = None
            app_exec = None
            app_icon = None
        if app_icon_custom:
            app_icon = "/tcos/link/custom/icons/" + app_icon_custom

        new_desktop_file_entries = self.getDesktopFileEntries(merge_desktop_filename)
        if new_desktop_file_entries.has_key("X-TCOS-EXECFIELDCODE"):
            app_exec = app_exec + " " + new_desktop_file_entries["X-TCOS-EXECFIELDCODE"]

        desktop_file_entries = {"Name" : app_name,
                                "Comment" : app_comment,
                                "Path" : app_path,
                                #"TryExec" : app_tryexec,
                                "Exec" : app_exec,
                                "Icon" : app_icon,
                                "X-TCOS-DN" : app_dn,
                                "Type" : "Application",
                                "Categories" : "Application;TCOS;"}

        for k, v in desktop_file_entries.items():
            if not v:
                del desktop_file_entries[k]

        desktop_file_entries.update(new_desktop_file_entries)

        if not desktop_file_entries.has_key("Exec"):
            e = "Unable to merge desktop file(no key: Exec): " + \
                "app_dn: " + str(app_dn) + \
                ", app_dn_info_dict: " + str(app_dn_info_dict) + \
                ", merge_desktop_filename: " + str(merge_desktop_filename)
            self.log(2, e)
        elif not desktop_file_entries.has_key("Name"):
            e = "Unable to merge desktop file(no key: Name): " + \
                "app_dn: " + str(app_dn) + \
                ", app_dn_info_dict: " + str(app_dn_info_dict) + \
                ", merge_desktop_filename: " + str(merge_desktop_filename)
            self.log(2, e)
        else:
            return desktop_file_entries

    def writeDesktopFile(self, desktop_file_entry_dict, desktop_file_foldername):
        if not desktop_file_entry_dict.has_key("Exec"):
            e = "Unable to write desktop file(no key: Exec): " + \
                "desktop_file_entry_dict: " + str(desktop_file_entry_dict) + \
                ", desktop_file_foldername: " + str(desktop_file_foldername)
            self.log(2, e)
            return
        elif not desktop_file_entry_dict.has_key("Name"):
            e = "Unable to write desktop file(no key: Name): " + \
                "desktop_file_entry_dict: " + str(desktop_file_entry_dict) + \
                ", desktop_file_foldername: " + str(desktop_file_foldername)
            self.log(2, e)
            return

        desktop_file = os.path.join(desktop_file_foldername,
                                    desktop_file_entry_dict["Comment"] + ".desktop")

        try:
            f = open(desktop_file, "w")
        except IOError, (errno, strerror):
            if errno == 2:
                try:
                    os.makedirs(desktop_file_foldername)
                    f = open(desktop_file, "w")
                except:
                    e = "Unable to write desktop file(" + \
                        str(sys.exc_info()[0]) + "): " + \
                        "desktop_file_entry_dict: " + \
                        str(desktop_file_entry_dict) + \
                        ", desktop_file_foldername: " + \
                       str(desktop_file_foldername) + \
                        ", desktop_file: " + str(desktop_file)
                    self.log(2, e)
                    raise
            else:
                e = "I/O error(" + str(errno) + ")" + ": " + \
                    str(strerror) + ": " + \
                    str(desktop_file)
                self.log(2, e)
                raise

        f.write("[Desktop Entry]\n")
        for k, v in desktop_file_entry_dict.iteritems():
            f.write(k + "=" + v + "\n")
        os.chmod(desktop_file, 0o775)
        f.close()

    def writeDesktopFiles(self,
                          home=os.getenv("HOME"),
                          desktop_file_foldernames={
                              'autostart': '.config/autostart',
                              'applications': '.local/share/applications',
                              'desktop': 'Desktop'}):
        l = Ldap()
        apps_dn_list = l.getAppsDn(self.CLIENT_DN,
                                   self.USER_DN,
                                   self.LDAP_URL)
        # create desktop file for every app, by merging the static desktop file
        # with the dynamic data of ldap
        for app_dn in apps_dn_list:
            app = l.getGroupOfUniqueNamesInfo(app_dn, self.LDAP_URL)
            app_name = app["schema"]
            app_dir = os.path.join(os.path.join("/", "opt", app_name))
            app_desktop_file = os.path.join(os.path.join(app_dir, "tcos", app_name+".desktop"))
            # workaround: if (empty) desktop file is missing in the package
            if not os.path.exists(app_desktop_file):
                app_desktop_file = "/tmp/empty.desktop"
                open(app_desktop_file, 'a').close()

            desktop_entry = self.getMergedDesktopFileEntries(
                                     app_dn,
                                     app,
                                     app_desktop_file)
            # (1) for every app
            self.writeDesktopFile(desktop_entry, os.path.join(home, desktop_file_foldernames['applications']))

            # (2) .nodesktop
            if os.path.exists(os.path.join(app_dir, "tcos", ".nodesktop")) or \
               os.path.exists(os.path.join(app_dir, "tcos", app_name+".desktop-reload")):
                # just create the desktop file in .local/share/applications
                pass
            else:
                # create desktop file on Desktop too
                self.writeDesktopFile(desktop_entry, os.path.join(home, desktop_file_foldernames['desktop']))

            entry = l.getNismapentry(app_dn, self.LDAP_URL)
            # (3) autostart
            if entry.get('General.Autostart') == "Yes" or \
               os.path.exists(os.path.join(app_dir, "tcos", app_name+".desktop-reload")):
                self.writeDesktopFile(desktop_entry, os.path.join(home, desktop_file_foldernames['autostart']))

    def removeDesktopFiles(self, desktop_file_foldernames=[]):
        desktop_file_filenames = []

        if desktop_file_foldernames == []:
            homedir = os.getenv("HOME")
            desktop_file_foldernames = [homedir + "/Desktop/",
                                        homedir + "/.local/share/applications/",
                                        homedir + "/.config/autostart/"]
        elif type(desktop_file_foldernames) == types.StringType:
            desktop_file_foldernames = [desktop_file_foldernames]

        for foldername in desktop_file_foldernames:
            if os.path.isdir(foldername):
                for filename in os.listdir(foldername):
                    if filename.endswith(".desktop"):
                        desktop_file_filenames.append(foldername + filename)

        for filename in desktop_file_filenames:
            # let the custom made menu files alive (mozo)
            if not "mozo" in filename:
                os.remove(filename)
