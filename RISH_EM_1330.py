#!/usr/bin/env python3

import time
import minimalmodbus

rs485 = minimalmodbus.Instrument('/dev/ttyUSB0', 2)
rs485.serial.baudrate = 9600
rs485.serial.bytesize = 8
rs485.serial.parity = minimalmodbus.serial.PARITY_NONE
rs485.serial.stopbits = 1
rs485.serial.timeout = 1
rs485.debug = False
rs485.mode = minimalmodbus.MODE_RTU

Para =["Voltage R","Voltage Y","Voltage B","Current R","Current Y","Current B","W1","W2","W3","VA1","VA2","VA3","VAR1","VAR2","VAR3","PF1","PF2","PF3"]

Addr =[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34]

print(len(Para),len(Addr))

Datapackage = {}

#print (rs485)
#print(rs485.read_register(0, functioncode=4,))
#Volts_A = rs485.read_float(0, functioncode=4, number_of_registers=4)
#print ('Voltage: {0:.1f} Volts'.format(Volts_A))
while 1 :
    for indx,A in enumerate(Addr):
        Val = rs485.read_float(A, functioncode=4, number_of_registers=2)
        #print("Addr-",A)
        #print(str(f'{Val :.2f}'),Para[indx])
        Datapackage[Para[indx]] = float(str(f'{Val :.2f}'))
        time.sleep(.1)

    print("Datapackage-",Datapackage)

    #reset
    Datapackage = {}