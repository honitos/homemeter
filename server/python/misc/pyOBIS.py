#! /user/bin/env python


#-- getting some infos for myself
#-- used to hide output via shell when in bg
import os
import subprocess

def check_bg():
	pid = os.getpid()
	if "+" in subprocess.check_output(["ps", "-o", "stat=", "-p", str(pid)]):
		return 0
	else:
		return 1
i_am_in_bg = 0

from datetime import datetime
from time import mktime
import serial
import MySQLdb
db = MySQLdb.connect(host="localhost",db="Energy")
cursor = db.cursor()

false = 0
true = 1
from pySML import *
"""
SML_Message ::= SEQUENCE
{
	transactionId 	Octet String,
	groupNo 	Unsigned8,
	abortOnError 	Unsigned8,
	messageBody 	SML_MessageBody,
	crc16 		Unsigned16,
	endOfSmlMsg 	EndOfSmlMsg
}
"""

SML_Message = {"transactionId","groupNo","abortOnError","messageBody","crc16","endOfSmlMsg"}

def sml_parseMessageBody(raw):
	global sml,sml_msg
	global Entries

	# SML_MessageBody
	# -- 2 Datenfelder:
	# -- 1 . Messagetype
	# -- 2 . Messageinhalt
	
	# ---- Messagetype lesen
	TL = sml_getTL(raw)
	#print "TL:",hex(TL)
	messagetype = sml_getData(raw)
	#print "Message Type ",hex(messagetype),"found: ",

	if messagetype == sml.OpenResponse:
		# ---- Messageinhalt lesen (SML_PublicOpen.Res)
		TL = sml_getTL(raw)
		#print "TL:",hex(TL)
		sml_msg.codepage = sml_getData(raw)
		sml_msg.clientId = sml_getData(raw)  #.. darf weggelassen werden, da der Response ein Broadcast ist
		sml_msg.reqFileId = sml_getData(raw)
		sml_msg.serverId = sml_getData(raw)  #... z.B.  Server-ID: 09-01-45-53-59-11-03-98-4F-4D
		sml_msg.refTime = sml_getData(raw)
		sml_msg.sml_version = sml_getData(raw)
		#print "codepage:",hex(codepage), " - reqFileId:",reqFileId," - serverId",serverId," - sml-version",hex(sml_version)

	elif messagetype == sml.CloseResponse:
		# ---- Messageinhalt lesen (SML_PublicClose.Res)
		TL = sml_getTL(raw)
		globalSignature = sml_getData(raw)
			
	elif messagetype == sml.GetListResponse:
		"""
		clientId 	Octet String OPTIONAL,
		serverId 	Octet String,
		listName 	Octet String OPTIONAL,
		actSensorTime 	SML_Time OPTIONAL,
		valList 	SML_List,
		listSignature 	SML_Signature OPTIONAL,
		actGatewayTime 	SML_Time OPTIONAL
		"""

		# ---- Messageinhalt lesen (SML_PublicOpen.Res)
		TL = sml_getTL(raw)
		sml_msg.clientId = sml_getData(raw)
		sml_msg.serverId = sml_getData(raw)
		sml_msg.listname = sml_getData(raw)
		sml_msg.actSensorTime = sml_getSensorTime(raw)
		#print "Time:",datetime.fromtimestamp(sml_msg.actSensorTime)

		# valList
		TL = sml_getTL(raw) - 0x70
		#print " Listelements:",TL

		Entries = []
		for e in range(0,TL):
			Entry = sml_getListEntry(raw)
			Entries.append(Entry)

		# listSignature
		sml_msg.listSignature = sml_getData(raw)
		sml_msg.actSensortime = sml_getSensorTime(raw)	

	else:
		print "unknown message type: ",	hex(messagetype)
		return 0

	# --- crc
	crc = sml_getData(raw)

	# --- endOfSmlMsg
	endofSmlMsg = sml_getData(raw)

	return messagetype


def sml_parseMessage(raw):
	#-- TL-Feld
	TL = sml_getTL(raw)
	if (TL < 0x60 or TL > 0x7F):
		print "ungueltige Typlaenge ermittelt: ",hex(TL)
		return false

	# SML_Message parsen
	fields = TL-0x70
	#print "TL: ",hex(TL)," - binaer ",bin(TL)," - Felder: ",fields
	transactionId = sml_getData(raw)
	groupNo = sml_getData(raw)
	abortOnError = sml_getData(raw)
	#print "transactionIid:",ByteToHex(transactionId),"groupNo:",hex(groupNo),"abortOnError:", hex(abortOnError)

	return sml_parseMessageBody(raw)




def sml_parse(raw):
	global sml
	global Entries
	global first_run
	global db
	global i_am_in_bg

	# --
	# -- Nach Header Escape Sequnce '1b 1b 1b 1b' suchen
	sml.msg_pointer = 0

	position = sml_checkseq(raw,sml.seq_escape)
	if position == 0:
		print "keine gueltige Nachricht:"
		print ByteToHex(sml_raw)
		return false
	# --
	# -- Nach Beginn der Nachricht '01 01 01 01' suchen
	position = sml_checkseq(raw,sml.seq_begin)
	if position == 0:
		print "Nachrichtenbeginn nicht gefunden:"
		print ByteToHex(sml_raw)
		return false
		

	#-------------------------------------------------------------
	#-- Begin parsing SML_Message
	#-------------------------------------------------------------
	end_of_msg = 0
	while not end_of_msg == 1:
		message = sml_parseMessage(raw)
		if message == sml.CloseResponse:
			end_of_msg = 1

		elif message == sml.GetListResponse:
			if first_run == 1 and i_am_in_bg ==0:
				print "OBIS:  Medium - Kanal : Messgroesse . Messart . Tarifstufe * Vorwert"
				print "ServerID: ",sml_msg.serverId
					
				#--- Ausgabe der Titelzeile
				print "Time                |",
				for entry in Entries:
					obis = sml_OBIS(entry.objName)
					if obis[0:4] == "1-0:":
						print sml_OBIS(entry.objName),"|",
				first_run = 0
				print " "			
			#---
			#print '\r',
			obis_ts = datetime.fromtimestamp(sml_msg.actSensorTime)
			wertStr = ""
			for entry in Entries:
				obis = sml_OBIS(entry.objName)
				if obis[0:4] == "1-0:":
					breite = len(obis)
					wert = entry.value
					if obis == "1-0:96.5.5*255":
						wert = bin(entry.value)
					elif obis == "1-0:1.8.0*255":
						wert = wert / 10000000.0
						obis_total = wert

					elif obis[0:9] == "1-0:1.8.1":
						wert = wert / 100.0
						wert = str(wert)
						obis_tarif1 = wert

					elif obis[0:9] == "1-0:1.8.2": 
						wert = wert / 100.0
						wert = str(wert)
						obis_tarif2 = wert

					elif obis[0:9] == "1-0:1.7.0":
						wert = wert / 100.0
						wert = str(wert)
						obis_leistung = wert
						
					wertStr = wertStr + str(wert).rjust(breite) + "|"

			#----- Ausgabe auf Temrinal
			if i_am_in_bg == 0:
				print obis_ts," |",wertStr

			#----- schreiben in die SQL-Tabelle
			sql_command = "INSERT INTO Easymeter (SensorTime,Total,Leistung,Tagtarif,Spartarif)"
			sql_command = sql_command + " VALUES ('"
			sql_command = sql_command + str(obis_ts) + "','"
			sql_command = sql_command + str(obis_total) + "','" 
			sql_command = sql_command + str(obis_leistung) + "','"
			sql_command = sql_command + str(obis_tarif1) + "','" 
			sql_command = sql_command + str(obis_tarif2) + "')"
			#print sql_command

			cursor = db.cursor()
			cursor.execute(sql_command)
			db.commit()
		elif message == 0:
			print "unknown message, aborting..."
			end_of_msg = 1
	# Rest...
	#print "Rest zu verarbeiten:"
	#print ByteToHex(raw[sml.msg_pointer:])




# ----------------------------------------------------------
# -- Hauptroutine
# ----------------------------------------------------------

ser = serial.Serial(
    	port='/dev/ttyAMA0',
    	baudrate = 9600,
    	parity = serial.PARITY_NONE,
    	stopbits = serial.STOPBITS_ONE,
    	bytesize = serial.EIGHTBITS,
    	timeout = 1
)

counter = 0
a = 0
first_run = 1

while 1:
	try:
		i_am_in_bg = check_bg()

		sml_raw = ser.readline()
		#sml_raw = ser.read(250)
		#serial_data= "1B1B1B1B0101010176051288C06962006200726500000101760101074553595133420B09014553591103984F4D010163C09C0076051288C06A6200620072650000070177010B09014553591103984F4D017262016500BE01AF7677078181C78203FF01010101044553590177070100010800FF0101621E52FC6900000005F19C81F30177070100010801FF0101621E520165000321660177070100010802FF0101621E5201650000C3CE0177070100010700FF0101621B52FE550000D5040177070100600505FF01010101630190010101632CBA0076051288C06B6200620072650000020171016314D500001B1B1B1B1A017A02"
		#sml_raw = HexToByte(serial_data)
		sml.msg_length = len(sml_raw)
		if sml.msg_length > 240:
			#print sml.msg_length, " bytes empfangen: ",
			sml_parse(sml_raw)
		#else:
		#	print sml.msg_length, " bytes empfangen, Datensatz nicht vollaendig: ",ByteToHex(sml_raw)

		a = a + 1

	except OSError as e:
		#print "Fehler beim Lesen, mache trotzdem weiter...."
		pass

