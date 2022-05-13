#!/usr/bin/env python
#Reads the output of the PWRgate device and populates the Influx database for Grafana
import time
import serial
import sys
import os
import datetime
import RPi.GPIO as GPIO

#Use as load current when battery is powering it
load_current = 2.3 

#set up power relay
relaypin = 26 #BCM number for board #25
GPIO.setmode(GPIO.BCM)
GPIO.setup(relaypin,GPIO.OUT)
#Connect power supply - supply is on when pin is low
GPIO.output(relaypin,GPIO.LOW)
        
#set up relay logic override - will let the PS be controlled only by the GPIO pin
controlpin = 5

#For influx load
from influxdb import InfluxDBClient
# influx configuration - edit these
ifuser = "grafana"
ifpass = "JonWb2mnf"
ifdb   = "home"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "PWRgate"
timenow=datetime.datetime.utcnow()

print ("Reading last load current")
#tracker for cumulative battery current
try:
        #Retrieve the last cumulative charge from influx database
        query_result = ifclient.query ('SELECT ("Cum Battery Current") from "home"."autogen"."PWRgate" ORDER BY DESC LIMIT 1')
        query_lines = query_result.get_points()
        print ("Reading Influxdb")
        for query_line in query_lines:
                print ("Time: %s, Cum Current %i" % (query_line['time'],query_line['Cum Battery Current']))
                cum_batt_current = query_line['Cum Battery Current']
except:
        print ("Influxdb read failed = loading cun current at 100")
        cum_batt_current = 100
        
#Patch because last run overwrote last influx record
#cum_batt_current = 136

#Wipe out previous log file
if os.path.exists('/home/pi/logfile.txt'): os.remove('/home/pi/logfile.txt')

ser = serial.Serial(
        #This was the line in the code on the dead SD card
        port='/dev/ttyACM0', #Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
        #port='/dev/ttyS0', #This matches the line in the /etc/rules.d/49-custom.rules file
        baudrate = 9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
)
counter=0
# Send a 3 then 10 blank lines

x=ser.readline()
print (x)        
x=ser.readline()
print (x)        
x=ser.readline()
print (x)        
x=ser.readline()
print (x)

print ("Writingto serial port")      
StringToWrite= ('3'+'\r')
ser.write (StringToWrite.encode())

#ser.write ('3\r')
x=ser.readline()
print (x)

StringToWrite= ('14.4'+'\r')
ser.write (StringToWrite.encode())
#ser.write ('14.4'+'\r')
#time.sleep(1)


#Initialize CR to write
StringToWrite= ('\r')

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())
#ser.write ('\r')
#time.sleep(1)

x=ser.readline()
print (x)
#ser.write ('\r')
ser.write (StringToWrite.encode())
#time.sleep(1)

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())
#ser.write ('\r')
#time.sleep(1)

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())
#ser.write ('\r')
#time.sleep(1)

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())
#ser.write ('\r')
#time.sleep(1)

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())

x=ser.readline()
print (x)
ser.write (StringToWrite.encode())

last_x = x

#Now read from the port
while 1:
        timenow=datetime.datetime.utcnow()
        try:
                xb=ser.readline() #type is bytes
                x=str(xb,'utf-8')
        except ValueError:
                x=last_x
                print ("Value Error")        
 #       logfile = open('/home/pi/logfile2.txt', 'a+')
 #       logfile.write(x)
 #       logfile.close()
        
        print ("Line1=" + x)
        #print x.split(" ")
        fields=x.split(" ")
        print ('Fields = ' + str(len(fields)))
        
        #if we're reading the second line, read an additional line to cycle to the first
        if len(fields) == 12: x=str(ser.readline())
        
        #Fields has length of 17 once it's reading the telemetry
        if len(fields) >= 12:
                #print 'Fields0 =' + fields[0]
                #print 'Fields2 =' + fields[2]
                #batt=fields[len(fields)-12]
                #print ('Batt= ' +batt)
                #ps=fields[len(fields)-13]
                #print ('PS= ' + ps)
                print ('Current time='+str(timenow))
                devstatus=(x[1:11])
                devstatus = devstatus.strip()
                print ('PS Sub='+str(devstatus))
                
                unitstatus = 0
                if devstatus == 'Trickle': unitstatus = 2
                if devstatus == 'PS Off': unitstatus = 1
                if devstatus == 'Charging': unitstatus = 3
                if devstatus == 'MPPT': unitstatus = 4       
                print ('UnitStatus='+str(unitstatus))
                
                try:
                        pss=float(x[14:19])
                        print ('PSS='+str(pss))
                        bat=float(x[25:30])
                        print ('Batt='+str(bat))
                        battcur=float(x[32:38])
                        print ('Battery current='+str(battcur))
                        solvolt=float(x[45:49])
                        print ('Solar voltage='+str(solvolt))
                        statmin=float(x[58:61])
                        print ('Status minutes='+str(statmin))
                        # ~ pnum=float(x[65:68])
                        # ~ print ('Pnum='+str(pnum))
                        # ~ adc=(x[73:76])
                        # ~ print ('ADC='+str(adc))
                except:
                        continue
                
                #Duplicates code in ReadArduino
                if bat < 11.8: 
                        GPIO.output(relaypin, GPIO.LOW)
                        print ("Power supply ON")
                
                #If power is off assume battery is powering load
                if (unitstatus == 1): battcur = -load_current
                
                #Accumulate battery current for charge percentage - recorded every 2 seconds
                cum_batt_current = cum_batt_current + battcur/1800

                #Test GPIO control pin to see if logic below should be applied
                #if GPIO.input(controlpin):
                #if 1:
                #This logic is moved to ReadFromArduino.py
                        #Turn  PS off if solar voltage is > 15 volts - should be sufficient to charge
                        #if solvolt > 15: GPIO.output(relaypin,GPIO.HIGH)
                        #Turn PS off if trickle charging
                        #if unitstatus == 2: GPIO.output(relaypin,GPIO.HIGH)
                        #Turn PS off if solar charging
                        #if unitstatus == 4: GPIO.output(relaypin,GPIO.HIGH)

                # Load the data into Influx
                body = [
                    {
                        "measurement": measurement_name,
                        "time": timenow,
                        "fields": {
                            "Status": devstatus,
                            "PS Voltage": pss,
                            "Battery Voltage": bat,
                            "Battery Current": battcur,
                            "Solar Voltage": solvolt,
                            "Status Minutes": statmin,
                            "Unit Status" :  unitstatus,
                            "Cum Battery Current": cum_batt_current                            
                        }
                    }
                ]

                # connect to influx
                ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)

                # write the measurement
                try:
                        ifclient.write_points(body)
                except Exception as e:
                        print (e.__doc__)
                        print (e.message)
                        time.sleep(30)
                        continue
                      
        #print "Line1 split = " + x.split(" ")[0]
        xb=ser.readline() #type is bytes
        x=str(xb,'utf-8')
        print ("Line2=" + x)


