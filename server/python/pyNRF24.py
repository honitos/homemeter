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

	# Connect to the mesh
    print("honitos HomeServer V0.01 started...\n");
    mesh.begin()

    #mesh.begin(108, RF24_250KBPS)
    #radio.setPALevel(RF24_PA_MAX) # Power Amplifier
    radio.printDetails()

def rf24_run():

	# dataformat from smartmeter client - that is the payload:
	# 
	# sml_dataset {
	#	uint32_t actSenstorTime;
	#	uint32_t valTotal;
	#	uint32_t valTarif1;
	#   uint32_t valTarif2;
	#   uint32_t valCurrent;
	# }
 
	header = RF24NetworkHeader()
	while 1:
		# Call network.update as usual to keep the network updated
		mesh.update()

 		# In addition, keep the 'DHCP service' running on the master node so address$
  		# be assigned to the sensor nodes
		mesh.DHCP()

		# Check for incoming data from the sensors
		while network.available():
			network.peek(header)
			if chr(header.type) == "E":
				header, payload = network.read(20)
				if len(payload) == 20:
					actSensorTime,valTotal,valTarif1,valTarif2,valCurrent = unpack("<LLLLL", bytes(payload))
					print("Total:",valTotal,",Current:",valCurrent,"from Client",oct(header.from_node)," at:",actSensorTime)
				else:
					print("Length of payload not correct, dataset will be ignored.")
			else:
				#network.read(header,0,0);
				print("Recieved bad message type (%d) from node %d",header.type,oct(header.from_node))

			time.sleep(1)

if __name__ == "__main__":
    rf24_init()
    rf24_run()
    exit()
