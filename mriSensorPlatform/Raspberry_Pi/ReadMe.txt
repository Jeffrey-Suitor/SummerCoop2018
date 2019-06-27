Jeff Suitor
McMaster University
St. Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
August 14th 2018

This is my custom code for the bluetooth temperature transmission using Arduino (MRduino.py) and Raspberry Pi (raspMRI.py).
raspMRI.py also receives and records live video from the Raspberry PI. Both methods use the DS12B20 temperature probe.
The Arduino uses an HC-05 module for bluetooth and the Raspberry Pi uses any compatible Picamera.

To run the code on Arduino:

1. Plug in the HC-05 module. Ensure that the pins for the bluetooth module are wired correctly. RX on Arduino to the TX
on the HC-05 and the TX on the Arduino to the RX on the HC-05.

2. Next plug in the sensors to the appropriate ONE_Wire_BUS (currently set to 2) and flash the OneWireAddressFinder sketch
you then run it and it will return a list of the available sensors and their addresses. Copy these addresses and paste
them into both addresses and addressesNamed (make sure this is stringed) in the MRI_Arduino_Sketch.

3. Then proceed to flash the MRI_Arduino_Sketch.

4. On your bluetooth enabled PC run MRduino and you will begin to receive the temperature data and it will be live graphed
and stored in the patient's file found in the patientData folder. Make sure to update this path in MRduino. Note that this
code is not synched to the TTL Pulse.

To run the code on the Raspberry Pi:

1. On the Raspberry Pi update the bluetooth address book. Use the bluetooth address finder to quickly get your bluetooth
address just make sure to change the target PC name. Then do the same for the Wifi. Use whatever method is appropriate to
get the ip of the PC you are using and not the Pi.

2. Make sure the Pi and the PC can connect over bluetooth and wifi. Also make sure to update the raspberry Pi info in
raspMRI.py. Record window is currently setup for a 4k display so if you are using something small modify the placement
of the window in the recordWindow function.

3. Then attach your PC to the TTL Pulse box, in the case of our MRI this is a button box which sends 5 when a scan starts.
You will have to modify this based on system. Look in the bluetoothProcess function and go from there.