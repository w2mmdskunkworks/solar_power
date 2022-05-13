python /home/pi/ReadSerial.py > /dev/null & echo $! > read_serial_process_id.txt
python /home/pi/ReadFromArduino.py > /dev/null & echo $! >read_arduino_process_id.txt

