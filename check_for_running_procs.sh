#!/bin/bash
#Checks for  running status of last WX process
#If that process doesn't exist reboot
dt=`date '+%d/%m/%Y %H:%M:%S'`
#echo "$dt"

#Check ReadSerial process
LAST_PROCESS=$(tail /home/pi/read_serial_process_id.txt)
echo $LAST_PROCESS
ps -h  $LAST_PROCESS
RETURN_CODE=$?
echo $?
echo $RETURN_CODE
if [ "$RETURN_CODE" -eq "1" ]
then
	echo "Restarting ReadSerial"
	python /home/pi/ReadSerial.py > /dev/null & echo $! > read_serial_process_id.txt &
	logger "Restarted ReadSerial"
else
	echo "Continuing ReadSerial" 
fi
#-------------------------------------------------------------
#Check ReadArduino process
LAST_PROCESS=$(tail /home/pi/read_arduino_process_id.txt)
echo $LAST_PROCESS
ps -h  $LAST_PROCESS
RETURN_CODE=$?
echo $?
echo $RETURN_CODE
if [ "$RETURN_CODE" -eq "1" ]
then
        echo "Restarting ReadArduino"
        python /home/pi/ReadFromArduino.py > /dev/null & echo $! > read_arduino_process_id.txt &
        logger "Restarted ReadArduino"
else
        echo "Continuing ReadArduino"
fi

