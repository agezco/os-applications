'''Provides global pytcos configuration. Eg. Mockups for Unit Testing'''
import os

class Config(object):

    __mac_addr = ''
    ext_ldap = {}

    def __init__(self):
        self.__debug = os.environ['DEBUG']
        self.__test = os.environ['UNIT']

    '''Todo: setup test mac address, ldap Binding'''
