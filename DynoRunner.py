__author__ = "Colton Tshudy, Erin Freck"
__version__ = "0.52"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

from datetime import datetime
import serial
import csv
import serial.tools.list_ports
from enum import Enum
import os
import serial.tools.list_ports

#======================================
# DYNO THROTTLE MAPPER RUNNER
# | Settings:
SER_PORT_NAME = 'USB'
GENERATE_CSV = False
#======================================

class State(Enum):
    Idle = 0
    Pending = 1
    Executing = 2
    Finished = 3

# Functions
#================================

def getSerialList():
    return ports.description
getSerialList.ser = ''
getSerialList.ports = ports = list(serial.tools.list_ports.comports())
getSerialList.serial_is_connected = False

def findDefaultPortIndex():
    '''Returns the Arduino Nano port, otherwise returns port index 0'''
    i = 0
    for p in getSerialList.ports:
        if SER_PORT_NAME in p.description: #arduino nano tag
            return i
        i = i+1
    return 0

def setSerialPort(port_index):
    try:
        getSerialList.ser = serial.Serial(port=checkSerial.ports[port_index].device, baudrate=115200, timeout=.1)
        getSerialList.ser.flushInput()
        getSerialList.serial_is_connected = True
    except:
        print('Serial port is busy or inaccessable.')
        getSerialList.serial_is_connected = False

def exitProgram(softExitMsg):
    '''Prints a message and raises an exception to trigger the catch'''
    print(softExitMsg) 
    raise Exception(softExitMsg)

def createCSV():
    '''Opens a new CSV and writes a header'''
    timeobj = datetime.now()
    timestamp = timeobj.strftime('%m_%d_%Y_%I_%M_%p')

    abs_path = os.path.dirname(__file__)
    rel_path = ''.join(['logs/throttle_log_', timestamp, '.csv'])
    full_path = os.path.join(abs_path, rel_path)
    d = open(full_path, 'w', newline='')
    writer = csv.writer(d,delimiter=',')
    
    writer.writerow(['Volts', 'Thr%', 'Ohms', 'Millis'])
    return writer, d

def serialConnected():
    return getSerialList.serial_is_connected

# Startup
# ==========================================

#CSV setup
if GENERATE_CSV:
    writer, d = createCSV()

#Plaintxt command file
f = open('throttle_cmds.txt')
lines = f.readlines()

setSerialPort(findDefaultPortIndex())

# Serial
# =======================================
def checkSerial(paused, command, terminate, restart):
    '''Executes all commands of a given text file. Records serial to CSV'''

    #execute argument commands
    if command != False:
        if command[len(command)-1] != '\n':
            command = command + '\n'
        getSerialList.ser.write(command.encode('ascii'))
        print(command)
    if terminate:
        getSerialList.ser.write('q\n'.encode('ascii'))
        print('terminated')
        restart = True

    #settings arguments
    if restart:
        checkSerial.curLine = 0
        checkSerial.fsmState = State.Pending

    #wait until a message is recieved
    if getSerialList.ser.inWaiting() != 0:
        #tame the recieved message
        recieved = getSerialList.ser.readline()
        decoded = recieved.decode('ascii')
        decoded = decoded.strip()
        print(decoded)
        msgType = decoded[0]
        data = False #for if data is recieved
        
        #fsm to control sending commands
        match checkSerial.fsmState:
            case State.Idle:
                if msgType == '>':
                    checkSerial.fsmState = State.Pending
                    
            case State.Pending:
                if not paused:
                    cmd = lines[checkSerial.curLine]
                    if cmd[len(cmd)-1] != '\n':
                        cmd = cmd + '\n'
                    getSerialList.ser.write(cmd.encode('ascii'))
                    checkSerial.curLine = checkSerial.curLine + 1
                    checkSerial.fsmState = State.Executing

            case State.Executing:
                if msgType == '<':
                    if checkSerial.curLine >= checkSerial.maxLine:
                        checkSerial.fsmState = State.Finished
                    else:
                        checkSerial.fsmState = State.Idle

            case State.Finished:
                pass

            case _:
                pass
        
        #record data to CSV
        if msgType == '[':
            rawdata = decoded[1:]
            data = rawdata.split(",")
            if GENERATE_CSV:
                writer.writerow(data)
        
        return msgType, decoded, data

    return False
#state variable
checkSerial.fsmState = State.Idle
#command iterator
checkSerial.curLine = 0
checkSerial.maxLine = len(lines)

def endOfFile():
    return checkSerial.fsmState == State.Finished

def closeRunner():
    '''closes all files when user terminates program'''
    getSerialList.ser.write("q".encode('ascii')) #send quit command
    if GENERATE_CSV:
        d.close
    f.close
    getSerialList.ser.close
    print('DynoRunner Terminated')