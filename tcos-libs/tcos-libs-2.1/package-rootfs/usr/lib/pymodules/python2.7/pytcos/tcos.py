# -*- coding: utf-8 -*-

################################################################################
# openthinclient.org ThinClient suite
#
# Copyright (C) 2004, 2007 levigo holding GmbH. All Rights Reserved.
#
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
###############################################################################

import base64
import commands
import copy
import ldap
import ldap.filter
import ldapurl
import os
import re
import sys
import time
import subprocess
import syslog
import types
import urllib

'''Superclass all pytcos classes are derived from '''
import Config

''' Provides Legacy pytcos Interface compatibility '''
from modules.Ldap import Ldap
from modules.Desktop import Desktop
from modules.Launcher import Launcher
from modules.Cmd import Cmd
from modules.Logger import Logger
from modules.Util import Util
from modules.System import System

# Classes
#










