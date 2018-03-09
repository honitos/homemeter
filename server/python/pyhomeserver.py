#!/usr/bin/env python

# --
# -- include some basic libraries
from __future__ import print_function
import sys
import datetime
import time
from struct import *        # this way we integrate all the contents in the global namespace without using struct.-namespace


# --
# -- configuring the logger
import logging
vlogformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
vloghandler = logging.StreamHandler()
vloghandler.setFormatter(vlogformatter)
vlog = logging.getLogger()
vlog.setLevel(logging.DEBUG)
vlog.addHandler(vloghandler)


# --
# -- include sql-stuff
import MySQLdb
# -- define some configurration for the sql-access
DATABASE_HOSTNAME = "192.168.2.3"
DATABASE_NAME = "smartmeter"
DATABASE_USER = "smartmeter"
DATABASE_PASSWD = "smartmeter"
DATABASE_TABLE ="easymeter"
import warnings
# -- modify behaviour of warnings: they should be raise an exception to catch them
warnings.filterwarnings("error", category=MySQLdb.Warning)


# --
# -- include stuff for using the rf24-module
import RPi.GPIO as GPIO
from RF24 import *
from RF24Network import *
from RF24Mesh import *


# --------------------------------------------------------------------------------------
# --
# -- Define functions for rf24 and SQL handling
# --
# --------------------------------------------------------------------------------------

def mysql_init(host=DATABASE_HOSTNAME,db=DATABASE_NAME,user=DATABASE_USER,passwd=DATABASE_PASSWD):
    global sqldb
    
    vlog.info("Initiating database-connections...")
    sqldb = MySQLdb.connect(host,db,user,passwd)
    sqlcursor = sqldb.cursor()
    sqlcursor.execute("SHOW tables")
    sqltables = [v for (v,) in sqlcursor] # make a list of sqlcursor
    if DATABASE_TABLE in sqltables:
        vlog.debug("Table '%s' found, will be used for storing data.",DATABASE_TABLE)
    else:
        # Create a table to store the data, if it does not exists
        sqlcommand = "CREATE TABLE IF NOT EXISTS `" + DATABASE_TABLE + "` ("
        sqlcommand+= "`SensorTime` int(10) unsigned NOT NULL DEFAULT '0',"
        sqlcommand+= "`Current` int(4) unsigned DEFAULT NULL,"
        sqlcommand+= "`Total` int(4) unsigned DEFAULT NULL,"
        sqlcommand+= "`DateTime` datetime(3) NOT NULL DEFAULT '0000-00-00 00:00:00.000',"
        sqlcommand+= "PRIMARY KEY (`SensorTime`),"
        sqlcommand+= "UNIQUE KEY `SensorTime` (`SensorTime`),"
        sqlcommand+= "KEY `DateTime` (`DateTime`)"
        sqlcommand+= ") ENGINE=InnoDB DEFAULT CHARSET=latin1"
        try:
            vlog.warn("Table '%s' does not exist in database '%s', creating table..." % (DATABASE_TABLE,db))
            sqlcursor.execute(sqlcommand)

        except(MySQLdb.Warning) as e:
            vlog.warn(e)

        except(MySQLdb.Error, MySQLdb.Warning) as e:
            vlog.error("Table could not been created, due to following SQL-reason:")
            return False

        except:
            vlog.error("I am sorry, but we have an undhandled exception here:")
            e = sys.exc_info()[:2]
            #vlog.error("%s - Error (%s)" % e)
            vlog.error(e)
            return False

    return True


def mysql_insert(payload):
    now = datetime.datetime.utcnow()
    actSensorTime,valTotal,valTarif1,valTarif2,valCurrent = unpack("<LLLLL", bytes(payload))

    sqlcommand = "INSERT INTO easymeter (SensorTime,Current,Total,Datetime) "
    sqlcommand += "VALUES ("
#    sqlcommand += str(actSensorTime) + ","
    sqlcommand += str("1") + ","

    sqlcommand += str(valCurrent) + ","
    sqlcommand += str(valTotal) + ","
    sqlcommand += "Now(3))"
    try:
        #vlog.debug("sending to db: ",sql_command)
        sqlcursor = sqldb.cursor()
        sqlcursor.execute(sqlcommand)
        sqldb.commit()

    except(MySQLdb.Error,MySQLdb.Warning) as e:

        if e[0]==1061: #Already Exists Primary Key error
            vlog.error("SQLDB-Error: Dataset with SensorTime (%d) already exists, will be ignored.",actSensorTime)
        else:
            vlog.error("SQLDB-Error (%d): %s" % (e.args[0], e.args[1]))

    except:
        vlog.error("I am sorry, but we have an undhandled exception here:")
        e = sys.exc_info()
        vlog.error(e)
        return False


    return True


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
    return True

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
                    vlog.debug("Total: %s Current: %s from Client %s at %s" %(valTotal,valCurrent,oct(header.from_node),actSensorTime))

                    mysqlStatus = mysql_insert(payload)
                    if mysqlStatus == False: 
                        vlog.warn("--> error writing to db")

                else:
                    vlog.warn("Length of payload (%s) not correct, dataset will be ignored.",len(payload))
            else:
                #network.read(header,0,0);
                vlog.warn("Recieved bad message type",header.type,"from node",oct(header.from_node))

            time.sleep(2)


# --------------------------------------------------------------------------------------
# --
# -- main routine
# --
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    vlog.info("Program started...")
    if mysql_init() == True:
        if rf24_init() == True:
            vlog.info("honitos HomeServer V0.01 started...")
            rf24_run()

    #-- closing connection to db
    if sqldb:
        vlog.debug("Closing database...")
        sqldb.close()

    vlog.debug("Program terminated...")

else:
    vlog.error("This program may not be executed as a module.")

exit()
