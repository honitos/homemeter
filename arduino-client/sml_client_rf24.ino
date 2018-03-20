// -- global settings
#define _debugmode
#define use_WLAN  1   // switch to enable or disable sending (for debugging purposes)
#define ledPin    13  // if we want to use the LED on arduino to signal something
#define dataPin   2   // the PIN used for SoftwareSerial
byte ledState;

// -- variables to evaluate uptime
unsigned long current_millis_value = 0;
unsigned long previous_millis_value = 0;
unsigned long diff_millis_value = 0;
unsigned long seconds = 0;
unsigned long minutes = 0;
unsigned long hours = 0;

// ---------------------------------------------------------
// includes used in this project
// ---------------------------------------------------------
#include <printf.h>
#include <MemoryFree.h>

// -- routines for processing the datastream coming from smartmeter
#include <SML.h>
sml mysml;

// -- routines to read serial datastream via photoled from smartmeter
#include <SoftwareSerial.h>
SoftwareSerial mySerial(2, 11,false);
const unsigned int MAXBUF = 255;
unsigned short bufCnt = 0;
const unsigned long eotTimeoutMs = 500;    // if no char received for 500 ms, declare end of transmission

// -- routines for sending processed data via RF24 to server
#include "RF24.h"
#include "RF24Network.h"
#include "RF24Mesh.h"
#include <SPI.h>
#include <EEPROM.h>
RF24 radio(6,7);   // the used pins on the Nano!
RF24Network network(radio);
RF24Mesh mesh(radio, network);
// -- the nodeID for this client will be 1
#define nodeID 1

struct payload_t {
  unsigned long ms;
  unsigned long counter;
};

/* -- only used for debugging on terminal
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
*/

// -- the setup function runs once when you press reset or power the board
void setup() {
  mysml.rawdata = new uint8_t[MAXBUF];

  // -- set pin modes
  pinMode(ledPin, OUTPUT);
  pinMode(dataPin, INPUT);
  
  // -- open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // -- set the data rate for the SoftwareSerial port
  mySerial.begin(9600);

  // -----------------------------------------------
  // -- settings for the radio-Module
  if(use_WLAN) 
  {
    //digitalWrite(ledPin, HIGH);
    Serial.println(F("Initiating RF24-network ..."));
    printf_begin();
    
    mesh.setNodeID(nodeID);
    
    // -- Connect to the mesh
    Serial.println(F("Establishing connecting to network ..."));
    // PA: RF24_PA_MIN = 0,RF24_PA_LOW, RF24_PA_HIGH, RF24_PA_MAX
    // Datarate: RF24_1MBPS = 0, RF24_2MBPS, RF24_250KBPS
    // CRC: RF24_CRC_DISABLED = 0, RF24_CRC_8, RF24_CRC_16
    // Channel: MESH_DEFAULT_CHANNEL
    // timeout: MESH_RENEWAL_TIMEOUT
    if (mesh.begin(MESH_DEFAULT_CHANNEL,RF24_1MBPS,MESH_RENEWAL_TIMEOUT)) {
      //radio.setPALevel(RF24_PA_HIGH);      
      //radio.setCRCLength(RF24_CRC_8);
      //radio.setRetries(5,15);
      radio.printDetails();     // Dump the configuration of the rf unit for debugging
      Serial.println(F("Mesh successfully initiated ..."));
      
      if (mesh.checkConnection()) {
        //digitalWrite(ledPin, LOW);
        Serial.println(F("Connection established ..."));
      } else {
        Serial.println(F("noe connection established so far ..."));
      };
    } else {
      Serial.println(F("Somehow that did not work, renewing network-address ..."));
      if (mesh.renewAddress()!=0) {
        Serial.println(F("success"));
      } else {
        Serial.println(F("fail"));
      };
    };    
  };
  
  Serial.println(F("Start optical reading from smartmeter ..."));
}

// -- the loop function runs over and over again forever
void loop() 
{
  current_millis_value = millis(); 
  diff_millis_value += current_millis_value - previous_millis_value; // should work even when millis rolls over 
  seconds += diff_millis_value / 1000; 
  diff_millis_value = diff_millis_value % 1000; 
  minutes += seconds / 60; 
  seconds = seconds % 60; 
  hours += minutes / 60; 
  minutes = minutes % 60; 
  previous_millis_value = current_millis_value;
  
  if (use_WLAN) mesh.update();
        
  // --------------------------------------------------------------------------------------------------
  // example of datastream:
  // just to show the string representation, normally the data is already a bytestream!
  //
  // static const char* serial_data = "1B1B1B1B0101010176051288C06962006200726500000101760101074553595133420B09014553591103984F4D010163C09C0076051288C06A6200620072650000070177010B09014553591103984F4D017262016500BE01AF7677078181C78203FF01010101044553590177070100010800FF0101621E52FC6900000005F19C81F30177070100010801FF0101621E520165000321660177070100010802FF0101621E5201650000C3CE0177070100010700FF0101621B52FE550000D5040177070100600505FF01010101630190010101632CBA0076051288C06B6200620072650000020171016314D500001B1B1B1B1A017A02\n";
  // mysml.initdata(serial_data);
  // mysml.parse();
  // --------------------------------------------------------------------------------------------------

  unsigned long lastCharTime = 0;
  
  // -- enter "receiving" state if something is waiting to be read()  
  // -- if there is data received from the photodiode, the data will be read
  // -- and passed by the sml-method parse()
  if (mySerial.available() > 0) {            
    // -- read first char
    mysml.rawdata[bufCnt++] = (uint8_t) mySerial.read();    
    
    // -- timer start
    lastCharTime = millis();             
    
    // -- read whole message from smartmeter
    while ((mySerial.available() > 0) || (millis() - lastCharTime < eotTimeoutMs) && (bufCnt < MAXBUF - 1)) {
      if (mySerial.available() > 0) {
        mysml.rawdata[bufCnt++] = mySerial.read();
        // timer restart
        lastCharTime = millis();             
      }
    }
    // -- "close" buffer
    mysml.rawdata[bufCnt] = 0;
    mysml.rawlength = bufCnt;

    // --
    // -- processing received SML-data
    // --
    sml_dataset_t payload;
    
    // -- parse-method returns 0 on success
    switch(mysml.parse(&payload))
    {
      case 4:
        Serial.println("Error 4 with data stream.");
        break;
        
      case 3:
        Serial.println("Error 3 with data stream.");
        break;
        
      case 2:
        Serial.println("Error 2 with data stream.");
        break;
        
      case 1:
        Serial.println("Error 1 with data stream.");
        break;
        
      case 0:
        Serial.print(F("SensorTime: "));
        Serial.print(payload.actSensorTime);
        Serial.print(F(" - Current: "));
        Serial.print(payload.valCurrent);
        Serial.print(F("Wh - energy value: "));
        Serial.print(payload.valTotal);
        //Serial.print(F("kWh - Tarif1: ")); 
        //Serial.print(payload.valTarif1);
        //Serial.print(F"kWh - Tarif2: "));
        //Serial.println(payload.valTarif2);
        
      if(use_WLAN)
      {
        // -- send all the data to server
        Serial.print(F(" - sending data via RF24 ... "));
               
        // -- messagetype:
        // -- E ... Electricity
        // -- G ... Gas
        // -- W ... Water
        if (!mesh.write(&payload, 'E', sizeof(payload))) {
          // -- if a write fails, check connectivity to the mesh network
          if ( ! mesh.checkConnection() ) {
            // refresh the network address
            Serial.print(F(" - Renewing Address ... "));            
            if (mesh.renewAddress()!=0) {
              radio.printDetails();   
            } else {
              Serial.println(F(" habe keine Addresse erhalten."));
            };            
          } else {
            Serial.println(F(" - Fail, but connection was OK"));
          }
        } else {
          Serial.print(F(" - OK ")); //Serial.println(start_time);
        }
          
      } else{
        Serial.print(F(" - no wifi-mode "));        
      }
      
      // -- just used for testing memory leaks:
      //Serial.print(F(" freeMem:"));
      //Serial.print(freeMemory());
      //Serial.print(F(" -  uptime:"));
      //Serial.print(hours); Serial.print(":");Serial.print(minutes);Serial.print(":");Serial.print(seconds);
      Serial.print("\r\n");
    } 
    // -- reset counter for next transmission
    bufCnt = 0;  
  }
}
