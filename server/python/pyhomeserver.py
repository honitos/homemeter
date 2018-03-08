#!/usr/bin/env python

from __future__ import print_function
#from datetime import datetime
import datetime
import time
import logging
import MySQLdb
import RPi.GPIO as GPIO
from struct import *        # this way we integrate all the contents in the global namespace
from RF24 import *
from RF24Network import *
from RF24Mesh import *

vlogformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
vloghandler = logging.StreamHandler()
vloghandler.setFormatter(vlogformatter)
vlog = logging.getLogger()
vlog.setLevel(logging.DEBUG)
vlog.addHandler(vloghandler)

DATABASE_HOSTNAME = "192.168.2.3"
DATABASE_NAME = "smartmeter"
DATABASE_USER = "smartmeter"
DATABASE_PASSWD = "smartmeter"

def mysql_init(host=DATABASE_HOSTNAME,db=DATABASE_NAME,user=DATABASE_USER,passwd=DATABASE_PASSWD):
    global sqldb
    
    vlog.info("Initiating database-connections...")
    sqldb = MySQLdb.connect(host,db,user,passwd)
    sqlcursor = sqldb.cursor()
    sqlcursor.execute("SHOW tables")
    sqltables = [v for (v,) in sqlcursor]
    if "easymeter" in sqltables:
        vlog.debug("Table 'easymeter' found, will be used for storing data.")
    else:
        # Create a table to store the data, if it does not exists
        vlog.warn("Table 'easymeter' does not exist in that database '",db,"', creating table...")
        sqlcommand = "CREATE TABLE IF NOT EXISTS `easymeter` ("
        sqlcommand+= "`SensorTime` int(10) unsigned NOT NULL DEFAULT '0',"
        sqlcommand+= "`Current` int(4) unsigned DEFAULT NULL,"
        sqlcommand+= "`Total` int(4) unsigned DEFAULT NULL,"
        sqlcommand+= "`DateTime` datetime(3) NOT NULL DEFAULT '0000-00-00 00:00:00.000',"
        sqlcommand+= "PRIMARY KEY (`SensorTime`),"
        sqlcommand+= "UNIQUE KEY `SensorTime` (`SensorTime`),"
        sqlcommand+= "KEY `DateTime` (`DateTime`)"
        sqlcommand+= ") ENGINE=InnoDB DEFAULT CHARSET=latin1"
        sqlcursor.execute(sqlcommand)
    return 0    

def mysql_insert(payload):
    now = datetime.datetime.utcnow()
    actSensorTime,valTotal,valTarif1,valTarif2,valCurrent = unpack("<LLLLL", bytes(payload))

    sqlcommand = "INSERT INTO easymeter (SensorTime,Current,Total,Datetime) "
    sqlcommand += "VALUES ("
    sqlcommand += str(actSensorTime) + ","
    sqlcommand += str(valCurrent) + ","
    sqlcommand += str(valTotal) + ","
    sqlcommand += "Now(3))"
    #print(sql_command)

    sqlcursor = sqldb.cursor()
    sqlcursor.execute(sqlcommand)
    sqldb.commit()

def rf24_init():
    """Initiate the whole rf24 stuff"""
    global radio, network, mesh
    
    vlog.info("Initiating RF24-Meshnetwork...")
    #RPi B
    # Setup for GPIO 22 CE and CE1 CSN with SPI Speed @ 8Mhz
    radio = RF24(RPI_V2_GPIO_P1_22, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
    network = RF24Network(radio)
    mesh = RF24Mesh(radio,network)

    # set the Node ID as Master, which will be 0
    mesh.setNodeID(0)

    # Connect to the mesh
    mesh.begin()

    #mesh.begin(108, RF24_250KBPS)
    #radio.setPALevel(RF24_PA_MAX) # Power Amplifier
    if vlog.getEffectiveLevel() == logging.DEBUG: radio.printDetails()
    return 0

def rf24_run():

    # dataformat from smartmeter client - that is the payload:
    # 
    # sml_dataset {
    #   uint32_t actSenstorTime;
    #   uint32_t valTotal;
    #   uint32_t valTarif1;
    #   uint32_t valTarif2;
    #   uint32_t valCurrent;
    # }
 
    vlog.info("Start to listen for messages from nodes, we are mesh-node (%s)",mesh.getNodeID())
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
                    #vlog.debug("Total: ",valTotal,"Current:",valCurrent,"from Client",oct(header.from_node)," at:",actSensorTime)
                    vlog.debug("Total: %s Current: %s from Client %s at %s" %(valTotal,valCurrent,oct(header.from_node),actSensorTime))
                    mysqlStatus = mysql_insert(payload)
                    if mysqlStatus == 0: vlog.warn("--> error writing t odb, error",mysqlStatus)
                else:
                    vlog.warn("Length of payload (%s) not correct, dataset will be ignored.",len(payload))
            else:
                #network.read(header,0,0);
                vlog.warn("Recieved bad message type",header.type,"from node",oct(header.from_node))

            time.sleep(2)

if __name__ == "__main__":
    vlog.info("Program started...")
    if mysql_init() == 0:
        if rf24_init() == 0:
            vlog.info("honitos HomeServer V0.01 started...")
            rf24_run()
            if sql:
                vlog.debug("Closing database...")
                sql.close()
    vlog.info("Program terminated...")
    exit()
