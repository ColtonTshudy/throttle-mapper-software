__author__ = "Colton Tshudy"
__version__ = "0.1"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

#Talks to the hardware

from datetime import datetime
import csv
import os

class Logger:
    def __init__(self):
        self._file = ''
        self._writer = ''
        self._isopen = False

    def open(self):
        '''Opens a new CSV and writes a header'''
        timeobj = datetime.now()
        timestamp = timeobj.strftime('%m_%d_%Y_%I_%M_%p')

        this_path = os.getcwd()
        rel_path = 'logs\\throttle_log_{}.csv'.format(timestamp)
        full_path = os.path.join(this_path, rel_path)

        self._file = open(full_path, 'w', newline='')
        self._writer = csv.writer(self._file,delimiter=',')
        
        self._writer.writerow(['Volts', 'Thr%', 'Ohms', 'Millis'])

        self._isopen = True

    def logData(self, data_array):
        if self._isopen:
            self._writer.writerow(data_array)

    def isOpen(self):
        return self._isopen

    def close(self):
        if self._isopen:
            self._file.close()

def tester():
    #check what happens if not yet open
    log = Logger()
    log.logData(['test', 'data', ':()*&<>', '12345'])
    log.close()
    print(log.isOpen())

    #check what happens when open
    log.open()
    log.logData(['test', 'data', ':()*&<>', '12345'])
    log.logData(['test', 'successful!'])
    print(log.isOpen())
    log.close()

tester()