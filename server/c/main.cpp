

 /** RF24Mesh_Example_Master.ino by TMRh20
  *
  * Note: This sketch only functions on -Arduino Due-
  *
  * This example sketch shows how to manually configure a node via RF24Mesh as a master node, which
  * will receive all data from sensor nodes.
  *
  * The nodes can change physical or logical position in the network, and reconnect through different
  * routing nodes as required. The master node manages the address assignments for the individual nodes
  * in a manner similar to DHCP.
  *
  */


#include "stdio.h"
#include <unistd.h>
#include "string.h"
#include "time.h"

#include <honitos_sql.h>

#include "RF24Mesh/RF24Mesh.h"
#include <RF24/RF24.h>
#include <RF24Network/RF24Network.h>

using namespace std;

RF24 radio(RPI_V2_GPIO_P1_22, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ);
RF24Network network(radio);
RF24Mesh mesh(radio,network);

struct sml_dataset_t {
	uint32_t actSensorTime;
	uint32_t valTotal;
	uint32_t valTarif1;
	uint32_t valTarif2;
	uint32_t valCurrent;
};

int main(int argc, char** argv) {

    honitos_sql mysql("192.168.2.3","smartmeter","smartmeter","smartmeter");

    // connect to the mysql database
    std::cout << "Connecting to DB 192.168.2.3..." << std::endl;
    int mysql_status =0;

    mysql.connect();


    // Execute the first query, the result ist stored in mysql.query_result
    std::cout << "checking tables..." << std::endl;
    mysql.query("show tables");


    printf("MySQL Tables in mysql database:\n");
    MYSQL_ROW row;	// the results row (line by line)
    while ((row = mysql_fetch_row(mysql.query_result)) !=NULL)
        printf("%s \n", row[0]);

    /* clean up the database result set */
    mysql.free_result();

    /* clean up the database link */
    //mysql.close();

    // Set the nodeID to 0 for the master node
    mesh.setNodeID(0);
    // Connect to the mesh
    printf("honitos HomeServer V0.01 started...\n");
    mesh.begin();
    //radio.setCRCLength(RF24_CRC_8);
    radio.printDetails();

    time_t t_now;
    std::string command = "";

while(1)
{

  // Call network.update as usual to keep the network updated
  mesh.update();

  // In addition, keep the 'DHCP service' running on the master node so addresses will
  // be assigned to the sensor nodes
  mesh.DHCP();

  // Check for incoming data from the sensors
  while(network.available()){
//    printf("rcv\n");
    RF24NetworkHeader header;
    network.peek(header);

    sml_dataset_t sml;
    uint32_t dat = 0;

    switch(header.type){
      // Display the incoming millis() values from the sensor nodes
      case 'E':
		network.read(header,&sml,sizeof(sml));
        t_now = time(NULL);

        //printf("Total: %u, Current: %u from 0%o at: %ld\n",sml.valTotal,sml.valCurrent,header.from_node,t_now);
        std::cout << "Total: " << sml.valTotal;
        std::cout << ", Current: " << sml.valCurrent;
        std::cout << ", from Client " << header.from_node;
        std::cout << ", at: " << t_now;
        command = "INSERT INTO easymeter (SensorTime,Current,Total,DateTime) ";
        command += "VALUES (";
        command += std::to_string(sml.actSensorTime) + ",";
        command += std::to_string(sml.valCurrent) + ",";
        command += std::to_string(sml.valTotal) + ",";
        command += "Now(3))";


        mysql_status =  mysql.query(command.c_str());
        //mysql_status = 0;

        if(mysql_status!=0)
        {
            std::cout << " --> error writing to db, error " << mysql_status << std::endl;
        } else {
            std::cout << " --> written to database." << std::endl;
        };

		break;

      case 'M':
		network.read(header,&dat,sizeof(dat));
        printf("Rcv %u from 0%o\n",dat,header.from_node);
        break;

      default:
		network.read(header,0,0);
        printf("Rcv bad type %d from 0%o\n",header.type,header.from_node);
        break;
    }
    }
    usleep(2000);
    }
    return 0;
}




