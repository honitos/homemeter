#include <MemoryFree.h>
#include <SML.h>

#include <SoftwareSerial.h>
SoftwareSerial mySerial(2, 11,false);
const unsigned int MAXBUF = 255;
//char buffer[MAXBUF];
unsigned short bufCnt = 0;
const unsigned long eotTimeoutMs = 500;    // if no char received for 500 ms, declare end of transmission
sml mysml;

#include <VirtualWire.h>
const unsigned int sendframe = VW_MAX_MESSAGE_LEN;

// globale einstellungen
const int ledPin = 13;
const int dataPin = 2;
const int radioPin = 5;
byte ledState;


void honitosLED(byte blinks) {
  byte c = 0;

  //delay(1000);
  for (c = 0; c < blinks; c++) {
    digitalWrite(ledPin, HIGH);
    delay(500);
    digitalWrite(ledPin, LOW);
    delay(150);
  }
  for (c = 0; c < blinks; c++) {
    digitalWrite(ledPin, HIGH);
    delay(150);
    digitalWrite(ledPin, LOW);
    delay(150);
  }

}

void toggleLED(int pinNum) {
  digitalWrite(pinNum, ledState);
  ledState = !ledState;
}


// the setup function runs once when you press reset or power the board
void setup() {

  mysml.rawdata = new uint8_t[MAXBUF];

  // Pins konfigurieren
  pinMode(ledPin, OUTPUT);
  pinMode(dataPin, INPUT);

  honitosLED(3);

  // Open serial communications and wait for port to open:
  Serial.begin(57600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // set the data rate for the SoftwareSerial port
  mySerial.begin(9600);

  // Setup Virtual Wire
  vw_setup(4000);           // Bits pro Sekunde
  vw_set_tx_pin(radioPin);  // Datenleitung

  Serial.println("Empfangsbereit...");
}

// the loop function runs over and over again forever
void loop() 
{
  //--------------------------------------------------------------------------------------------------
  //static const char* serial_data = "1B1B1B1B0101010176051288C06962006200726500000101760101074553595133420B09014553591103984F4D010163C09C0076051288C06A6200620072650000070177010B09014553591103984F4D017262016500BE01AF7677078181C78203FF01010101044553590177070100010800FF0101621E52FC6900000005F19C81F30177070100010801FF0101621E520165000321660177070100010802FF0101621E5201650000C3CE0177070100010700FF0101621B52FE550000D5040177070100600505FF01010101630190010101632CBA0076051288C06B6200620072650000020171016314D500001B1B1B1B1A017A02\n";
  // nur in diesem Text, im Normalfall liefern die Daten ja schon als byte-strom vor...
  //mysml.initdata(serial_data);
  //mysml.parse();
  //--------------------------------------------------------------------------------------------------

  unsigned long lastCharTime = 0;
  if (mySerial.available() > 0) {            // enter "receiving" state if something is waiting to be read()  
    if (bufCnt > MAXBUF){
      Serial.println("PUFFERUEBERLAUF!");
    }
    //Serial.println("Lese daten.");
    mysml.rawdata[bufCnt++] = (uint8_t) mySerial.read();    // read first char
    lastCharTime = millis();             // timer start
    while ((mySerial.available() > 0) || (millis() - lastCharTime < eotTimeoutMs) && (bufCnt < MAXBUF - 1)) {
      if (mySerial.available() > 0) {
        mysml.rawdata[bufCnt++] = mySerial.read();
        lastCharTime = millis();             // timer restart
      }
      //Serial.print(mysml.rawdata[bufCnt-1],HEX);
    }
    //Serial.println("");
    // exit from "receiving" state due to:
    // - timeout (proper eot marker)
    // - buffer full condition (TODO: should be reported as an error)

    // "close" buffer
    mysml.rawdata[bufCnt] = 0;
    mysml.rawlength = bufCnt;
    
    digitalWrite(13, HIGH);

    uint8_t s;
    uint8_t sendlength = 150;
    uint8_t senddata[sendlength];
    for(s=0;s<150;s++) senddata[s]=0;
    mysml.parse(senddata);    
    Serial.print("Memfree nach Parser= ");
    Serial.print(freeMemory());   
    Serial.println(" bytes");

    digitalWrite(13, LOW);
    // reset counter for next transmission
    bufCnt = 0;   

    // -- send all the data to the data server  
    
    //printHex(senddata,64);
    uint8_t a,b;    
    uint8_t msg[sendframe];
    for(a=0; a < 100; a = a + sendframe){
      Serial.print("sending ");
      Serial.print(a);
      Serial.print(": ");
      for(b=0;b<sendframe;b++){
        if(a+b<sendlength){
          msg[b] = senddata[a+b];
        }
        else {
          msg[b] = 0;
        }
        Serial.print(msg[b],HEX);
        Serial.print(' ');
      }
      Serial.print("   sende");
      vw_send((uint8_t *)msg,sendframe);
      vw_wait_tx();
      Serial.println("...");
      delay(5);      
    }
    
   
  }
}

