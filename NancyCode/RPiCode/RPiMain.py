'''
mainTest.py
Jeff Suitor
McMaster University
St. Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
August 15th 2018

Description: This program is the main program run on the Raspberry PI to get hte temperature and send video. Note that
this setup uses the DS18B20 temperature probe. To use other
'''
'''
NOTES FOR NANCY

You can pretty well ignore anything regarding temp here. Everything is just the specific way to get the temp reading from the raspberry pi.

In video connect you'll notice a command variable. This is essentially [ raspivid and parameters | netcat commands]. Netcat is the networking utility I used to send video. 
It's a utility you can download and using subprocess you can send the commmands to the temrinal. Its fairly simple, but it can probably be done cleaner with a python library. 
The command works by | which pipes the output of the first command to the second command. 
nc ip-address port pipes send piped data to the specified ip address over the specified port.


''' 

# Libraries
import glob
import bluetooth #This the bluez library
import time
import subprocess 

# Variables
flag = False
btAddBook = "bluetoothAddressBook"
wifiAddBook = "wifiAddressBook"
base_dir = '/sys/bus/w1/devices/'  # This is used to get the onewire temperature sensor you can ignore this

nameList = [  # Add string of for each sensor, this will be the title in the legend. Sensor can be inactive
    'sensor1',
    'sensor2',
    'sensor3']
activeSensors=[]  #
addressList=[  #addressList index = nameList index (This is the address list for the different sensors)
    "/sys/bus/w1/devices/28-0117c1c18bff",
    "/sys/bus/w1/devices/28-0117c1bc55ff",
    "/sys/bus/w1/devices/28-0417c45796ff"]


#Functions

#Temperature Sensor (ignore all this its just for the temp sensors)

def readRawTemp():  # Get terminal output lines (This is all for the onewire temp sensor so you can ignore this)
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def readTemp():
    lines = readRawTemp()
    while lines[0].strip()[-3:] != 'YES':
        lines = readRawTemp()
    equals_pos = lines[1].find('t=') # Find temperature
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0  # Print in celcius
        return temp_c

def readAddressBook(filename):
    addressBook = open(filename)
    addressList = addressBook.readlines()  # Create a list of the different lines
    for i in range(len(addressList)):  # Split those lines based on whitespace delimiter
        addressList[i] = addressList[i].split()
    return addressList


# Video Connection
ipAddList = readAddressBook(wifiAddBook)  # Get a list of the ip addresses
for i in range(len(ipAddList)):
    try:
        command = "raspivid -t 0 -w 1280 -h 720 -fps 60 -o -p | nc " + str(ipAddList[i][1]) + " 2222" #Uses netcat to send video
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) # Send the command variable to the shell
        time.sleep(1)
    except:
        print('video passed')
        pass
        
        
# Bluetooth Connection (ignore all this is its just for setting up the temp sensors)
subprocess.Popen('modprobe w1-gpio', shell=True, stdout=subprocess.PIPE) #Turn on OneWire
subprocess.Popen('modprobe w1-therm', shell=True, stdout=subprocess.PIPE) #Turn on temperature OneWire

btAddList = readAddressBook(btAddBook)  # Get a list of the bluetooth addresses
deviceList = glob.glob(base_dir + '28*')

for i in range(len(deviceList)):
    #print(deviceList[i])  # Uncomment to find addresses of all connected sensors
    for k in range(len(addressList)):
        if deviceList[i] == addressList[k]:
            activeSensors.append(nameList[k])  # Creates a list of the names of the active sensors
        

#Bluetooth connect
for i in range(len(btAddList)):
    if flag != True:
        try:
            bd_addr = str(btAddList[i][1])

            port = 1

            sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM) #Creates a bluetooth connection object
            sock.connect((bd_addr, port)) #Connection is the bluetooth address and whatever bluetooth port you want. This will fail if it can't connect and thus that is why there is a broad try and except. I didn't really understand the error codes when I wrote this originally.
            flag = True
            
            while True:  
                data = "" #Resets the data string
                for i in range(len(deviceList)): # Adds each device to the data string before setting it by iterating over each
                    device_folder = glob.glob(base_dir + '28*')[i]
                    device_file = device_folder + '/w1_slave'
                    data += activeSensors[i] + " " + str(readTemp()) + "|" # Add each sensor to the data string
                sock.send(str.encode(data))  # Sends the data string

        except:
            pass
