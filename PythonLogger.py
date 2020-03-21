# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 17:59:21 2020

@author: niel.cansino

This script decodes the incoming data log.
The variables com_port and baud_rate must be defined.

"""

import os
import csv
import time
import binascii
import serial # import Serial Library
from serial.tools import list_ports # for automatic available port listing
import numpy  # Import numpy
import struct
from crccheck.crc import CrcModbus #crc checker

# PLEASE SET THIS
com_port = '/dev/ttyAMA0' #in linux the format should be '/dev/ttyACM0'
baud_rate = 115200

# CONSTANTS
START_CONDITION = 0xFEEFFFEF #user-defined start condition
TIME_STR = time.strftime("%Y%m%d-%H%M%S")
FILE_PATH=os.path.join(os.getcwd(),TIME_STR+'.csv')

# FILE HEADER
FILE_HEADER = ['sync', 'crc',
               'roll_target', 'roll_meas',
               'pitch_target', 'pitch_meas',
               'yaw_target', 'yaw_meas',
               'V1(FL)_target', 'V2(FL)_target',
               'V3(FL)_target', 'V4(FL)_target',
               'V1(FL)_meas', 'V2(FL)_meas',
               'V3(FL)_meas', 'V4(FL)_meas',
               'roll_in', 'pitch_in',
               'yaw_in', 'throttle_in',
               'engine_speed_limit', 'engine_speed_target',
               'engine_speed', 'throttle_position']

#Define struct
s = struct.Struct('H H f f f f f f H H H H H H H H H H H H H H H H')
PACKET_SIZE = 60    # packet # of bytes

# Global buffers
queue_start = []
my_packet = bytearray()
my_list_of_tuples = []

# Auto-detect available serial ports
def auto_detect_port():
    global com_port
    is_found = False
    
    print("\nAuto-detecting available serial ports...\n")

    # get the list
    port_list = list_ports.comports()

    for port in port_list:
        if "Arduino" in str(port.manufacturer):
            is_found = True
            my_port = str(port.device)
            print("Found", my_port ,"\n")

    # return
    if is_found:
        return my_port
    else:
        print("No applicable serial ports found.")
        print("Will try to connect to default:",com_port,"\n") 
        return com_port

def write_to_csv(data):
    global TIME_STR
    with open(FILE_PATH,'w', newline='') as out:
        csv_out=csv.writer(out)
        
        #write header
        csv_out.writerow(FILE_HEADER)
        
        #write data
        csv_out.writerows(data)

def is_start_condition(x):
    global queue_start
    x_int = int.from_bytes(x,"little")
    if x_int == 0xEF or x_int == 0xFE or x_int == 0xFF:
        queue_start.append(x_int)
    #check if start condition has occurred
    if( len(queue_start) == 4 ):
        # convert to uint
        val = struct.unpack('I', bytearray(queue_start))[0]
        if val == START_CONDITION:
            #match reset condition
            #reset queue
            queue_start = []
            return True
        else:
            #not yet, pop the first elemenet
            queue_start.pop(0)
            return False
    else:
        return False

def on_keyboard_interrupt(serial_port):
    global my_list_of_tuples
    #write on text file
    print("\nWriting to text file", FILE_PATH)
    write_to_csv(my_list_of_tuples)
    #exit serial port
    print("Closing",serial_port.port,"...")
    serial_port.close()
    print("Closed. Bye!")

# main function here
def main():
    # Print welcome message
    print("Speeder Speedy Datalogger v1.0")
    print("by Niel Cansino\n\n")

    print("Cleaning previously opened ports...")
    # Close existing serial connection if it exists
    try:
        serial_port.close()
        print("Closing port",com_port,"...\n")
    except NameError:
        print("No existing opened ports found.")

    print("Preparation done...\n\n")

    # Dynamically locate serial port
    my_port = auto_detect_port()

    # Open port
    try:
        serial_conn = serial.Serial(my_port, baud_rate) #Creating our serial object
    except serial.serialutil.SerialException:
        print("ERROR:    Exception on", my_port, "at",baud_rate,"occurred!!")
        print("          Please check if the port exists or if the device is connected.")
        print("\nQuitting...\n")
        quit()

    # Print serial port open msg
    print("Serial port",my_port,"opened!")
    
    #counter variables
    ctr_start_condition=0
    ctr_success=0

    #packet buffer
    my_packet = bytearray()

    try:
        while True:
            while ( serial_conn.inWaiting == 0 ): #Wait here until there is data
                pass #do nothing
            x = serial_conn.read()

            #detect start bit
            if is_start_condition(x):
                if 0 == ctr_start_condition % 100:
                    print( ctr_start_condition / 100 )
                ctr_start_condition += 1
                # initialize packet as empty byte array
                my_packet = bytearray()
                continue

            #insert x to my_packet
            my_packet += bytearray(x)

            #check if valid packet already
            if len(my_packet) == PACKET_SIZE:
                # decode
                unpacked_data = s.unpack(my_packet)

                #delete header for crc calculation
                del my_packet[0:4]
                #calculate crc
                crc_value_expect = CrcModbus.calc(bytes(my_packet))

                #verify CRC
                if crc_value_expect == unpacked_data[1]:
                    #add data to output tuple
                    my_list_of_tuples.append(unpacked_data)
                    #increment success counter
                    ctr_success += 1

    except KeyboardInterrupt:
        on_keyboard_interrupt(serial_conn)
    
if __name__ == '__main__':
    main()
