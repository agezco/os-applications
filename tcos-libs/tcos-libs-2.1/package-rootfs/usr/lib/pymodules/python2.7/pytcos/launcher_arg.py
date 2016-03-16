#!/usr/bin/env python

# Standard tcosmodules
import sys
import os
import base64

# TCOS tcosmodules
import tcos

user = os.getenv('USER')
s = tcos.System()
ld = tcos.Ldap()

a = []
for i, val in enumerate(sys.argv):
	a.append(val)

def get_hashed_arg(arg):
	ldap_url  = s.getLdapUrl()
	user_dn   = ld.getUserDn(user, ldap_url)
	mac	  = s.getMac()
	client_dn = ld.getClientDn(mac, ldap_url)
	apps_dn	  = ld.getAppsDn(client_dn, user_dn, ldap_url)

        for app_dn in apps_dn:
                if arg in app_dn:
                        return app_dn, base64.b16encode(app_dn)
if __name__ == "__main__":
        try:
                app_dn, b16 = get_hashed_arg(a[1])
                print 'app_dn: %s\t hash: %s' % (app_dn, b16)
        except:
		print '*** No app found containing searchstring.'


