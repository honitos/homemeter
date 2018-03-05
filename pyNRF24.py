#!/usr/bin/env python

from __future__ import print_function
import time
from struct import *
from RF24 import *
from RF24Network import *
from RF24Mesh import *
import RPi.GPIO as GPIO


def rf24_init():
    """Initiate the whole rf24 stuff"""
    global radio, network, mesh
	
    #RPi B
    # Setup for GPIO 22 CE and CE1 CSN with SPI Speed @ 8Mhz
    radio = RF24(RPI_V2_GPIO_P1_22, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
    network = RF24Network(radio)
    mesh = RF24Mesh(radio,network)

    # set the Node ID as Master, which will be 0
    mesh.setNodeID(0)
    mesh.begin()
    #mesh.begin(108, RF24_250KBPS)
    #radio.setPALevel(RF24_PA_MAX) # Power Amplifier
    radio.printDetails()

def rf24_run():
    while 1:
	mesh.update()
	mesh.DHCP()
	while network.available():
	header, payload = network.read(16)
	print("empfange etwas, payload ", len(payload))
	ms, number = unpack(">LL", bytes(payload))
        #print("received payload ", number," at ", ms, " from", oct(header.from_node))
	type = header.type
	print(type)	
	time.sleep(1)

if __name__ == "__main__":
    rf24_init()
    rf24_run()
    exit()
