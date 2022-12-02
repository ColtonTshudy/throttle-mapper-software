__author__ = "Colton Tshudy, Erin Freck"
__version__ = "0.4"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

from datetime import datetime
import serial
import csv
import serial.tools.list_ports

#======================================
# DYNO THROTTLE MAPPER RUNNER
#======================================

def main():
    arduino_port = findArduinoPort()

    #CSV to record to
    d = open("throttle_log.csv", "a", newline='')
    writer = csv.writer(d,delimiter=",")
    formatCSV(writer)

    #Plaintxt command file
    f = open("throttle_cmds.txt")
    lines = f.readlines()   

    #serial port   
    ser = serial.Serial(port=arduino_port, baudrate=115200, timeout=.1)
    ser.flushInput()

    #command iterator
    curLine = 0
    maxLine = len(lines)

    #read serial, watch for ">"
    while True:
        commandExecuting = False
        try:
            #wait until a message is recieved
            if ser.inWaiting() != 0:
                #tame the recieved message
                recieved = ser.readline()
                decoded = recieved.decode('ascii')
                decoded = decoded.strip()
                print(decoded)
                
                #check what the recieved message contained
                match decoded[0]:
                    case '>':
                        commandExecuting = False
                        if curLine < maxLine:
                            cmd = lines[curLine]
                            #append a newline character if needed
                            if cmd[len(cmd)-1] != '\n':
                                cmd = cmd + "\n"
                            ser.write(cmd.encode('ascii'))
                            curLine = curLine + 1
                        elif not commandExecuting:
                            exitProgram()
                    case '<':
                        commandExecuting = True
                    case '[':
                        decoded = decoded[1:]
                        data = decoded.split(",")
                        writer.writerow(data)
                    case _:
                        pass
            
        # closes all files when user terminates program
        except:
            ser.write("t 0\n".encode('ascii')) #throttle 0%
            d.close
            f.close
            ser.close
            print("DynoRunner Terminated Gracefully")
            break

# Functions
#================================
def findArduinoPort():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "CH340" in p.description: #arduino nano tag
            return p.device
    return 'COM1' #default return

def exitProgram():
    softExitMsg = "Reached end of command file"
    print(softExitMsg) 
    raise Exception(softExitMsg)

def formatCSV(writer):
    timestamp = datetime.now()
    date = timestamp.strftime("%m/%d")
    year = timestamp.strftime("%Y")
    time = timestamp.strftime("%H:%M:%S")
    writer.writerow(["New Run", date, year, time])
    writer.writerow(["Volts", "Thr%", "Ohms", "Millis"])


# Main Runner
#==================================
if __name__ == '__main__':
    main()