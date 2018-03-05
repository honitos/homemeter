#include "stdint.h"
#include "stdio.h"
#include "ctype.h"
#include "string.h"

#define IGNORE_OCTETS 0
/*
    Functions for working with SML-Messages
*/

/* Encodes string to hexadecimal string reprsentation
    Allocates a new memory for supplied lpszOut that needs to be deleted after use
    Fills the supplied lpszOut with hexadecimal representation of the input
*/
void ByteToHex(uint8_t *szInput, size_t size_szInput, char **lpszOut)
{
  uint8_t *pin = szInput;
  const char *hex = "0123456789ABCDEF";
  size_t outSize = size_szInput * 2 + 2;
  *lpszOut = new char[outSize];
  char *pout = *lpszOut;
  for (; pin < szInput + size_szInput; pout += 2, pin++)
  {
    pout[0] = hex[(*pin >> 4) & 0xF];
    pout[1] = hex[*pin & 0xF];
  }
  pout[0] = 0;
}

void HexToByte(const char* input, uint8_t output[]) {
  uint16_t i;
  uint16_t str_len = strlen(input);
  for (i = 0; i < (str_len / 2); i++) {
    sscanf(input + 2 * i, "%02x", &output[i]);
  }
}

void printHex(uint8_t* input, uint8_t length) {
  uint8_t i;
  Serial.print(length);
  Serial.print(" : ");
  for (i = 0; i < length; i++) {
    if (input[i] < 0x10)  Serial.print("0");
    Serial.print(input[i], HEX);
  }
  Serial.print("\n");
}

void printHexChar(char* input, uint8_t length) {
  uint8_t i;
  Serial.print(length);
  Serial.print(" : ");
  for (i = 0; i < length; i++) {
    if ((uint8_t)input[i] < 0x10)  Serial.print("0");
    Serial.print((uint8_t)input[i], HEX);
  }
  Serial.print("\n");
}


void str_midlower(char* input, char start, char length, char* output) {

  uint8_t inputlen = strlen(input);
  //Serial.print("\nLänge Input %d\n",inputlen);
  if (inputlen == 0) return;
  if (start < 0) return;
  if (start > inputlen) return;

  //Serial.print("\nStart Input %d:%c\n",start-1,input[start-1]);
  //Serial.print("1. Länge %d\n",length);
  if (start - 1 + length > inputlen) length = inputlen - start;
  //Serial.print("2. Länge %d\n",length);
  uint8_t a = 0;
  for (a = 0; a < length; a++) {
    output[a] = tolower(input[start - 1 + a]);
    //Serial.print(">>%d,%c\n",a,output[a]);
  }
  output[length] = 0;
}


void str_tolower(char* input) {

  uint8_t inputlen = strlen(input);
  if (inputlen == 0) return;

  uint8_t a = 0;
  for (a = 0; a < inputlen; a++) {
    input[a] = tolower(input[a]);
  }
}

void streamBytes(uint8_t *streamdata,uint32_t &position, uint32_t data, uint8_t bytes)
{
	uint8_t i;
	//Serial.print(">>");
	for(i=0;i<bytes;i++){		
		*(streamdata + position) = (uint8_t) (data >> (8*(3-i)));
		//Serial.print(  (uint8_t) (data >> (8*(3-i)))  );
		//Serial.print(",");
		position += 1;
	}
}

void  streamChar(uint8_t *streamdata,uint32_t &position, char* data, uint8_t bytes)
{
	uint8_t i;
	for(i=0;i<bytes;i++){		
		*(streamdata + position) = (uint8_t) data[i];
		position += 1;
	}	
}


class sml_ListEntry
{
  public:
	uint8_t objLength;
    char* objName;
    uint8_t status;
    uint32_t valTime;
    uint8_t unit;
    char scaler;

    uint32_t value;

    char* valueSignature;

    void getOBIS(char* output) {

      // Kennzahl   Medium - Kanal : Messgroesse . Messart . Tarifstufe * Vorwertzaehlerstand
      // Stellen      (1)    (1-2)     (1-2)        (1-2)       (1)            (1-2)
/*
      uint8_t medium  =  objName;         // 1.. Elektrizitaet      
      uint8_t kanal   =  objName+1;       // 0..64
      uint8_t messgroesse = objName+2;   // 1.. Summe Wirkleistung+, 3.. Summe Blindleistung
      uint8_t messart = objName+3  ;   // 6.. Maximum, 8.. Zeitintegral1, 9..Zeitintegral2, 29.. Zeitintegral5
      uint8_t tarifstufe = objName+4 ; // 0.. Total, 1..9 Tagrif 1-0
      uint8_t vorwert = objName+5  ; 
*/
      //return str(medium) + chr(0x2D) + str(kanal) + chr(0x3A) + str(messgroesse) + chr(0x2E) + str(messart) + chr(0x2E) + str(tarifstufe) + chr(0x2A) + str(vorwert)

    }

};


class sml_message
{
  public:
	uint32_t msgtype;
    uint8_t codepage;
    char* clientId;       //.. darf weggelassen werden, da der Response ein Broadcast ist
    char* reqFileId;
    char* serverId;
    char* listname;
	uint8_t NumEntries;
	sml_ListEntry Entries[6];
    uint32_t refTime;
    uint8_t sml_version;
    char*  listSignature;
    uint32_t actSensorTime;
    uint8_t crc;
};


class sml
{
  protected:
    static const char*    seq_escape;
    static const char*    seq_begin;
    static const uint32_t OpenRequest     = 0x00000100;
    static const uint32_t OpenResponse    = 0x00000101;
    static const uint32_t CloseResponse   = 0x00000201;
    static const uint32_t GetListRequest  = 0x00000700;
    static const uint32_t GetListResponse   = 0x00000701;
    static const uint8_t  Boolean     = 0x42;
    static const uint8_t  Integer8    = 0x52;
    static const uint8_t  Integer16     = 0x53;
    static const uint8_t  Integer32     = 0x55;
    static const uint8_t  Integer64     = 0x59;
    static const uint8_t  Unsigned8     = 0x62;
    static const uint8_t  Unsigned16  = 0x63;
    static const uint8_t  Unsigned32  = 0x65;
    static const uint8_t  Unsigned64  = 0x69;
    static const uint8_t  Octet       = 3;
    static const uint32_t   E3B_init_timestamp = 1441368080;


  private:
    char* globalSignature;

    uint8_t checkseq(const char* str_check)
    {
      uint8_t bytes = strlen(str_check);
      if (bytes == 0) return 0;

      //Serial.print("checkin for : %s, len: %d\n",str_check,bytes);

      char *sequence = NULL;
      ByteToHex(this->rawdata + this->message_pointer, bytes / 2, &sequence);

      //Serial.print("hexstring: %s, len: %d\n",sequence,strlen(sequence));

      str_tolower(sequence);

      //Serial.print("lower: %s, len: %d\n",sequence,strlen(sequence));

      if (strcmp(sequence, str_check) == 0) {
        this->message_pointer += bytes / 2;
        delete[] sequence;
        return message_pointer;
      }
      else {
        // erwartetes Teilstueck im Strom nicht gefunden
        delete[] sequence;
        return 0;
      }
    }


    void getListEntry(sml_ListEntry &Entry)
    {
      uint8_t tmp_TL = getTL() - 0x70;
      //Serial.print("Valueentries: ");
      //Serial.println(TL, HEX);
      //printHex(this->rawdata + this->message_pointer, 32);
	
      Entry.objLength = this->getOctet(&Entry.objName);
      Entry.status = getData();
      Entry.valTime = getData();
      Entry.unit = getData();
      Entry.scaler = getData();
      Entry.value = getData();
      if (this->getOctet(&Entry.valueSignature)>0)
	  {
		  delete Entry.valueSignature;
	  }
    }


    uint8_t getTL()
    {
      return this->rawdata[this->message_pointer++];
    }


    uint32_t getSensorTime()
    {
      uint8_t TL = this->getTL();
      if (TL == 0x01) return 0;

      uint8_t timeformat = this->getData();
      if (timeformat == 0x01) {
        uint32_t dt = this->getData() + this->E3B_init_timestamp;
        //today = datetime.now()
        //sec_since_epoch = mktime(today.timetuple()) + today.microsecond/1000000.0
        return dt;
      }
      else
        Serial.print( "unknown timeformat");
      return 0;
    }

    uint8_t getOctet(char** str_data)
    {
      uint8_t datatype = this->getTL(); //this->rawdata[this->message_pointer];
      //this->message_pointer += 1;
      if (datatype < 0x50)
      {
        uint8_t os_len = datatype - 1;  //einen weniger, in der laenge zaehlt das laengebyte mit!
        if (os_len < 1) return 0;

		//Serial.print("octet length: 0x");
		//Serial.println(os_len,HEX);
		
		if (IGNORE_OCTETS == 1){
			Serial.println("ignoring all Octets.");
			this->message_pointer += os_len;
			return 0;
		}
	
        //Serial.print("Octetlaenge ");
        //Serial.print(os_len);
        //Serial.print(" : ");

        *str_data = new char[os_len];
        char *pout = *str_data;

        uint8_t i;
        for (i = 0; i < os_len; i++) {
          pout[i] = this->rawdata[message_pointer];
          //Serial.print((uint8_t) this->rawdata[this->message_pointer], HEX);
          //Serial.print(":");
          this->message_pointer += 1;
        }
        pout[os_len] = 0;
        //Serial.print("  >>> ");
        //Serial.println(pout);
		return os_len;
      }
      else {
        Serial.print("unknown datatye in getOctet: 0x");
		Serial.println(datatype,HEX);
		return 0;
      }
    }

    uint32_t getData()
    {
      uint32_t data;
      uint8_t datatype = this->rawdata[this->message_pointer];
      this->message_pointer += 1;

      if (datatype == this->Boolean)
      {
        data = this->rawdata[this->message_pointer];
        this->message_pointer += 1;
        return data;
      }
      else if (datatype == this->Integer8) {
        data = this->rawdata[this->message_pointer];
        this->message_pointer += 1;
        return data;
      }

      else if (datatype == this->Integer16)
      {
        uint8_t byte1 = this->rawdata[this->message_pointer];
        uint8_t byte2 = this->rawdata[this->message_pointer + 1];
        data = (byte1 << 8) + byte2;
        this->message_pointer += 2;
        return data;
      }

      else if (datatype == this->Integer32)
      {
        uint8_t counter = 4;
        uint8_t i;
        for (i = 0; i < counter; i++) {
          uint8_t byte1 = this->rawdata[this->message_pointer + i];
          data = (data << 8) + byte1;
        }
        this->message_pointer += counter;
        return data;
      }

      else if (datatype == this->Unsigned8)
      {
        data = this->rawdata[this->message_pointer];
        this->message_pointer += 1;
        return data;
      }

      else if (datatype == this->Unsigned16)
      {
        uint8_t counter = 2;
        uint8_t i;
        for (i = 0; i < counter; i++) {
          uint8_t byte1 = this->rawdata[this->message_pointer + i];
          data = (data << 8) + byte1;
        }
        this->message_pointer += counter;
        return data;
      }

      else if (datatype == this->Unsigned32)
      {
        uint8_t counter = 4;
        uint8_t i;
        for (i = 0; i < counter; i++) {
          uint8_t byte1 = this->rawdata[this->message_pointer + i];
          data = (data << 8) + byte1;
        }
        this->message_pointer += counter;
        return data;
      }

      else if (datatype == this->Unsigned64)
      {
		uint8_t i;
        uint8_t counter = 8;
		uint64_t data64;

		/*
        Serial.print("warning:not supported: Unsigned64, casting to Unsigned32: ");
		for (i=0;i<8;i++){
          uint8_t byte1 = this->rawdata[this->message_pointer + i];
		  if (byte1<0x10) Serial.print("0");
		  Serial.print(byte1,HEX);
		  Serial.print(":");
		}
		*/
		
        for (i = 0; i < counter; i++) {
          uint8_t byte1 = this->rawdata[this->message_pointer + i];
          data64 = (data64 << 8) + byte1;
        }
		Serial.println("");
		data = (uint32_t) (data64 / 1000);
        this->message_pointer += counter;
        return data;
      }

      else if (datatype == 0x01)
      {
        // OPTIONAL, der Parameter wurde nicht bereitgestellt
        data = 0;
        //message_pointer += 1
        return data;
      }

      else if (datatype == 0x00)
      {
        // EndOfMessage ist "00"
        return 0;
      }

      else if (datatype < 0x50)
      {
        uint8_t octet_len = datatype - 1;
        //Serial.print("ich soll einen String zurüchgeben mit zeichen: ");
        //Serial.println(octet_len);
        if (octet_len > 4) {
          Serial.println("Mehr als 4 Bytes sind als Rueckgabe fuer Octet leider nicht moeglich.");
          this->message_pointer += octet_len;
          return 0;
        }
        uint8_t i;
        for (i = 0; i < octet_len; i++) {
          uint8_t byte1 = this->rawdata[this->message_pointer + i];
          data = data << 8 + byte1;
        }
        this-> message_pointer += octet_len;
        return data;
      }

      else {
        Serial.print("unknown datatype: ");
        Serial.println(datatype);
      }
    }

    void parseMessageBody(sml_message &msg)
    {		
      // SML_MessageBody
      // -- 2 Datenfelder:
      // -- 1 . Messagetype
      // -- 2 . Messageinhalt

	  //printHex(this->rawdata+this->message_pointer,54);
 	  
		//Serial.println("Parsemessagebody.");
      // ---- Messagetype lesen
      uint8_t TL = getTL();
      //Serial.print("TL: ");
      //Serial.println(TL, HEX);

      long messagetype = getData();
      //Serial.print("Message Type found:");
      //Serial.println(messagetype, HEX);
      if (messagetype == this->OpenResponse)
      {
		//Serial.println("Open Response gefunden.");
        // ---- Messageinhalt lesen (SML_PublicOpen.Res)
        TL = getTL();

        //print "TL:",hex(TL)
        msg.codepage = this->getData();
        if (this->getOctet(&msg.clientId)>0)  //.. darf weggelassen werden, da der Response ein Broadcast ist
        {
			delete msg.clientId;
		}
		if (this->getOctet(&msg.reqFileId)>0)
		{
			delete msg.reqFileId;
		}
        if (this->getOctet(&msg.serverId)>0)  //... z.B.  Server-ID: 09-01-45-53-59-11-03-98-4F-4D
		{
		  delete msg.serverId;
		}
        
		msg.refTime = this->getSensorTime();
        msg.sml_version = this->getData();

        //Serial.print("codepage: ");
        //Serial.print(msg.codepage);
        //Serial.print(" - reqFileId: ");
        //Serial.print(msg.reqFileId);
        //Serial.print(" - serverID: ");
        //Serial.println(msg.serverId);
      }
      else if (messagetype == this->CloseResponse)
      {
		//Serial.println("Close Response gefunden.");
        // ---- Messageinhalt lesen (SML_PublicClose.Res)
        TL = this->getTL();
        if (this->getOctet(&this->globalSignature)>0)
		{
			delete this->globalSignature;
		}	
      }

      else if (messagetype == this->GetListResponse)
	  {		  
		  /*
          clientId  Octet String OPTIONAL,
          serverId  Octet String,
          listName  Octet String OPTIONAL,
          actSensorTime   SML_Time OPTIONAL,

          valList   SML_List,

          listSignature   SML_Signature OPTIONAL,
          actGatewayTime  SML_Time OPTIONAL
        */
		//Serial.println("GetListRequestResponse gefunden.");
		//Serial.print("Memfree=");
		//Serial.println(freeMemory());  
		
		//printHex(this->rawdata+this->message_pointer,32);

        // ---- Messageinhalt lesen (SML_PublicOpen.Res)
        TL = this->getTL();
		
        if (this->getOctet(&msg.clientId)>0)  //.. darf weggelassen werden, da der Response ein Broadcast ist
		{
			delete msg.clientId;
		}
        if (this->getOctet(&msg.serverId)>0)
		{
			delete msg.serverId;
		}
        if (this->getOctet(&msg.listname)>0)
		{
			delete msg.listname;
		}

        msg.actSensorTime = this->getSensorTime();
		
        // valList
        TL = this->getTL() - 0x70;
        //Serial.print("Listelements: ");
        //Serial.println(TL);
	
        //sml_ListEntry Entry[TL-1];
		msg.NumEntries = TL;
		//msg.entries = new sml_ListEntry *[TL-1];
				
        uint8_t e = 0;
        for (e = 0; e < TL; e++)
        {
		  //printHex(this->rawdata+ message_pointer,32);
		  //return 0;
		  //Entry[e] = new sml_ListEntry();
		  //msg.entries[e] = new sml_ListEntry;
          getListEntry(msg.Entries[e]);
		  //sml_ListEntry tmpEntry;
		  //getListEntry(&tmpEntry);
		  /*
		  uint8_t tmpTL = getTL() - 0x70;
		  uint32_t tmp1 =0;
		  char* tmp2;
		  tmp1 = this->getOctet(&tmp2);
		  tmp1 = getData();
		  tmp1 = getData();
		  tmp1 = getData();
		  tmp1 = getData();
		  tmp1 = getData();
		  tmp1 = this->getOctet(&tmp2);
		  */
        }
		   
		//Serial.print("Memfree1=");
		//Serial.println(freeMemory());   
  
		
        // listSignature
        if (this->getOctet(&msg.listSignature)>0)
		{
			delete msg.listSignature;
		}

		uint32_t tmpTime = this->getSensorTime();
		if (tmpTime > 0) msg.actSensorTime = tmpTime;
		//Serial.println(msg.actSensorTime);
		//Serial.print("Memfree=");
		//Serial.println(freeMemory());  
	  }

      else {
        Serial.print("unknown message type:");
        Serial.println(messagetype, HEX);
        return;
      }

      // --- crc
      msg.crc = this->getData();

      // --- endOfSmlMsg
      this->end_of_msg = this->getData();
	  msg.msgtype = messagetype;
      return;
    }

    void parseMessage(sml_message &msg)
    {
	  // -- TL-Feld
      uint8_t TL = this->getTL();
      if (TL < 0x60 or TL > 0x7F) {
        Serial.print("ungueltige Typlaenge ermittelt: ");
        Serial.println(TL, HEX);
        return;
      }

      // SML_Message parsen
      uint8_t fields = TL - 0x70;
      //Serial.print("TL: ");
      //Serial.print(TL);
      //Serial.print(" Fields: ");
      //Serial.println(fields);

      char* transactionId = NULL;
      if(this->getOctet(&transactionId)>0)
	  {
		delete transactionId;
	  }
		
      uint8_t groupNo = this->getData();
      uint8_t abortOnError = this->getData();

	  this->parseMessageBody(msg);
      return;
	  }


  public:
    uint8_t message_pointer;
    uint8_t end_of_msg;

    uint8_t* rawdata;
    uint8_t rawlength;

    /*
       Diese Routine wird nun benötigt, wenn die Eingangsdaten als HexStrom vorliegen und erst in Byte-Daten umgewandelt werden sollen
    */
    bool initdata(const char* input)
    {
      this->rawlength = strlen(input) / 2;
      this->rawdata = new uint8_t[this->rawlength];

      HexToByte(input, this->rawdata);

    }

    bool parse(uint8_t *streamdata)
    {
      
	  if (this->rawlength<200) 
	  {
		Serial.println("Nachricht zu kurz, wird nicht verwendet.");
		return 0;
	  }
		//Serial.println("Parse Nachricht."); 
	  // --
      // -- Nach Header Escape Sequnce '1b 1b 1b 1b' suchen
      this->message_pointer = 0;
      this->end_of_msg = 0;

      uint8_t position = 0;

      position = this->checkseq(this->seq_escape);
      if (position == 0) {
        Serial.print("keine gueltige Nachricht:\n");
        printHex(this->rawdata, this->rawlength);
        return 0;
      } else {
        //Serial.println("Escape gefunden.");
      }

      // --
      // -- Nach Beginn der Nachricht '01 01 01 01' suchen
      position = this->checkseq(this->seq_begin);
      if (position == 0) {
        Serial.print("Nachrichtenbeginn nicht gefunden:\n");
        //Serial.println(this->rawdata);
        return 0;
      } else {
        //Serial.print("Beginn gefunden.");
      }

      /*-------------------------------------------------------------
         -- Begin parsing SML_Message
         -------------------------------------------------------------
      */
      while (this->end_of_msg != 1) {
		//Serial.println("parseMessage:");
        sml_message msg;
	
		this->parseMessage(msg);
		if (msg.msgtype == this->OpenResponse)
		{
          //Serial.println("OpenResponse processed\n");			
		}
        else if (msg.msgtype == this->CloseResponse)
        {
          //Serial.println("CloseMessage processed\n");
          this->end_of_msg = 1;
        }
        else if (msg.msgtype == this->GetListResponse)
        {
		  //Serial.println("GetListResponse processed\n");
		  uint8_t i,j;
		  uint32_t stream_pointer = 0;
		  
		  streamBytes(streamdata,stream_pointer,msg.actSensorTime,4);
					  
		  // Print Information of received data...
		  Serial.print("SensorTime: ");
		  Serial.println(msg.actSensorTime);
	      for(j=0;j < msg.NumEntries;j++)
		  {
			  for (i = 0; i < 6; i++) 
			  {
				Serial.print((uint8_t) msg.Entries[j].objName[i]);
				Serial.print(":");
			  }
			  Serial.print(", Status: ");
			  Serial.print(msg.Entries[j].status);
			  Serial.print(", valTime: ");
			  Serial.print(msg.Entries[j].valTime);
			  Serial.print(", unit: ");
			  Serial.print(msg.Entries[j].unit);
			  Serial.print(", value: ");
			  Serial.println(msg.Entries[j].value);

			  streamChar(streamdata,stream_pointer,msg.Entries[j].objName,6);
			  streamBytes(streamdata,stream_pointer,msg.Entries[j].status,4);
			  streamBytes(streamdata,stream_pointer,msg.Entries[j].valTime,4);
			  streamBytes(streamdata,stream_pointer,msg.Entries[j].unit,4);
			  streamBytes(streamdata,stream_pointer,msg.Entries[j].value,4);
			  		  
			  if (msg.Entries[j].objLength > 0) {
				delete msg.Entries[j].objName;
				msg.Entries[j].objLength = 0;
			  }			  
		  }
		  Serial.print(", codierte bytes: ");
		  Serial.println(stream_pointer);
        }
        else
        {
          Serial.print("unknown message <");
		  Serial.print(msg.msgtype);
		  Serial.println(">, aborting...\n");
          this->end_of_msg = 1;
		  
        }
        // exit in development
        //this->end_of_msg = 1;
		//delete msg;
      }
    }
};


const char* sml::seq_escape = "1b1b1b1b";
const char* sml::seq_begin = "01010101";

