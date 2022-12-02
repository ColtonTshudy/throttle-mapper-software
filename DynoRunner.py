import string
import serial
import time
import csv

#======================================
# BEGIN MAIN
#======================================

def main():
    #CSV to record to
    d = open("C:\\Users\\Tshud\\Documents\\throttle_log.csv", "a", newline='')
    writer = csv.writer(d,delimiter=",")

    #Plaintxt command file
    f = open("C:\\Users\\Tshud\\Documents\\throttle_cmds.txt")
    lines = f.readlines()

    #serial port   
    ser = serial.Serial(port='COM8', baudrate=115200, timeout=.1)
    ser.flushInput()

    #for line in lines:
    while True:
        try:
            if ser.inWaiting() !=0:
                recieved = ser.readline()
                decoded = recieved.decode('ascii')
                size = len(decoded)
                decoded = decoded[:size-2]
                print(decoded)
                data = decoded.split(",")
                writer.writerow(data);

        # closes all files when user terminates program
        except:
            d.close
            f.close
            ser.close
            print("ThrottleMapper Terminated")
            break



# Main Runner
if __name__ == '__main__':
    main()