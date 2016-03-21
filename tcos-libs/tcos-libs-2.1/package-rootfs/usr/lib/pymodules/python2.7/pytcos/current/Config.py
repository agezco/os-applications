'''Provides global pytcos configuration. Eg. Mockups for Unit Testing'''
import os

class Config(object):

    #Singleton Implementation
    class __Config:
        def __init__(self):
            self.val = None
        def __str__(self):
            return repr(self) + self.val

    instance = None

    def __init__(self, arg):
        if not Config.instance:
            Config.instance = Config.__Logger(arg)
        else:
            Config.instance.val = arg
        self.LOG = []


    __mac_addr = ''
    __logger__ = ''
    ext_ldap = {}

    def __init__(self):
        self.__debug = os.environ['DEBUG']
        self.__test = os.environ['UNIT']

    '''Todo: setup test mac address, ldap Binding'''
