#!/usr/bin/env python

import tcos
import inspect

#Legacy api

l = tcos.Ldap()
s = tcos.System()
d = tcos.Desktop()
u = tcos.Util()

ldap_url = s.getLdapUrl()
client_dn = l.getClientDn(s.getMac(), ldap_url)
location_dn = l.getLocationsDn(client_dn, ldap_url)
user_dn = l.getUserDn('tcos', ldap_url)
devices_dn = l.getDevicesDn(client_dn, ldap_url)
apps_dn_list = l.getAppsDn(client_dn, user_dn, ldap_url)
app_dn = apps_dn_list[0]

#current
''' Todo:
        * import detection
        * legacy interface
        * set env
'''
