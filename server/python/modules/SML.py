def ByteToHex( byteStr ):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    """

    # Uses list comprehension which is a fractionally faster implementation than
    # the alternative, more readable, implementation below
    #
    #    hex = []
    #    for aChar in byteStr:
    #        hex.append( "%02X " % ord( aChar ) )
    #
    #    return ''.join( hex ).strip()

    return ''.join( [ "%02X" % ord( x ) for x in byteStr ] ).strip()

def HexToByte( hexStr ):
    """
    Convert a string hex byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    """
    # The list comprehension implementation is fractionally slower in this case
    #
    #    hexStr = ''.join( hexStr.split(" ") )
    #    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
    #                                   for i in range(0, len( hexStr ), 2) ] )

    bytes = []

    hexStr = ''.join( hexStr.split(" ") )

    for i in range(0, len(hexStr), 2):
        bytes.append( chr( int (hexStr[i:i+2], 16 ) ) )

    return ''.join( bytes )

def mid(s, offset, amount):
    return s[offset:offset+amount]



class sml:
	OpenRequest = 0x00000100
	OpenResponse = 0x00000101
	CloseResponse = 0x00000201
	GetListRequest = 0x00000700
	GetListResponse = 0x00000701
	
	seq_escape = "1b1b1b1b"
	seq_begin = "01010101"
	Boolean = 0x42
	Integer8 = 0x52
	Integer16 = 0x53
	Integer32 = 0x55
	Integer64 = 0x59
	Unsigned8 = 0x62
	Unsigned16 = 0x63
	Unsigned32 = 0x65
	Unsigned64 = 0x69
	Octet = 3
	msg_pointer = 0
	msg_length = 0
	E3B_init_timestamp = 1441368080

# 1441367238

class sml_msg:
	codepage = 0
	clientId = 0  #.. darf weggelassen werden, da der Response ein Broadcast ist
	reqFileId = 0
	serverId = 0
	refTime = 0
	sml_version = 0
	listSignature = 0
	actSensorTime = 0
	

Entries = []
class ListEntry:
	def __init__(self,objName,status,valTime,unit,scaler,value,valueSignature):
		self.objName = objName
		self.status = status
		self.valTime = valTime
		self.unit = unit
		self.scaler = scaler
		self.value = value
		self.valueSignature = valueSignature




def sml_checkseq(raw, str):
	global sml

	if raw == '':
		return 0
	if str == '':
		return 0

	bytes = len(str) / 2
	sequence = mid(raw,sml.msg_pointer,bytes).lower()

	tempstr = ByteToHex( sequence ).lower()
	if tempstr == str:
		sml.msg_pointer = sml.msg_pointer + bytes
		#print "gefunden, neue position",sml_msg_pointer
		return sml.msg_pointer
	else:
		print "suche nach [",str,"] in [",tempstr,"] nicht erfolgreich"
		return 0


def sml_OBIS(objName):
	# Kennzahl   Medium - Kanal : Messgroesse . Messart . Tarifstufe * Vorwertzaehlerstand
	# Stellen      (1)    (1-2)     (1-2)        (1-2)       (1)            (1-2)

	medium 	= ord(mid(objName,0,1))       	# 1.. Elektrizitaet
	kanal 	= ord(mid(objName,1,1))		# 0..64
	messgroesse = ord(mid(objName,2,1))	# 1.. Summe Wirkleistung+, 3.. Summe Blindleistung
	messart = ord(mid(objName,3,1))		# 6.. Maximum, 8.. Zeitintegral1, 9..Zeitintegral2, 29.. Zeitintegral5
	tarifstufe = ord(mid(objName,4,1))	# 0.. Total, 1..9 Tagrif 1-0
	vorwert = ord(mid(objName,5,1))		#
		
	return str(medium) + chr(0x2D) + str(kanal) + chr(0x3A) + str(messgroesse) + chr(0x2E) + str(messart) + chr(0x2E) + str(tarifstufe) + chr(0x2A) + str(vorwert)	

def sml_Status(status):
	"""
	Bit[7] . MSB, 0=Leerlauf, 1=oberhalb Anlauf
	Bit[6] . beim Phasenausfall L1 wird gesetzt
	Bit[5] . beim Phasenausfall L2 wird gesetzt
	Bit[4] . beim Phasenausfall L3 wird gesetzt
	Bit[3] . reserviert, immer 0
	Bit[2] . Manipulationserkennung, wird auf .1. gesetzt, falls ein DC-Magnetfeld erkannt wird. Ruecksetzen bei Spannungswiederkehr oder 24h nach Unterschreiten der Grenze des Magnetfeldes. Bei Q3Dx-Reihe ist immer .0..
	Bit[1] . .0. das Telegramm wird immer asynchron im festen Zeitraster ausgegeben
	Bit[0] . .0. kein Fehler, .1. . Fehler
	"""


def sml_getTL(raw):
	global sml
	TL = ord(raw[sml.msg_pointer:sml.msg_pointer+1])
	sml.msg_pointer += 1
	return TL

def sml_getSensorTime(raw):
	global sml
	global sml_raw

	TL = sml_getTL(raw)
	if TL == 0x01:
		return

	timeformat = sml_getData(raw)
	if timeformat == 0x01:
		dt = sml_getData(raw) + sml.E3B_init_timestamp
		#today = datetime.now()
		#sec_since_epoch = mktime(today.timetuple()) + today.microsecond/1000000.0
		return dt
	else:
		print "unknown timeformat"



#-- parse message for a standard SML_ListEntry
"""
objName Octet String,
status 	SML_Status OPTIONAL,
valTime SML_Time OPTIONAL,
unit 	SML_Unit OPTIONAL,
scaler 	Integer8 OPTIONAL,
value 	SML_Value,
valueSignature SML_Signature OPTIONAL
"""

def sml_getListEntry(raw):
	global sml

	TL = sml_getTL(raw)
	#print "Valueentries:",hex(TL)
	objName = sml_getData(raw)
	status = sml_getData(raw)
	valTime = sml_getData(raw)
	unit = sml_getData(raw)
	scaler = sml_getData(raw)
	value = sml_getData(raw)
	valueSignature = sml_getData(raw) 			
	Entry = ListEntry(objName,status,valTime,unit,scaler,value,valueSignature)
	return Entry


def sml_getData(raw):
	global sml
	datatype = ord(raw[sml.msg_pointer])
	sml.msg_pointer += 1

	if datatype == sml.Boolean:
		data = ord(raw[sml.msg_pointer])
		sml.msg_pointer += 1
		return data

	if datatype == sml.Integer8:				
		data = ord(raw[sml.msg_pointer])
		sml.msg_pointer += 1
		return data

	if datatype == sml.Integer16:				
		byte1 = ord(raw[sml.msg_pointer])
		byte2 = ord(raw[sml.msg_pointer+1])
		data = (byte1 << 8) + byte2
		sml.msg_pointer += 2
		return data

	elif datatype == sml.Integer32:
		byte1 = ord(raw[sml.msg_pointer])
		byte2 = ord(raw[sml.msg_pointer+1])
		byte3 = ord(raw[sml.msg_pointer+2])
		byte4 = ord(raw[sml.msg_pointer+3])
		data = (byte1 << 24) + (byte2 << 16) + (byte3 << 8) + byte4
		sml.msg_pointer += 4
		return data

	if datatype == sml.Unsigned8:				
		data = ord(raw[sml.msg_pointer])
		sml.msg_pointer += 1
		return data

	elif datatype == sml.Unsigned16:
		byte1 = ord(raw[sml.msg_pointer])
		byte2 = ord(raw[sml.msg_pointer+1])
		data = (byte1 << 8) + byte2
		sml.msg_pointer += 2
		return data

	elif datatype == sml.Unsigned32:
		byte1 = ord(raw[sml.msg_pointer])
		byte2 = ord(raw[sml.msg_pointer+1])
		byte3 = ord(raw[sml.msg_pointer+2])
		byte4 = ord(raw[sml.msg_pointer+3])
		data = (byte1 << 24) + (byte2 << 16) + (byte3 << 8) + byte4
		sml.msg_pointer += 4
		return data

	elif datatype == sml.Unsigned64:
		byte1 = ord(raw[sml.msg_pointer])
		byte2 = ord(raw[sml.msg_pointer+1])
		byte3 = ord(raw[sml.msg_pointer+2])
		byte4 = ord(raw[sml.msg_pointer+3])
		byte5 = ord(raw[sml.msg_pointer+4])
		byte6 = ord(raw[sml.msg_pointer+5])
		byte7 = ord(raw[sml.msg_pointer+6])
		byte8 = ord(raw[sml.msg_pointer+7])

		data = (byte1 << 56) + (byte2 << 48) + (byte3 << 40) + (byte4 << 32) + (byte5 << 24) + (byte6 << 16) + (byte7 << 8) + byte8
		sml.msg_pointer += 8
		return data

	elif datatype == 0x01:
		# OPTIONAL, der Parameter wurde nicht bereitgestellt
		data = 0
		#sml.msg_pointer += 1
		return data

	elif datatype == 0x00:
		# EndOfMessage ist "00"
		return 0

	elif datatype < 0x50:		
		os_len = datatype - 1
		data = raw[sml.msg_pointer:sml.msg_pointer+os_len]
		sml.msg_pointer += os_len
		return data

	else:
		print "unknown datatype:",hex(datatype)
