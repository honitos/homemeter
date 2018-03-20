This is the arduino sketch file that enables an Arduino UNO oder Arduino Nano (both tested), to recieve data from easymeter and parse the complete message.
After parsing, the sketch transmits the data to the receiving unit. It uses the RF24Mesh-network routines.

There are two versions available:

sml_client_rf24 : uses rf24-mesh to transmit data to server
sml_client_vw   : uses virtualwire to transmit data to server (will not be updated anymore)

The parsing will be done by methods found in SML.h.
