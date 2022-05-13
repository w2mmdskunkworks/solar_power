import RPi.GPIO as GPIO
#set up power relay
relaypin = 26 #BCM number for board #25
GPIO.setmode(GPIO.BCM)
GPIO.setup(relaypin,GPIO.OUT)
#Connect power supply - supply is on when pin is low
GPIO.output(relaypin,GPIO.LOW)

GPIO.output(relaypin, GPIO.HIGH)
print ("Power supply OFF")
