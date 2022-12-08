__author__ = "Colton Tshudy, Erin Freck"
__version__ = "0.51"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

from datetime import datetime
import serial
import csv
import serial.tools.list_ports
from enum import Enum
import os

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
def findArduinoPort():
    '''Returns the Arduino Nano port, otherwise returns port COM1'''
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if SER_PORT_NAME in p.description: #arduino nano tag
            return p.device
    return False

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

# Startup
# ==========================================

arduino_port = findArduinoPort()
if arduino_port == False:
    exitProgram('Serial port not found.')

#CSV setup
if GENERATE_CSV:
    writer, d = createCSV()

#Plaintxt command file
f = open('throttle_cmds.txt')
lines = f.readlines()

#serial port   
ser = serial.Serial(port=arduino_port, baudrate=115200, timeout=.1)
ser.flushInput()

# Serial
# =======================================
def checkSerial(paused, command, terminate):
    '''Executes all commands of a given text file. Records serial to CSV'''

    #wait until a message is recieved
    if ser.inWaiting() != 0:
        #tame the recieved message
        recieved = ser.readline()
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
                    ser.write(cmd.encode('ascii'))
                    checkSerial.curLine = checkSerial.curLine + 1
                    checkSerial.fsmState = State.Executing

            case State.Executing:
                if msgType == '<':
                    if checkSerial.curLine >= checkSerial.maxLine:
                        checkSerial.fsmState = State.Finished
                        return '', 'Reached end of command file.', False
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



def closeRunner():
    '''closes all files when user terminates program'''
    ser.write("q".encode('ascii')) #send quit command
    if GENERATE_CSV:
        d.close
    f.close
    ser.close
    print('DynoRunner Terminated')