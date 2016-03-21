import copy
import subprocess


from Logger import Logger
from Config import Config


class Cmd(Config):
    def __init__(self, exe=None):
        # self.LOG is filled and needed by Logger.log()
        self.LOG = []
        self._path = []
        if exe:
            self._path = Cmd._to_list(self._path, exe)
        pass

    def __call__(self, args=''):
        return self.run(args)

    def add(self, new):
        '''adds arguments to the self._path'''
        self._path = Cmd._to_list(self._path, new)

    @staticmethod
    def _to_list(_list, new):
        if type(new) == list:
            _list.extend(new)
        elif type(new) == str:
            _list.extend(new.split())
        else:
            _list.append(str(new))
        return _list

    @property
    def path(self):
        return self._path

    def run(self, args=''):
        '''args will not be stored permanently'''
        # throw away _path after run
        _path = copy.deepcopy(self._path)
        _path = Cmd._to_list(_path, args)
        logging = Logger()
        logging.log(1, str(_path))
        try:
            p = subprocess.Popen(_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except TypeError:
            raise
        else:
            return p