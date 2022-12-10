__author__ = "Colton Tshudy, Erin Freck"
__version__ = "0.2"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

#Talks to the hardware

import serial
import serial.tools.list_ports
from enum import Enum
import Logger as logger

#Gobals (objects)
class State(Enum):
    Idle = 0
    Pending = 1
    Executing = 2
    Finished = 3

#BEGIN CLASS DEFINITION
class Communicator:
    def __init__(self, baudrate=115200, generate_csv=True, default_port_name='CH340'):
        self._baudrate = baudrate
        self._ports = list(serial.tools.list_ports.comports())
        self._portindex = 0
        self._message = ''
        self._available = False
        self._busy = True
        self._ser = ''
        self._fileisopen = ''
        self._cmdfile = ''
        self._cmdindex = 0
        self._totalcommands = 0
        self._state = State.Idle
        self._paused = True
        self._log = logger.Logger()
        self.autoFindPort(default_port_name)

        if generate_csv:
            self._log.open()

    # Serial methods
    def autoFindPort(self, port_name):
        '''Returns the Arduino Nano port, otherwise returns port COM1'''
        i = 0
        for p in self.listPorts():
            if port_name in p: #arduino nano tag
                self.setPort(i)
                return True
            i += 1
        self.setPort(0) #default to port 0
        return False
                
    def hasMessage(self):
        return self._available

    def readMessage(self):
        if self._available:
            self._available = False
            return self._message
        else: return False

    def listPorts(self):
        port_descs = []
        for p in self._ports:
            port_descs.append(p.description)
        return port_descs

    def setPort(self, port_index, baudrate=115200):
        self._portindex = port_index
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
        return self._ports[self._portindex]

    def isBusy(self):
        return self._busy

    def sendCommand(self, command):
        if not self._busy:
            command = command.join('\n')
            if 'q' in command:
                self.reset()
            self._ser.write(command.encode('ascii'))

    # State related methods
    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False

    def terminate(self):
        self.sendCommand('q')

    def reset(self):
        self._state = State.Pending
        self._cmdindex = 0
        self._paused = True

    # File reader methods
    def setCommandFile(self, path):
        self._cmdfile = open(path)
        self._commands = self._cmdfile.readlines()
        self._totalcommands = len(self._commands)
        self._fileisopen = True

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
            decoded = recieved.decode('ascii').strip()
            msgType = decoded[0]
            self._message = decoded
            
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

        return True

    def close(self):
        '''closes all objects'''
        self.terminate()
        logger.close()
        self._cmdfile.close()
        self._ser.close()

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

    print('Waiting for message...')
    time.sleep(2)
    test.sendCommand('t 50')
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
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())
    test.checkSerial()
    print('message recieved:', test.readMessage())

tester()