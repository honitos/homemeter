import RPi.GPIO as GPIO
import time
from time import sleep

GPIO.setmode(GPIO.BOARD)
ports_board = [3,5,7,8,10,11,12,13,15,16,18,19,21,22,23,24,26]
#GPIO.setmode(GPIO.BCM)
#ports_bcm = [2,3,4,17,27,22,10,9,11,14,15,18,23,24,25,8,7]

# Using a dictionary as a lookup table to give a name to gpio_function() return code
port_use = {0:"OUT", 1:"IN",40:"SER",41:"SPI",42:"I2C",
           43:"PWM", -1:"???"}

# loop through the list of ports/pins querying and displaying the status of each
#GPIO.setup(10,GPIO.IN)
title = "PIN #: "
mode = "Mode : "
for port in ports_board:
    title = title + " {0:2d} |".format(port)
    usage = GPIO.gpio_function(port)
    mode = mode + " {0:3s}|".format(port_use[usage])
    if usage == 1:
        GPIO.setup(port,GPIO.IN)
    #else:
        #GPIO.setup(port,GPIO.OUT)

print title
print '-'*len(title)
print mode

a=0
try:
    while a<20:
        led = "Value: "
        for port in ports_board:
            usage = GPIO.gpio_function(port)
            if usage == 1:
                status = str(GPIO.input(port))
            else:
                status = '-'
            led = led + " {0:3s}|".format(status)
        print led," [" + str(a) + "]"
        sleep(1)
        a = a + 1
except KeyboardInterrupt:
        GPIO.cleanup()