# --
# -- include stuff for using the rf24-module
import RPi.GPIO as GPIO
from RF24 import *
from RF24Network import *
from RF24Mesh import *

import struct

radio = RF24(RPI_V2_GPIO_P1_22, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
network = RF24Network(radio)
mesh = RF24Mesh(radio,network)

mesh.setNodeID(0)
mesh.begin()

radio.printDetails()

#print("=====================================")
#for p in dir(mesh):
#    print(p)
##exit()

print("start listening...")
#for p in dir(header):
#    print(p)
#exit()
while 1:
    mesh.update()
    mesh.DHCP()

    while network.available():
        header, payload = network.read(10)
        print("Received message from {}, id {}: {}".format(header.from_node, header.id, payload))
