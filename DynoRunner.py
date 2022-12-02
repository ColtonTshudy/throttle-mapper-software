import string
import serial
import time
import csv
import serial.tools.list_ports

#======================================
# BEGIN MAIN
#======================================

def main():
    arduino_port = findArduinoPort()

    #CSV to record to
    d = open("throttle_log.csv", "a", newline='')
    writer = csv.writer(d,delimiter=",")

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
        sent_flag = False
        try:
            #wait until a message is recieved
            if ser.inWaiting() != 0:
                #tame the recieved message
                recieved = ser.readline()
                decoded = recieved.decode('ascii')
                size = len(decoded)
                decoded = decoded[:size-2]
                print(decoded)
                
                #check what the recieved message contained
                if decoded == ">" and curLine < maxLine:
                    ser.write(lines[curLine].encode('ascii'))
                    curLine = curLine + 1
                    sent_flag = True
                else:
                    data = decoded.split(",")
                    writer.writerow(data)
            
        # closes all files when user terminates program
        except:
            d.close
            f.close
            ser.close
            print("DynoRunner Terminated")
            break

def findArduinoPort():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "CH340" in p.description: #arduino nano tag
            return p.device
    return 'COM1' #default return
    

# Main Runner
if __name__ == '__main__':
    main()

