#include <SoftwareSerial.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

SoftwareSerial serial_connection(10, 11);//Create a serial connection with TX and RX on these pins
int i = 0; //Arduinos are not the most capable chips in the world so I just create the looping variable once
int numSensors;
int count = 0;
int j = 0;
int relevantSensors[9];  //Array to store the number of relevant sensors, set to any number above the amount of sensors you are using

char addresses[][8] = {
  {0x28, 0xFF, 0x55, 0xBC, 0xC1, 0x17, 0x01, 0xA8}, //Addresses and addressesNamed are copies of one and other
  {0x28, 0xFF, 0x96, 0x57, 0xC4, 0x17, 0x04, 0x13},
  {0x28, 0xFF, 0x8B, 0xC1, 0xC1, 0x17, 0x01, 0x61}//Use the address finder to get the addresses of the sensors and enter them here
};

char* addressesNamed[][8] = {
  {"0x28", "0xFF", "0x55", "0xBC", "0xC1", "0x17", "0x01", "0xA8"},
  {"0x28", "0xFF", "0x96", "0x57", "0xC4", "0x17", "0x04", "0x13"},
  {"0x28", "0xFF", "0x8B", "0xC1", "0xC1", "0x17", "0x01", "0x61"}
};

char* names[] = { //Titles of the different sensors, change these to change the name on the graph.
  "Red",
  "Plain",
  "White",
  "Leg",
  "Feet",
  "ccccccccccc",
  "dddddddddd",
  "eeeeeeeeeeeee",
  "ffffffffffffff"
};

void setup()
{
  Serial.begin(9600);//Initialize communications to the serial monitor in the Arduino IDE
  sensors.begin(); //Initialize sensor (title of the one wire and dallas instance)
  serial_connection.begin(9600);//Initialize communications with the bluetooth module

  serial_connection.println("Ready!!!");//Send something to just start comms. This will never be seen.
  Serial.println("Started");//Tell the serial monitor that the sketch has started.

  numSensors = sensors.getDeviceCount(); //Detects the number of available sensors

  serial_connection.println("There are " + String(numSensors) + " temperature sensors available");
  Serial.println("There are " + String(numSensors) + " temperature sensors available");

  for (i = 0; i < 9; i++) {
    if (sensors.isConnected(addresses[i]) == true) { //Appends the index number of the available sensors in addresses to relevantSensors
      relevantSensors[count] = i;
      count++;
    }
  }
}
void loop()
{
  sensors.requestTemperatures();

  for (i = 0; i < numSensors; i++) {
    serial_connection.print(names[relevantSensors[i]]); //Prints the name of the sensor
    serial_connection.print(" ");
    serial_connection.print(sensors.getTempC(addresses[relevantSensors[i]])); //Prints the available temperature
    serial_connection.print("|");

  }
  serial_connection.println("");
  delay(500);//Pause for a moment

}
