__author__ = "Colton Tshudy, Erin Freck"
__version__ = "0.21"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

#Talks to the hardware

import serial
import serial.tools.list_ports
from enum import Enum
import logger as logger

#Gobals (objects)
class State(Enum):
    Idle = 0
    Pending = 1
    Executing = 2
    Finished = 3

#BEGIN CLASS DEFINITION
class Communicator:
    def __init__(self, baudrate=115200, generate_csv=True):
        self._baudrate = baudrate
        self._ports = list(serial.tools.list_ports.comports())
        self._portindex = 0
        self._message = ''
        self._messagetype = ''
        self._available = False
        self._busy = True
        self._ser = ''
        self._fileisopen = ''
        self._cmdfile = ''
        self._cmdindex = 0
        self._commands = ''
        self._totalcommands = 0
        self._state = State.Idle
        self._log = logger.Logger()
        self._paused = True
        self._end_of_file = False

        if generate_csv:
            self._log.open()

    # Serial methods
    def autoFindPort(self, port_name='CH340'):
        '''Returns the Arduino Nano port, otherwise returns port COM1'''
        i = 0
        for p in self.listPorts():
            if port_name in p and p != self.currentPort():
                self.setPort(i,  baudrate=self._baudrate)
                return True
            i += 1
        return False
                
    def hasMessage(self):
        return self._available

    def readMessage(self):
        if self._available:
            self._available = False
            return self._message
        else: return False

    def messageType(self):
        return self._messagetype

    def listPorts(self):
        port_descs = []
        for p in self._ports:
            port_descs.append(p.description)
        return port_descs

    def setPort(self, port_index, baudrate=-1):
        self._portindex = port_index
        if baudrate != -1:
            self._baudrate = baudrate
            
        if not self._busy:
            self._ser.close()
        try:
            self._ser = serial.Serial(port=self._ports[self._portindex].device, baudrate=self._baudrate, timeout=.1)
            self._busy = False
            return True
        except serial.serialutil.SerialException:
            self._busy = True
            return False

    def currentPort(self):
        return self._ports[self._portindex].description

    def isBusy(self):
        return self._busy

    def sendCommand(self, command):
        if not self._busy and len(command)>0:
            if command[-1] != '\n':
                command += '\n'
            if 'q' in command:
                self.reset()
            self._ser.write(command.encode('ascii'))

    # State related methods
    def isPaused(self):
        return self._paused

    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False

    def terminate(self):
        self.sendCommand('q')        

    def reachedFileEnd(self):
        return self._end_of_file

    def reset(self):
        self._state = State.Pending
        self._paused = True
        self._end_of_file = True

    def restartFile(self):
        self._cmdindex = 0
        self._end_of_file = False

    # File reader methods
    def openCommandFile(self, path):
        try:
            new_file = open(path)
            if self._fileisopen:
                self._cmdfile.close()
            if self._fileisopen and self._cmdfile.name == new_file.name:
                new_file.close()
                return False
            self._cmdfile = new_file
            self._commands = self._cmdfile.readlines()
            self._totalcommands = len(self._commands)
            self._fileisopen = True
            return True
        except:
            return False

    def closeCommandFile(self):
        if self._fileisopen:
            self._cmdfile.close()
            return True
        return False

    # Big meaty finite state machine method
    def checkSerial(self):
        '''Record serial recieved and send serial commands'''
        #end early if serial port is busy
        if self._busy:
            return False

        #wait until a message is recieved
        if self._ser.inWaiting() != 0:
            self._available = True

            #tame the recieved message
            recieved = self._ser.readline()
            decoded = ''
            msgType = ''
            if recieved != '':
                decoded = recieved.decode('ascii').strip()
                msgType = decoded[0]
            
            #fsm to control sending commands
            match self._state:
                case State.Idle:
                    if msgType == '>':
                        self._state = State.Pending
                case State.Pending:
                    if not self._paused and self._fileisopen:
                        self.sendCommand(self._commands[self._cmdindex])
                        self._cmdindex += 1
                        self._state = State.Executing
                case State.Executing:
                    if msgType == '<':
                        if self._cmdindex >= self._totalcommands:
                            self._state = State.Finished
                            self._end_of_file = True
                        else:
                            self._state = State.Idle
                case State.Finished:
                    pass
                case _:
                    pass

            #record data to CSV
            if msgType == '[':
                rawdata = decoded[1:]
                data = rawdata.split(",")
                self._log.logData(data)

            #store data to class variables
            self._message = decoded
            self._messagetype = msgType
        return True

    def close(self):
        '''closes all objects'''
        self.terminate()
        self._log.close()
        if self._fileisopen:
            self._cmdfile.close()
        self._ser.close()

# Method to run a test of the code
def tester():
    import time
    test = Communicator(baudrate=115200, generate_csv=False)
    print('is busy:', test.isBusy())
    print('is paused:', test._paused)
    test.resume()
    print('is paused:', test._paused)
    test.pause()
    print('is paused:', test._paused)
    test.setPort(0)
    print('port:', test.currentPort())
    print('is busy:', test.isBusy())
    test.autoFindPort("CH340")
    print('port:', test.currentPort())
    print('is busy:', test.isBusy())
    print('baudate:', test._baudrate)

    print('Waiting for message...')
    time.sleep(2)
    test.sendCommand('t 25')
    test.checkSerial()
    print('message available:', test.hasMessage())
    print('message recieved:', test.readMessage())
    print('message available:', test.hasMessage())
    print('Waiting for next messages...')
    time.sleep(1)
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())

    time.sleep(0.5)
    test.openCommandFile('throttle_cmds.txt')
    test.resume()
    test.checkSerial()

    time.sleep(1)
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())

    test.close()

#tester()