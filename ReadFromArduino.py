#!/usr/bin/env python
import time
import serial
import datetime
import sys
import os
import RPi.GPIO as GPIO

#Once PS charging is initiated it will continue for 
ps_charging_time = 4.0*60.0*60.0 #4 hours in seconds
charge_stop_time = 0.0

#set up power relay
relaypin = 26 #BCM number for board #25
GPIO.setmode(GPIO.BCM)
GPIO.setup(relaypin,GPIO.OUT)
#Connect power supply - supply is on when pin is low
GPIO.output(relaypin,GPIO.HIGH)

#set up relay logic override - will let the PS be controlled only by the GPIO pin
controlpin = 5
GPIO.setup(controlpin,GPIO.IN)

#Set GPIO pin 6 to indicate that battery is charging - current is negative
charging_pin = 6
GPIO.setup(charging_pin,GPIO.OUT)

#For influx load
from influxdb import InfluxDBClient
# influx configuration - edit these
ifuser = "grafana"
ifpass = "JonWb2mnf"
ifdb   = "home"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "PowerUse"
timenow=datetime.datetime.utcnow()

#Initialize battery cumulative max and min current load
accum_bat_cur = 100.0 #Accumulated battery current since program start
cum_max_bat_cur = 0.0 #Maximum battery current since program start - start low and let it increase with read values
cum_min_bat_cur = 100 #Minumum (most negative) battery current since program start - start high and let it decrease

"""
#Read previous min and max charge levels from file
with open('/home/pi/minfile.txt') as minfile:
        file_cum_min_bat_cur = float(minfile.readline())
        cum_min_bat_cur = file_cum_min_bat_cur
        minfile.close()
        print ('Read minvalue from file ', str(cum_min_bat_cur))

with open('/home/pi/maxfile.txt') as maxfile:
        file_cum_max_bat_cur = float(maxfile.readline())
        cum_max_bat_cur = file_cum_max_bat_cur
        maxfile.close()
        print ('Read maxvalue from file ', str(cum_max_bat_cur))
"""

#Initialize serial port from GPIO pins
ser = serial.Serial('/dev/ttyS0', 9600)
#ser = serial.Serial('/dev/ttyAMA0', 9600)
#ser = serial.Serial('/dev/ttyACM0', 9600)

#initialize the value of the line to be read
x = 'B,13.00,-167.82,12.83,-1693.10,22030.00,S,13.37,125.66,13.50,1256.90,16806.00,L,12.94,196.16,13.13,2450.90,31362.00,P,13.10,284.79,13.38,2831.40,37064.00,-1693.10'

while 1:
        last_x ='B,13.00,-167.82,12.83,-1693.10,22030.00,S,13.37,125.66,13.50,1256.90,16806.00,L,12.94,196.16,13.13,2450.90,31362.00,P,13.10,284.79,13.38,2831.40,37064.00,-1693.10'
        try:
                x=ser.readline().decode('ascii')
        except UnicodeDecodeError:
                print ("IO Error")
                x=last_x
       
        print (x)
        
        #Reading string values
        try:
                bt_ind,bt_buss,bt_shunt,bt_loads,bt_curs,bt_pwrs,\
                lo_ind,lo_buss,lo_shunt,lo_loads,lo_curs,lo_pwrs,\
                so_ind,so_buss,so_shunt,so_loads,so_curs,so_pwrs,\
                ps_ind,ps_buss,ps_shunt,ps_loads,ps_curs,ps_pwrs,\
                cum_batt_currents = x.split(',')
        except ValueError: #Still getting value error here from last_x.split
                print ("Value Error")
                bt_ind,bt_buss,bt_shunt,bt_loads,bt_curs,bt_pwrs,\
                lo_ind,lo_buss,lo_shunt,lo_loads,lo_curs,lo_pwrs,\
                so_ind,so_buss,so_shunt,so_loads,so_curs,so_pwrs,\
                ps_ind,ps_buss,ps_shunt,ps_loads,ps_curs,ps_pwrs,\
                cum_batt_currents = last_x.split(',')
        
        #Current amounts are in milliamps- convert to amps
        bt_cur = -float(bt_curs) / 1000.0
        so_cur = float(so_curs) / 1000.0
        lo_cur = -float(lo_curs) / 1000.0
        ps_cur = -float( ps_curs) / 1000.0
        
        #float other values
        bt_bus = float(bt_buss)
        bt_load = float(bt_loads)
        bt_pwr = float(bt_pwrs)
        lo_bus = float(lo_buss)
        lo_load = float(lo_loads)
        lo_pwr = float(lo_pwrs)
        so_bus = float(so_buss)
        so_load = float(so_loads)
        so_pwr = float(so_pwrs)
        ps_bus = float(ps_buss)
        ps_load = float(ps_loads)
        ps_pwr = float(ps_pwrs)
        cum_batt_current = float(cum_batt_currents)
        
#Compute battery charge level based on Pi readings, not Arduino readings    
        #For new run set accum battery current to cum_batt_current from the Arduino - but can't do that here
        #accum_bat_cur = float(cum_batt_current) / 1000.0
        
        #Add net present battery current to accumulated battery current - this is computed by the Pi
        #Replaced the Pi computed accumulated current with the Arduino computed amount - switched back because Arduino cum current looks wrong
        accum_bat_cur = accum_bat_cur - (float(bt_cur) / 3600.0) # convert to amp-hours
        #accum_bat_cur = float(cum_batt_current) / 1000.0
        #Compute the highest cumulative battery current (maximum battery charge) since program start
        cum_max_bat_cur = max(cum_max_bat_cur,accum_bat_cur)
        #Compute the lowest cumulative battery current (minimum battery charge) since program start
        cum_min_bat_cur = min(cum_min_bat_cur,accum_bat_cur)
        
        #Compute current percent of maximum charge
        if (cum_max_bat_cur == 0):
                pct_max_chg = 0.0
        else:
                #Need to negate accum bat current to show ratio right
                pct_max_chg = (accum_bat_cur / cum_max_bat_cur)
        
        #Percent of load coming from solar
        if(lo_cur == 0):
                solar_pct_of_load = 0
        else:
                solar_pct_of_load = (float(so_cur)/float(lo_cur))

        #Percent of load coming from PS
        if(lo_cur == 0):
                ps_pct_of_load = 0
        else:
                ps_pct_of_load = (float(ps_cur)/float(lo_cur))

        #Percent of load coming from battery
        if(lo_cur == 0):
                bt_pct_of_load = 0
        else:
                bt_pct_of_load = max(-(float(bt_cur)/float(lo_cur)),0.0)

#Control the power supply           
        #Test GPIO control pin to see if logic below should be applied - control pin will defeat all logic below
        #Also note that the ReadSerial program can turn off the power supply
        if GPIO.input(controlpin):
                #Turn on power supply if voltage < 11.8
                
                print ("Battery bus volt = ",str(bt_bus))
                
                if bt_bus < 11.8: 
                        print ("Turning on PS")
                        GPIO.output(relaypin, GPIO.LOW)
                        
                        remaining_charge_time = (charge_stop_time - time.time())/60.0
                        if remaining_charge_time < 0.0: # Charge timer has expired, need to reset it for the next charge
                                charge_stop_time = time.time() + ps_charging_time #time at which PS can be disconnected
                        
                        print ("Time now: ",str(time.time()))
                        print ("PS charging time: ", str(ps_charging_time))
                        print ("Charge stop time: ",str(charge_stop_time))
                        
                        print ("Voltage low - power supply ON")
                remaining_charge_time = (charge_stop_time - time.time())/60.0
                print ("Stopping PS in minutes: ", str(remaining_charge_time))
                
                #Turn off supply if solar current is .5 amp higher than load current -can't use 1 amp because the load is 2.3 amps and the max current that the 
                #device will read is 3.2 amps
                if float(so_cur) > float(lo_cur) + 0.5 and time.time() > charge_stop_time: 
                        GPIO.output(relaypin,GPIO.HIGH)
                        print ("Power supply OFF - solar current exceeds load")
      
#Write Influx record
        try:
                timenow=datetime.datetime.utcnow()
                print ("Record write time = ",str(timenow))
                body = [  
                        {
                                "measurement": measurement_name,
                                "time": timenow,
                                "fields": {
                                    #"Battery indicator": int(bt_ind),
                                    "Battery Bus Voltage": float(bt_bus),
                                    "Battery Shunt Voltage": float(bt_shunt),
                                    "Battery Load Voltage": float(bt_load),
                                    "Battery Current": float(bt_cur),
                                    "Battery Power": float(bt_pwr),
                                    
                                    "Solar Bus Voltage": float(so_bus),
                                    "Solar Shunt Voltage": float(so_shunt),
                                    "Solar Load Voltage": float(so_load),
                                    "Solar Current": float(so_cur),
                                    "Solar Power": float(so_pwr),
                                    
                                    "Load Bus Voltage": float(lo_bus),
                                    "Load Shunt Voltage": float(lo_shunt),
                                    "Load Load Voltage": float(lo_load),
                                    "Load Current": float(lo_cur),
                                    "Load Power": float(lo_pwr),
                                    
                                    "PS Bus Voltage": float(ps_bus),
                                    "PS Shunt Voltage": float(ps_shunt),
                                    "PS Load Voltage": float(ps_load),
                                    "PS Current": float(ps_cur),
                                    "PS Power": float(ps_pwr),
                                    
                                    "Cumulative Battery Current": float(accum_bat_cur),
                                    "Max Cumulative Battery Current": float(cum_max_bat_cur),
                                    "Min Cumulative Battery Current": float(cum_min_bat_cur),
                                    "Pct Maximum Charge": float(pct_max_chg),
                                    "Solar Pct of Load": float(solar_pct_of_load),
                                    "Pwr Supply Pct of Load": float(ps_pct_of_load),
                                    "Battery Pct of Load": float(bt_pct_of_load),
                                    "Arduino Cum Battery Current": float(cum_batt_current)
                                    }
                        }
                ]

                # connect to influx
                ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)

                # write the measurement
                ifclient.write_points(body)
        except Exception as e:
                print (e.__doc__)
                print (e.message)
                time.sleep(30)
                continue
        
        print ("Influx record written")
        print ("-----------------------------------------")
  #      print ("Influx record suppressed")
