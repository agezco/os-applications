#Global Imports
import os

#Local Imports
from Logger import Logger
from Utils import Utils
from Config import Config

class ObjectManager:

    __logger = ''
    __utils = ''
    __config = ''

    def __init__(self):
        self.__logger = Logger.getInstance()
        self.__utils = Utils()
        self.__config = Config()

    @property
    def Utils(self):
        return self.__utils

    @property
    def Logger(self):
        return self.__logger

    @property
    def Config(self):
        return self.__config



