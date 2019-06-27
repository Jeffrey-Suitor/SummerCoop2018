'''
bluetoothFinder.py
Jeff Suitor
McMaster University
St. Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
August 15th 2018

Description: This program is run on the Raspberry Pi to locate the address to add to the bluetoothAddressBook.
'''

# Libraries
import bluetooth

targetName = "HAL9000"  # This is the name of the machine you want to add to the bluetoothAddressBook
targetAddress = None  # Initialized target address

nearby_devices = bluetooth.discover_devices()  # Returns a list of nearby devices

for address in nearby_devices:
    if targetName == bluetooth.lookup_name(address):  # If the address is the same as the target name
        targetAddress = address
        break

if targetAddress is not None:  # If you find correct address
    print("found target bluetooth device with address ", targetAddress)
else:
    print("could not find target bluetooth device nearby")