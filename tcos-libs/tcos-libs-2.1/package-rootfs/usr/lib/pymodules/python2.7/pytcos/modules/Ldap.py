import base64
import ldap
import ldap.filter
import ldapurl
import os
import re
import sys
import types
import urllib

from Logger import Logger
from pytcos.Config import Config


class Ldap(Logger,Config):
    class DirectoryType:
        UNKNOWN, RFC, ADS, OPENLDAP, OPENLDAP_LOCAL = range(5)

    class SecondaryLdapConnection:
        def __init__(self, ldap_url=None):
            if ldap_url:
                self.LDAP_URL = ldap_url
            else:
                self.LDAP_URL = System().getLdapUrl()

            client_dn = Ldap().getClientDn(System().getMac(), self.LDAP_URL)
            location_dn = Ldap().getLocationsDn(client_dn, self.LDAP_URL)

            self.LOCATION_ENTRY = Ldap().getNismapentry(location_dn, self.LDAP_URL)
            self.CONNECTION_ENTRY = Ldap().getRealmConfiguration(self.LDAP_URL)

            dsl = "Directory.Secondary.LDAPURLs"
            ud = "UserGroupSettings.DirectoryVersion"

            # check location for overwrite
            if self.LOCATION_ENTRY.has_key(dsl) and \
               self.LOCATION_ENTRY.has_key(ud):
                if self.LOCATION_ENTRY[ud] == "secondary":
                    self.CONNECTION_ENTRY = self.LOCATION_ENTRY

        def getLdapUrl(self):
            value = ""
            key = "Directory.Secondary.LDAPURLs"
            if self.CONNECTION_ENTRY.has_key(key):
                value = self.CONNECTION_ENTRY[key] + \
                    "????bindname=" + urllib.quote(self.getRoPrincipal()) + \
                    ",X-BINDPW=" + base64.b64encode(self.getRoSecret())

            return value

        def getRoPrincipal(self):
            value = ""
            key = "Directory.Secondary.ReadOnly.Principal"
            if self.CONNECTION_ENTRY.has_key(key):
                value = self.CONNECTION_ENTRY[key]

            return value

        def getRoSecret(self):
            value = ""
            key = "Directory.Secondary.ReadOnly.Secret"
            if self.CONNECTION_ENTRY.has_key(key):
                value = self.CONNECTION_ENTRY[key]

            return value

        def getType(self):
            value = ""
            key = "UserGroupSettings.Type"
            if self.CONNECTION_ENTRY.has_key(key):
                value = self.CONNECTION_ENTRY[key]

            return value

        def getDirectoryVersion(self):
            value = ""
            key = "UserGroupSettings.DirectoryVersion"
            if self.CONNECTION_ENTRY.has_key(key):
                value = self.CONNECTION_ENTRY[key]

            return value

    def __init__(self):
        # self.LOG is filled and needed by Logger.log()
        self.LOG = []

        # stats
        self.SEARCHCOUNT = 0
        self.SEARCHCOUNT_RECURSIVE = 0

    def trimDnToUpper(self, dn):
        ret = ""
        dn_esc = dn.replace("\,", "#%COMMA%#")
        ret_list = dn_esc.split(',')

        for i in range(len(ret_list)):
            ret_list[i] = ret_list[i].strip()
            if ret_list[i].startswith("cn="):
                ret_list[i] = ret_list[i].replace("cn=", "CN=", 1)
            elif ret_list[i].startswith("dc="):
                ret_list[i] = ret_list[i].replace("dc=", "DC=", 1)
            elif ret_list[i].startswith("ou="):
                ret_list[i] = ret_list[i].replace("ou=", "OU=", 1)
            elif ret_list[i].startswith("l="):
                ret_list[i] = ret_list[i].replace("l=", "L=", 1)
            ret = ret + ret_list[i].strip()
            if i + 1 < len(ret_list):
                ret = ret + ",";

        return ret.replace("#%COMMA%#", "\,")

    def getLdapObj(self, ldap_url):
        try:
            lurl = ldapurl.LDAPUrl(ldap_url)
            # bindname is urlencoded
            username = urllib.unquote(lurl.who)
            try:
                password = base64.b64decode(lurl.cred)
            except TypeError:
                password = lurl.cred
            ldap_obj = ldap.initialize(lurl.urlscheme + "://" + lurl.hostport)
            ldap_obj.simple_bind_s(username, password)
            return ldap_obj
        except:
            e = "Unable to get ldap object: ("  + \
                str(sys.exc_info()[0]) + "): " + \
                "ldap_url: " + str(ldap_url) + \
                ", hostport: " + str(lurl.hostport) + \
                ", username: " + str(username) + \
                ", password: " + str(password)
            self.log(3, e)

    def guessServerType(self, ldap_url):
        try:
            lurl = ldapurl.LDAPUrl(ldap_url)
            if lurl.hostport.startswith("127."):
                return self.DirectoryType.OPENLDAP_LOCAL

            l = self.getLdapObj(ldap_url)
            match = l.search_s("",
                               ldap.SCOPE_BASE,
                               "(objectclass=*)",
                               ["dsServiceName","vendorName","objectClass"])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1

            ret_list = match[0][1]
            if (ret_list.get("vendorName")):
                if (ret_list.get("vendorName")[0].upper().startswith("APACHE")):
                    return self.DirectoryType.RFC
            elif (ret_list.has_key("dsServiceName")):
                return self.DirectoryType.ADS
            elif (ret_list.has_key("objectClass")):
                for i in ret_list.get("objectClass"):
                    if i.upper().startswith("OPENLDAPROOTDSE"):
                        return self.DirectoryType.OPENLDAP
            else:
                raise
        except:
            e = "Unable to guess Server Type for ldap_url: " + str(ldap_url)
            self.log(3, e)
            return self.DirectoryType.UNKNOWN

    def getPamSaslMechanisms(self, ldap_url):
        try:
            l = self.getLdapObj(ldap_url)
            match = l.search_s("",
                               ldap.SCOPE_BASE,
                               "(objectclass=*)",
                               ["supportedSASLMechanisms"])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1

            try:
                return  match[0][1]["supportedSASLMechanisms"]
            except:
                return []

        except:
            e = "Unable to get supportet SASL mechanisms for ldap_url: " + str(ldap_url)
            self.log(3, e)
            return []

    def getRealmConfiguration(self, ldap_url):
        lurl = ldapurl.LDAPUrl(ldap_url)
        try:
            return self.getNismapentry("ou=RealmConfiguration," + lurl.dn,
                                       ldap_url)
        except:
            e = "Unable to get RealmConfiguration(" + \
                str(sys.exc_info()[0]) + "): " + \
                "ldap_url: " + str(ldap_url)

            return {}

    def getRealmConfigurationEntry(self, ldap_url, key):
        crc_dict = self.getRealmConfiguration(ldap_url)
        if crc_dict.has_key(key):
            return crc_dict[key]
        else:
            return ""

    def getClientDn(self, mac, ldap_url):
        try:
            l = self.getLdapObj(ldap_url)
            lurl = ldapurl.LDAPUrl(ldap_url)
            match = l.search_s("ou=clients," + lurl.dn,
                               ldap.SCOPE_ONELEVEL,
                               "(&(objectclass=ieee802Device)(macAddress=" +
                               mac + "))",
                               ['cn'])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1

            if len(match) > 0 and match[0][0] != None:
                #return self.trimDnToUpper(match[0][0])
                return match[0][0]
            else:
                # try default mac 00:00:00:00:00:00
                match = l.search_s("ou=clients," + lurl.dn,
                                   ldap.SCOPE_ONELEVEL,
                                   "(&(objectclass=ieee802Device)(macAddress=00:00:00:00:00:00))",
                                   ['cn'])
                self.SEARCHCOUNT = self.SEARCHCOUNT + 1

                if len(match) > 0 and match[0][0] != None:
                    return match[0][0]
                else:
                    e = "Unable to get CLIENT_DN for MAC(notExistent): " + \
                        "mac: " + str(mac) + \
                        ", ldap_url: " + str(ldap_url)

                    self.log(2, e)
                    return ""

        except:
            e = "Unable to get CLIENT_DN for MAC(" + \
                str(sys.exc_info()[0]) + "): " + \
                "mac: " + str(mac) + \
                ", ldap_url: " + str(ldap_url)

            self.log(2, e)
            return ""

    def getUserDn(self, username, ldap_url):
        try:
            slc = self.SecondaryLdapConnection(ldap_url)

            secondary_ldap_url = slc.getLdapUrl()
            usergroup_ldap_dir = slc.getDirectoryVersion()
            usergroup_type = slc.getType()

            use_secondary_ldap_url = False
            if (username != 'tcos' and secondary_ldap_url and usergroup_ldap_dir == "secondary" and \
                    (usergroup_type == "Users" or usergroup_type == "UsersGroups")):
                use_secondary_ldap_url = True
                ldap_url = secondary_ldap_url

            server_type = self.guessServerType(ldap_url)
            if (server_type == self.DirectoryType.RFC or \
                    server_type == self.DirectoryType.OPENLDAP_LOCAL or \
                    use_secondary_ldap_url == False):
                lurl = ldapurl.LDAPUrl(ldap_url)
                #user_dn = 'CN=' + username + ',OU=users,' + lurl.dn
                user_dn = 'cn=' + username + ',ou=users,' + lurl.dn
                #return self.trimDnToUpper(user_dn)
                return user_dn

            elif (server_type == self.DirectoryType.ADS and \
                    use_secondary_ldap_url == True):
                l = self.getLdapObj(ldap_url)
                l.set_option(ldap.OPT_REFERRALS, 0)
                lurl = ldapurl.LDAPUrl(ldap_url)
                match = l.search_s(lurl.dn,
                                   ldap.SCOPE_SUBTREE,
                                   "(&(objectclass=person)(sAMAccountName=" +
                                   username + "))",
                                   ["sAMAccountName"],
                                   1)
                self.SEARCHCOUNT = self.SEARCHCOUNT + 1
                if len(match) > 0 and match[0][0] != None:
                    #return self.trimDnToUpper(match[0][0])
                    return match[0][0]

                e = "Unable to get USER_DN(notExistent): " + \
                    "username: " + str(username) + \
                    ", ldap_url: " + str(ldap_url)

                self.log(2, e)
                return ""

            elif (server_type == self.DirectoryType.OPENLDAP and \
                    use_secondary_ldap_url == True):
                l = self.getLdapObj(ldap_url)
                l.set_option(ldap.OPT_REFERRALS, 0)
                lurl = ldapurl.LDAPUrl(ldap_url)
                match = l.search_s(lurl.dn,
                                   ldap.SCOPE_SUBTREE,
                                   "(&(objectclass=posixAccount)(uid=" +
                                   username + "))",
                                   ["uid"],
                                   1)
                self.SEARCHCOUNT = self.SEARCHCOUNT + 1
                if len(match) > 0 and match[0][0] != None:
                    #return self.trimDnToUpper(match[0][0])
                    return match[0][0]

                e = "Unable to get USER_DN(notExistent): " + \
                    "username: " + str(username) + \
                    ", ldap_url: " + str(ldap_url)

                self.log(2, e)
                return ""
            else:
                raise
        except:
            e = "Unable to get USER_DN(" + str(sys.exc_info()[0]) + "): " + \
                "username: " + str(username) + \
                ", ldap_url: " + str(ldap_url)
            self.log(2, e)
            return ""

    def getPamLdapUrl(self, ldap_url):
        slc = self.SecondaryLdapConnection(ldap_url)

        secondary_ldap_url = slc.getLdapUrl()
        usergroup_ldap_dir = slc.getDirectoryVersion()
        usergroup_type = slc.getType()

        if secondary_ldap_url and \
           usergroup_ldap_dir == "secondary" and \
           (usergroup_type == "Users" or usergroup_type == "UsersGroups"):
            ldap_url = secondary_ldap_url

        return ldap_url

    def getGroupOfUniqueNamesDn(self,
                                organizational_unit, unique_member_dn_list, ldap_url):
        group_of_unique_names_dn =  ([])

        if type(unique_member_dn_list) == types.StringType:
            unique_member_dn_list = [unique_member_dn_list]

        search_pattern = "(|"
        for unique_member_dn in unique_member_dn_list:
            if unique_member_dn:
                unique_member_dn = ldap.filter.escape_filter_chars(unique_member_dn)
                search_pattern += "(uniquemember=" + unique_member_dn + ")"
        search_pattern += ")"

        if search_pattern == "(|)":
            return []

        try:
            l = self.getLdapObj(ldap_url)
            lurl = ldapurl.LDAPUrl(ldap_url)
            match = l.search_s("ou=" + organizational_unit + "," + lurl.dn,
                               ldap.SCOPE_ONELEVEL,
                               search_pattern,
                               ["cn"])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1

            for (dn, cn) in match:
                #group_of_unique_names_dn.append(self.trimDnToUpper(dn))
                group_of_unique_names_dn.append(dn)

            # the "who matches" is done by preserving order
            return Util().unifyList(group_of_unique_names_dn)
        except:
            e = "Unable to get DN(" + str(sys.exc_info()[0]) + "): " + \
                "organizational_unit: " + str(organizational_unit) + \
                ", unique_member_dn_list: " + str(unique_member_dn_list) + \
                ", search_pattern: " + str(search_pattern)

            self.log(2, e)
            return []

    def getGroupOfUniqueNamesDnRecursiv(self,
                                        organizational_unit,
                                        unique_member_dn_list,
                                        ldap_url):
        # TODO: port this crazy stuff to order preserving lists:
        #       who matches who, on recursive groups?!
        def __collectRecursiv(organizational_unit, unique_member_dn):
            child_set = set(self.__children)
            match_set = set([])
            try:
                l = self.getLdapObj(ldap_url)
                lurl = ldapurl.LDAPUrl(ldap_url)
                unique_member_dn = ldap.filter.escape_filter_chars(unique_member_dn)
                match = l.search_s("ou=" + organizational_unit + "," + lurl.dn,
                                   ldap.SCOPE_ONELEVEL,
                                   "(&(objectclass=groupOfUniqueNames)(uniquemember=" + unique_member_dn + "))",
                                   ["uniquemember"])
                self.SEARCHCOUNT = self.SEARCHCOUNT + 1
                self.SEARCHCOUNT_RECURSIVE = self.SEARCHCOUNT_RECURSIVE + 1
                for k, v in match:
                    if k != None:
                        match_set.add(k)
            except:
                e = "Unable to get DN(" + str(sys.exc_info()[0]) + "): " + \
                    "organizational_unit: " + str(organizational_unit) + \
                    ", unique_member_dn: " + str(unique_member_dn)

                self.log(2, e)
                match_set = set([])

            for i in match_set - child_set:
                if i == "DC=dummy": continue
                try:
                    if ldap.explode_dn(i, 1)[1] == organizational_unit:
                        self.__children += [i]
                        __collectRecursiv(organizational_unit, i)
                except:
                    e = "Unable to get DN(" + \
                        str(sys.exc_info()[0]) + "): " + \
                        "organizational_unit: " + \
                        str(organizational_unit) + \
                        ", unique_member_dn: " + str(i)

                    self.log(2, e)

            return set(self.__children)

        if type(unique_member_dn_list) == types.StringType:
            unique_member_dn_list = [unique_member_dn_list]

        self.__children = unique_member_dn_list
        all_children = set([])

        for unique_member_dn in unique_member_dn_list:
            all_children |= __collectRecursiv(organizational_unit, unique_member_dn)

        return list(all_children)

    def getGroupOfUniqueNamesInfo(self, group_of_unique_names_dn, ldap_url):
        description = {}
        try:
            l = self.getLdapObj(ldap_url)
            match = l.search_s(group_of_unique_names_dn,
                               ldap.SCOPE_BASE,
                               "(objectclass=groupOfUniqueNames)",
                               ["cn", "description"])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1
            description["name"] = match[0][1]["cn"][0]
            try:
                description["description"] = match[0][1]["description"][0]
            except:
                description["description"] = ''

            match = l.search_s("nismapname=profile," + group_of_unique_names_dn,
                               ldap.SCOPE_BASE,
                               "(objectclass=nisMap)",
                               ["description"])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1
            description["schema"] = match[0][1]["description"][0]

            for k, v in description.items():
                if not v:
                    del description[k]

            return description
        except:
            e = "Unable to get description for group of unique names DN(" + \
                str(sys.exc_info()[0]) + "): " + \
                "group_of_unique_names_dn: " + str(group_of_unique_names_dn)

            self.log(2, e)

    def getMemberOfDn(self, member_dn, ldap_url):
        l = self.getLdapObj(ldap_url)
        l.set_option(ldap.OPT_REFERRALS, 0)
        match = l.search_s(member_dn,
                           ldap.SCOPE_BASE,
                           "(memberOf=*)",
                           ["memberOf"])
        self.SEARCHCOUNT = self.SEARCHCOUNT + 1

        try:
            return match[0][1]["memberOf"]
        except:
            return []

    def getMemberOfDnRecursiv(self, member_dn_list, ldap_url):
        # TODO: port this crazy stuff to order preserving lists:
        #       who matches who, on recursive groups?!
        def __collectRecursiv(member_dn):
            child_set = set(self.__children)
            match_set = set([])
            try:
                l = self.getLdapObj(ldap_url)
                lurl = ldapurl.LDAPUrl(ldap_url)
                l.set_option(ldap.OPT_REFERRALS, 0)
                member_dn = ldap.filter.escape_filter_chars(member_dn)
                match = l.search_s(lurl.dn,
                                   ldap.SCOPE_SUBTREE,
                                   "(&(objectclass=group)(memberOf=" + member_dn + "))",
                                   ["NoAttributeNeeded"])

                self.SEARCHCOUNT = self.SEARCHCOUNT + 1
                self.SEARCHCOUNT_RECURSIVE = self.SEARCHCOUNT_RECURSIVE + 1
                for k, v in match:
                    if k != None:
                        match_set.add(k)
            except:
                e = "Unable to get DN(" + str(sys.exc_info()[0]) + "): " + \
                    "member_dn: " + str(member_dn)
                self.log(2, e)

            for i in match_set - child_set:
                try:
                    self.__children += [i]
                    __collectRecursiv(i)
                except:
                    e = "Unable to get DN(" + \
                        str(sys.exc_info()[0]) + "): " + \
                        "member_dn: " + str(i)

                    self.log(2, e)

            return set(self.__children)

        if type(member_dn_list) == types.StringType:
            member_dn_list = [member_dn_list]

        self.__children = member_dn_list
        all_children = set([])

        for member_dn in member_dn_list:
            all_children |= __collectRecursiv(member_dn)

        return list(all_children)

    def getMemberUidDn(self, username, ldap_url):
        member_uid_dn = ([])
        l = self.getLdapObj(ldap_url)
        lurl = ldapurl.LDAPUrl(ldap_url)
        l.set_option(ldap.OPT_REFERRALS, 0)
        match = l.search_s(lurl.dn,
                           ldap.SCOPE_SUBTREE,
                           "(&(objectclass=posixGroup)(memberUid=" + username + "))",
                           ["NoAttributeNeeded"])
        self.SEARCHCOUNT = self.SEARCHCOUNT + 1

        for dn, empty in match:
            member_uid_dn.append(dn)

        return member_uid_dn

    def getUsergroupsDn(self, user_dn, ldap_url):
        tcos_dn = self.getUserDn('tcos', ldap_url)
        slc = self.SecondaryLdapConnection(ldap_url)

        secondary_ldap_url = slc.getLdapUrl()
        usergroup_ldap_dir = slc.getDirectoryVersion()
        usergroup_type = slc.getType()

        if (secondary_ldap_url and \
           usergroup_ldap_dir == "secondary"):
            ldap_url = secondary_ldap_url

        server_type = self.guessServerType(ldap_url)
        if (server_type == self.DirectoryType.RFC or \
                  server_type == self.DirectoryType.OPENLDAP_LOCAL):
            direct_usergroups = self.getGroupOfUniqueNamesDn("usergroups",
                                                             user_dn,
                                                             ldap_url)
            usergroups = self.getGroupOfUniqueNamesDnRecursiv("usergroups",
                                                              direct_usergroups,
                                                              ldap_url)
        elif (server_type == self.DirectoryType.ADS and \
                  usergroup_type == "UsersGroups" and \
                  user_dn != tcos_dn):
            direct_usergroups = self.getMemberOfDn(user_dn, ldap_url)
            usergroups = self.getMemberOfDnRecursiv(direct_usergroups, ldap_url)
        elif (server_type == self.DirectoryType.OPENLDAP and \
                  usergroup_type == "UsersGroups"):
            usergroups = self.getMemberUidDn(System().getUsername(), ldap_url)
        else:
            usergroups = []

        return usergroups

    def getAppgroupsDn(self, client_dn, user_dn, ldap_url):
        usergroups = self.getUsergroupsDn(user_dn, ldap_url)
        clientgroups = self.getClientgroupsDn(client_dn, ldap_url)
        direct_appgroups = self.getGroupOfUniqueNamesDn("appgroups",
                                                        usergroups +
                                                        clientgroups +
                                                        [user_dn, client_dn],
                                                        ldap_url)
        appgroups = self.getGroupOfUniqueNamesDnRecursiv("appgroups",
                                                         direct_appgroups,
                                                         ldap_url)
        return appgroups

    def getClientgroupsDn(self, client_dn, ldap_url):
        direct_clientgroups = self.getGroupOfUniqueNamesDn("clientgroups",
                                                           client_dn,
                                                           ldap_url)
        clientgroups = self.getGroupOfUniqueNamesDnRecursiv("clientgroups",
                                                            direct_clientgroups,
                                                            ldap_url)
        return clientgroups

    def getAppsDn(self, client_dn, user_dn, ldap_url):
        appgroups = self.getAppgroupsDn(client_dn, user_dn, ldap_url)
        clientgroups = self.getClientgroupsDn(client_dn, ldap_url)
        usergroups = self.getUsergroupsDn(user_dn, ldap_url)
        apps_for_appgroups = self.getGroupOfUniqueNamesDn("apps",
                                                          appgroups,
                                                          ldap_url)
        apps_for_clientgroups = self.getGroupOfUniqueNamesDn("apps",
                                                             clientgroups,
                                                             ldap_url)
        apps_for_usergroups = self.getGroupOfUniqueNamesDn("apps",
                                                           usergroups,
                                                           ldap_url)
        apps_for_client = self.getGroupOfUniqueNamesDn("apps",
                                                       [client_dn],
                                                       ldap_url)
        apps_for_user = self.getGroupOfUniqueNamesDn("apps",
                                                     [user_dn],
                                                     ldap_url)
        apps = apps_for_appgroups + \
         apps_for_clientgroups + \
               apps_for_usergroups + \
               apps_for_client + \
               apps_for_user

        return Util().unifyList(apps)

    def getHwtypesDn(self, client_dn, ldap_url):
        hwtypes = self.getGroupOfUniqueNamesDn("hwtypes",
                                               client_dn,
                                               ldap_url)
        return hwtypes

    def getDevicesDn(self, client_dn, ldap_url):
        hwtypes = self.getHwtypesDn(client_dn, ldap_url)
        devices = self.getGroupOfUniqueNamesDn("devices",
                                               hwtypes + [client_dn],
                                               ldap_url)
        return devices

    def getLocationsDn(self, client_dn, ldap_url):
        try:
            l = self.getLdapObj(ldap_url)
            lurl = ldapurl.LDAPUrl(ldap_url)
            match = l.search_s(client_dn,
                               ldap.SCOPE_BASE,
                               "(objectclass=ieee802Device)",
                               ["l"])
            self.SEARCHCOUNT = self.SEARCHCOUNT + 1

            #return self.trimDnToUpper(match[0][1]["l"][0])
            return match[0][1]["l"][0]
        except:
            e = "Unable to get LOCATIONS_DN(" + str(sys.exc_info()[0]) + "): " + \
                "client_dn: " + str(client_dn)
            self.log(2, e)
            return ''

    def getPrintersDn(self, client_dn, user_dn, ldap_url):
        usergroups = self.getUsergroupsDn(user_dn, ldap_url)
        location = self.getLocationsDn(client_dn, ldap_url)
        printers = self.getGroupOfUniqueNamesDn("printers",
                                                [location] + usergroups +
                                                [user_dn, client_dn],
                                                ldap_url)
        return printers

    def getPrintersDnByClient(self, client_dn, ldap_url):
        location = self.getLocationsDn(client_dn, ldap_url)
        printers = self.getGroupOfUniqueNamesDn("printers",
                                                [location] + [client_dn],
                                                ldap_url)
        return printers

    def getPrintersDnByUser(self, user_dn, ldap_url):
        usergroups = self.getUsergroupsDn(user_dn, ldap_url)
        printers = self.getGroupOfUniqueNamesDn("printers",
                                                usergroups + [user_dn],
                                                ldap_url)
        return printers

    def getNismapentry(self, group_of_unique_names_dn, ldap_url):
        entry_dict = {}

        # accept list with one member as well
        if type(group_of_unique_names_dn) == types.ListType and \
           len(group_of_unique_names_dn) == 1:
            group_of_unique_names_dn = group_of_unique_names_dn[0]

        try:
            l = self.getLdapObj(ldap_url)
            lurl = ldapurl.LDAPUrl(ldap_url)
            match = l.search_s("nismapname=profile," + group_of_unique_names_dn,
                               ldap.SCOPE_ONELEVEL,
                               "(objectclass=nisObject)",
                               ["cn", "nismapentry"])
            for i in match:
                key = i[1]['cn'][0]
                try:
                    val = i[1]['nismapentry'][0]
                except KeyError:
                    val = i[1]['nisMapEntry'][0]

                val = os.path.expandvars(val)

                '''IMPORTANT: As there is no real type attribute within our xml
                scheme, we need to emulate it with the help of hashtags
                variable__BOOL -> boolean
                variable__INT  -> integer
                variable__FLOAT-> float

                - they will be part of the key
                - need to be cut from the variable name
                '''
                p = re.compile(r'__[A-Z]*$')
                m = p.search(key)

                if m:
                    if 'BOOL' in m.group():
                        if 'true' in val:
                            val = True
                        else:
                            val = False
                        key = key[:m.start()]
                    elif 'INT' in m.group():
                        val = int(val)
                        key = key[:m.start()]
                    elif 'FLOAT' in m.group():
                        val = float(val)
                        key = key[:m.start()]

                entry_dict[key] = val

            return entry_dict
        except:
            e = "Unable to get Nismapentry(" + str(sys.exc_info()[0]) + "): " + \
                "group_of_unique_names_dn: " + str(group_of_unique_names_dn) + \
                ", ldap_url: " + str(ldap_url)
            self.log(2, e)
            return {}

    def getCnByDn(self, dn):
        cn = ldap.explode_dn(dn)[0]
        if cn.startswith("cn="):
            cn = cn.split("cn=")[1]
        elif cn.startswith("CN="):
            cn = cn.split("CN=")[1]

        return cn