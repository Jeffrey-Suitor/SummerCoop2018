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

# Libraries
import glob
import bluetooth #This the bluez library
import time
import subprocess

# Variables
flag = False
btAddBook = "bluetoothAddressBook"  # Name of plain text bluetooth locations
wifiAddBook = "wifiAddressBook"  # Name of plain text wifi locations
base_dir = '/sys/bus/w1/devices/'

nameList = [  # Add string of for each sensor, this will be the title in the legend. Sensor can be inactive
    'sensor1',
    'sensor2',
    'sensor3']
activeSensors=[]  #
addressList=[  #addressList index = nameList index
    "/sys/bus/w1/devices/28-0117c1c18bff",
    "/sys/bus/w1/devices/28-0117c1bc55ff",
    "/sys/bus/w1/devices/28-0417c45796ff"]


#Functions

#Temperature Sensor

def readRawTemp():  # Get terminal output lines
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
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        time.sleep(1)
    except:
        print('video passed')
        pass
        
        
# Bluetooth Connection
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

            sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((bd_addr, port))
            flag = True
            
            while True:  # Here is where you would write your custom
                data = ""
                for i in range(len(deviceList)):
                    device_folder = glob.glob(base_dir + '28*')[i]
                    device_file = device_folder + '/w1_slave'
                    data += activeSensors[i] + " " + str(readTemp()) + "|"
                sock.send(str.encode(data))  # Sends the data string

        except:
            pass
