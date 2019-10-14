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
vlog.setLevel(logging.WARN)
#vlog.addHandler(termhandler)
vlog.addHandler(filehandler)


class globalData:
    energyRate = 26.98
    totalBeginOfYear = 0.0
    lastError = ""

class energyCurrent:
    sensorTime = 0
    value = 0
    highest = 0.0
    lowest = 10000.0
    total = 0
    totalCurrentYear = 0.0
    highestTime = ""
    lowestTime = ""
    from_node = 0


# windowing 
from modules.intuition import intuition
screen = None
 
# --
# -- configuring the sqlthings
from modules.thesqlthing import *


# --------------------------------------------------------------------------------------
# --
# -- Define functions for MQTT
# --
# --------------------------------------------------------------------------------------
# --
# -- MQTT stuff
import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
    """ Connection errors rc
    0: Connection successful
    1: Connection refused – incorrect protocol version
    2: Connection refused – invalid client identifier
    3: Connection refused – server unavailable
    4: Connection refused – bad username or password
    5: Connection refused – not authorised
    6-255: Currently unused.
    """
    if rc == 0:
        client.connected_flag = True
        print("mqtt connection ok")
    else:
        print("there was an error while connecting: ", rc)

import yaml

with open('secrets.yaml') as secretsfile:
    secrets = yaml.load(secretsfile, Loader = yaml.FullLoader)

mqtt.Client.connected_flag = False
broker_address = secrets['mqtt']['host']

mc = mqtt.Client(client_id = "homeserver")
mc.username_pw_set(secrets['mqtt']['username'], secrets['mqtt']['password'])
mc.on_connect = on_connect

mc.loop_start()
print("connecting to broker at (%s) with username (%s)" % (secrets['mqtt']['host'], secrets['mqtt']['username']))

mc.connect(broker_address)
while not mc.connected_flag:
    print("waiting...")
    time.sleep(1)

print("starting mainloop")
mc.loop_stop()


# --------------------------------------------------------------------------------------
# --
# -- Define functions for rf24 and SQL handling
# --
# --------------------------------------------------------------------------------------
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


def rf24_run():
    global win_data, win_chart, globalData
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

    chartmode = 'continues'
    current = energyCurrent()
    globalData = globalData()
    energyData = []
    payload = None

    _dt = '2019-01-01'
    _result = mysql.getDatasetByDate(_dt)
    if _result:
        globalData.totalBeginOfYear = _result[0][1] / 10000.0

    while 1:
        # === Event-Handling
        tevent = screen.screen.getch()
        if tevent in [27,ord("q"),screen.curses.KEY_EXIT]:
            return None

        elif tevent == screen.curses.KEY_RESIZE:
            screen.update_screen()
            update_windows()

        elif tevent in range(ord("1"),ord("9")):
            screen.write_status("setting colorset to " + chr(tevent))
            screen.colorset = int(chr(tevent)) 
            screen.update_screen()

        elif tevent != -1:
            tchar = chr(tevent)
            screen.write_status("keypress detected = " + tchar)

        # === Network-Handling
        # Call network.update as usual to keep the network updated
        mesh.update()

        # In addition, keep the 'DHCP service' running on the master node so address$
        # be assigned to the sensor nodes
        mesh.DHCP()

        # Check for incoming data from the sensors
        data_received = False
        while network.available():
            network.peek(header)

            if chr(header.type) == "E":
                header, payload = network.read(20)
                if len(payload) == 20:
                    actSensorTime,valTotal,valTarif1,valTarif2,valCurrent = unpack("<LLLLL", bytes(payload))
                    current.sensorTime = actSensorTime
                    current.value = valCurrent / 100.0
                    current.total = valTotal / 10000.0
                    current.totalCurrentYear = current.total - globalData.totalBeginOfYear
                    if current.value > current.highest:
                        current.highest = current.value
                        current.highestTime = time.localtime()
                    if current.value < current.lowest:
                        current.lowest = current.value
                        current.lowestTime = time.localtime()

                    # Wert in DB speichern
                    mysqlStatus = mysql.insertDataset(payload)
                    if mysqlStatus == False:
                        vlog.warn("--> error writing to db")
                        screen.write_error("couldnot write to db")

                    # Wert an MQTT broker senden
                    mc.publish("/energy/current",valCurrent)

                    # draw chart if activated
                    if current.value > 0:
                        energyData.append(current.value)

                    # Ausgabe auf UI ausgeben
                    screen.write_status("Received energy-message from node %s" % oct(header.from_node))
                    data_received = True

                else:
                    vlog.warn("Length of payload (%s) not correct, dataset will be ignored.",len(payload))
                    screen.write_status("Payload size of %s bytes not correct, will be ignored." % len(payload))

            elif chr(header.type) == "M":
                header, payload = network.read(4)
                timestamp = unpack("<L",payload)[0]
                screen.write_status("Received test-message from node %s (Payload %i)" % (str(oct(header.from_node)),timestamp))

            else:
                header, payload = network.read(4)
                vlog.warn("Received unkown message type [%s] from node %s" % (chr(header.type),str(oct(header.from_node))))
                screen.write_error("Bad message type [%s] from node %s" % (chr(header.type),str(oct(header.from_node))))

        if data_received:
            #energyData.append(1000)
            drawGraph(win_chart, energyData, chartmode)
            drawWinData(win_data, current)

        # Updating the screen
        screen.screen.addstr(1,screen.width-18,time.strftime("%x %X"),screen.curses.A_BOLD)
        if globalData.lastError:
            screen.write_error(globalData.lastError)
        screen.screen.refresh()
        #time.sleep(0.5)

def drawWinData(window, current):
    global energyData, globalData

    if window and current:
        window.box()
        window.addstr(1,2,"Current:         Wh  Total:            KWh  SensorTime :")
        window.addstr(3,2,"Lowest :         Wh  at                     Energy Rate:         Ct/KWh")
        window.addstr(4,2,"Highest:         Wh  at                     TotalYear  :         KWh")

        if current.value != 0:
            vlog.debug("Total: %s Current: %s from Client %s at %s" % (current.total,current.value,oct(current.from_node),current.sensorTime))
            window.addstr(1,11,"{:6.2f}".format(current.value),screen.curses.A_BOLD)
            window.addstr(1,30,"{:10.4f}".format(current.total),screen.curses.A_BOLD)
            window.addstr(1,59,str(current.sensorTime),screen.curses.A_BOLD)
            window.addstr(3,61,str(globalData.energyRate),screen.curses.A_BOLD)
            window.addstr(4,59,"{:4.2f}".format(current.totalCurrentYear),screen.curses.A_BOLD)
            window.addstr(5,60,"{:4.2f} EUR".format(current.totalCurrentYear * globalData.energyRate / 100.0),screen.curses.A_BOLD)

            window.addstr(3,11,"{:6.2f}".format(current.lowest),screen.curses.A_BOLD)
            window.addstr(4,11,"{:6.2f}".format(current.highest),screen.curses.A_BOLD)
            window.addstr(3,26,time.strftime("%Y-%m-%d %H:%M",current.lowestTime),screen.curses.A_BOLD)
            window.addstr(4,26,time.strftime("%Y-%m-%d %H:%M",current.highestTime),screen.curses.A_BOLD)

        window.refresh()

def roundSignificant(x, option):
    try:
        if x > 0:
            log10x = log10(abs(x))
            tenth = int(log10x)
            #print('log10x = ',log10x)
            #print('tenth = ',tenth)
            if option=='lowest':
                # berechne die Anzahl der 10er Stellen
                # 
                powerx = pow(10,tenth)
                result = int(x / powerx) * powerx
                if result == 0:
                    screen.close()
                    print(x)
                    print('powerx ',powerx)
                    print('log10x ',log10x)
                    print('tenth ',tenth)
                    exit(0)
                return result
            else:
                floorx = floor(log10x)
                x1 = x + 0.5 * pow(10,tenth)
                roundx = round(x1, -int(floorx))
                return roundx
        else:
            return 0
    except:
        if screen: screen.close()
        print(sys.exc_info()[0])
        print(x)
        exit()

class chartwindata:
    boxx = 0
    boxy = 0
    boxh = 0
    boxw = 0 
    delta = 0
    highest = 0
    lowest = 0
    
def drawGraph(window, energyData, chartmode):

    if window:
        window.clear()
        window.box()
        #window.bkgd('.')

    if energyData and len(energyData) > 1:
        chart = chartwindata()
        chart.boxx = 1
        chart.boxy = 1
        chart.boxh, chart.boxw = window.getmaxyx() 
        chart.boxw = chart.boxw - chart.boxx
        chart.boxh = chart.boxh - chart.boxy
        chart.delta = 0.0
        chart.highest = 0
        chart.lowest  = 1000000

        if chartmode == 'continues':
            if len(energyData) > chart.boxw:
                while len(energyData) > chart.boxw:
                    del energyData[0]
            elif len(energyData) < chart.boxw:
                while len(energyData) < chart.boxw:
                    energyData.insert(0,0)

        # Berechnen der Chartdimensionen
        # Maximalwert
        # Minimalwert
        # Delta
        # Skalierungsfaktor für Charthöhe
        # Skalierungsfaktor für Chartbreite
        z = 0
        z1 = 0
        for value in energyData:
            """
            z = z + 1
            if z > len(energyData)-10:
                # print the last 10 values
                z1 = z1 + 1
                if 4 + z1 < chart.boxh:
                    window.addstr(4+z1,80,str(z) + ": " + str(value))
            """

            if value > 0:
                if chart.highest < value:
                    chart.highest = roundSignificant(value,'highest')
                if chart.lowest > value:
                    chart.lowest = roundSignificant(value,'lowest')
        chart.delta = chart.highest - chart.lowest
        if chart.delta > 0: chart.scaleY = chart.boxh / chart.delta
        chart.scaleX = stepping = chart.boxw / len(energyData)


        """
        window.addstr(16,80,"high  : " + str(chart.highest))
        window.addstr(17,80,"low   : " + str(chart.lowest))
        window.addstr(18,80,"delta : " + str(chart.delta))
        window.addstr(19,80,"scaleX: " + str(chart.scaleX))
        window.addstr(20,80,"scaleY: " + str(chart.scaleY))
        window.addstr(21,80,"len() : " + str(len(energyData)))
        """

        # Draw chart and Legend
        counter = 0
        index = 0
        oindex = -1
        ovalue = 0
        oy = 0

        for rx in range(0,chart.boxw,1):
            index = int(counter / chart.scaleX) - 1
            value = energyData[index]
            x = rx
            y = int(chart.boxh - (value-chart.lowest) * chart.scaleY)
            if y <= chart.boxy:
                y = chart.boxy
            if y >= chart.boxh:
                y = chart.boxh - 1
            if x <= chart.boxx:
                x = chart.boxx
            if x >= chart.boxw:
                x = chart.boxw - 1

            symbol = screen.curses.ACS_DEGREE
            symbol2 = screen.curses.ACS_BULLET
            if oy > 0 and index>0 and ovalue>0:
                #vline(y, x, ch, n)
                try:
                    if oy-y<0:
                        posy = oy
                        n = abs(oy-y)

                    elif oy>0:
                        posy = y
                        n = oy-y

                    window.vline(posy, x, symbol,n)
                    window.addch(posy, x, symbol)
                    n2 = chart.boxh-posy + n - 1
                    window.vline(posy + n + 1, x, symbol2,n2) 

                except:
                    screen.close()
                    print("ERROR2: (y=" + str(posy) + "x=" + str(x)+ ") => n2="+str(n2))

            if index != oindex or oindex == -1:
                oindex = index                    
                ovalue = value
                #window.addstr(chart.boxh-1, x, str(index))
                oy = y

            counter = counter + 1            

    if window:
        window.refresh()        

       
def draw_screen(screen):
    global curses

    if screen.curses.has_colors():
        screen.screen.bkgd(screen.curses.color_pair(screen.colorset))

    screen.screen.box()
    screen.screen.addstr(1,2,"homeServer V0.1 - 2018 - honitos")
    
    # Trennlinie Titelzeile
    #screen.screen.hline(2,1,curses.ACS_HLINE,screen.width - 1)
    #screen.screen.addch(2,0,curses.ACS_LTEE)
    #screen.screen.addch(2,screen.width,curses.ACS_RTEE)
    
    # Trennlinie Statuszeile      
    screen.ystatus = screen.height - 3
    #screen.screen.hline(screen.ystatus - 1,1,curses.ACS_HLINE, screen.width - 1)
    #screen.screen.addch(screen.ystatus - 1,0,curses.ACS_LTEE)
    #screen.screen.addch(screen.ystatus - 1,screen.width,curses.ACS_RTEE)     
    screen.screen.addstr(screen.ystatus - 1,1,"Status:")
    screen.screen.addstr(screen.ystatus - 1,60,"last Error:")
    
    # Trennlinie Optionen
    screen.screen.hline(screen.height - 2,1, screen.curses.ACS_HLINE, screen.width - 1)
    screen.screen.addch(screen.height - 2,0, screen.curses.ACS_LTEE)
    screen.screen.addch(screen.height - 2, screen.width, screen.curses.ACS_RTEE)     
    screen.screen.addstr(screen.height - 1,1,"[q] Quit   [c] Continues Current   [d] Daily Current        [1-9] change Colorset")

    screen.screen.move(screen.ystatus,1)
    screen.screen.refresh()
        

def update_windows():
    global win_chart,screen
    
    if win_chart:
        win_chart.resize(screen.height-6,screen.width+1)
        #drawWinData(win_data,None)
# --------------------------------------------------------------------------------------
# --
# -- main routine
# --
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    mysql = None
    try:
        vlog.info("Program started...")
        screen = intuition()
        draw_screen(screen)

        win_chart = screen.curses.newwin(screen.height-6,screen.width+1,2,0)
        drawGraph(win_chart, None, '')

        win_data = screen.curses.newwin(7,75,4,3)
        drawWinData(win_chart, None)

        screen.write_status("Initiating DB-Connection to (%s)" % secrets['mysql']['host'])
        mysql = sql(vlog, secrets['mysql']['host'],
                          secrets['mysql']['dbname'],
                          secrets['mysql']['username'],
                          secrets['mysql']['password'])
        if mysql:
            screen.write_status("Initiating RF-Network...")
            if rf24_init() == True:
                vlog.info("honitos HomeServer V0.01 started...")

                screen.write_status("Start listing ...")
                screen.screen.nodelay(True)
                # -- here comes the main loop
                rf24_run()

    except:
        e = sys.exc_info()
        vlog.error(e)
        raise

    finally:
        #-- closing connection to db
        if screen: screen.close()

        if mysql:
            vlog.info("Closing database...")
            mysql.close()

        vlog.debug("Program terminated...")


else:
    vlog.error("This program may not be executed as a module.")

exit()

