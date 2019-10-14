#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --
# -- include some basic libraries
from __future__ import print_function
import sys
import datetime
import time
from math import log10, floor
from struct import *        # this way we integrate all the contents in the global namespace without using struct.-namespace

# --
# -- configuring the logger
import logging
vlogformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
termhandler = logging.StreamHandler()
termhandler.setFormatter(vlogformatter)
filehandler = logging.FileHandler("homeserver.log")
filehandler.setFormatter(vlogformatter)
vlog = logging.getLogger()
vlog.setLevel(logging.INFO)
vlog.addHandler(termhandler)
#vlog.addHandler(filehandler)


# --
# -- include stuff for using the rf24-module
import RPi.GPIO as GPIO
from RF24 import *
from RF24Network import *
from RF24Mesh import *

def rf24_init():
    """Initiate the whole rf24 stuff"""
    global radio, network, mesh

    vlog.info("Initiating RF24-Meshnetwork...")
    #RPi2+ B
    # Setup for GPIO 22 CE and CE1 CSN with SPI Speed @ 8Mhz
    radio = RF24(RPI_V2_GPIO_P1_22, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)

    network = RF24Network(radio)

    mesh = RF24Mesh(radio,network)

    # set the Node ID as Master, which will be 0
    mesh.setNodeID(0)
    #vlog.info("mesh_address = %o" % mesh.mesh_address)
    #vlog.info("NodeID of this node is %s" % mesh._nodeID)
    #vlog.info("current number of nodes = %i" & mesh.addrListTop)

    # Connect to the mesh
    mesh.begin()
    #mesh.begin(30,RF24_1MBPS)
    #mesh.begin(30,RF24_250KBPS)
    #mesh.begin(108, RF24_250KBPS)

    #radio.setPALevel(RF24_PA_MAX) # Power Amplifier
    #radio.printDetails()

    return True

# --------------------------------------------------------------------------------------
# --
# -- main routine
# --
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        vlog.info("Program started...")
        vlog.info("Initiating RF-Network...")
        if rf24_init() == True:
            vlog.info("Start to listen for messages from nodes, we are mesh-node (%s)",mesh.getNodeID())
            header = RF24NetworkHeader()
            payload = None
            
            while 1:
                # === Network-Handling
                # Call network.update as usual to keep the network updated
                mesh.update()
                
                # In addition, keep the 'DHCP service' running on the master node so address$
                # be assigned to the sensor nodes
                mesh.DHCP()
                
                # Check for incoming data from the sensors
                while network.available():
                    network.peek(header)
                    header, payload = network.read(4)
                    vlog.info(header)

    except:
        e = sys.exc_info()
        vlog.error(e)
        raise
                        
    finally:
        vlog.debug("Program terminated...")


else:
    vlog.error("This program may not be executed as a module.")

exit()

