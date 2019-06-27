""""
Jeff Suitor
McMaster University
St. Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
August 14th 2018

Notes: The arduino utilizes software serial 10 as rx and 11 as tx. The One Wire bus is pin 2.
"""

# System Libraries
import re
import subprocess
import time
import os

# Program Libraries
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import serial
import evdev

print(matplotlib.get_backend())
def animate(i):
    global stream
    print('hello')
    stream. getTemperature()
    # Plotting graph
    stream.ax1.clear()  # Clear plot
    for i in range(len(stream.immediateTemperature[0])):
        lineList = []  # Reset list
        for j in range(len(stream.immediateTemperature)):
            lineList.append(stream.immediateTemperature[j][i])  # Create a list of temperature data of one sensor
        stream.ax1.plot(stream.immediateTime, lineList, color=stream.colourList[i], label=stream.temperatureData[i][0]) # Plot one sensor
        stream.ax1.legend()  # Create legend
        stream.plotLabels()
    stream.logData()

class raspberryPiStreamConfig():

    def __init__(self):

        # Editable variables
        self.device = evdev.InputDevice('/dev/input/event6')  # Use cd /dev/input, ls and plug and unplug the device to find the TTL
        self.patientDataDirectory = "/home/jeff/PycharmProjects/MRIthon/patientData/"
        self.colourList = [[0.305, 0.911, 0.392],  # Light Green
                           [1.000, 0.403, 0.039],  # Orange
                           [0.458, 1.000, 0.984],  # Light Blue
                           [0.937, 0.043, 0.133],  # Red
                           [0.000, 0.050, 0.521],  # Dark Blue
                           [0.603, 0.556, 0.131],  # Light Brown
                           [0.431, 0.278, 0.027],  # Dark Brown
                           [1.000, 0.996, 0.039],  # Yellow
                           [1.000, 0.039, 0.592]]  # Pink
        self.TTLKey = "xmodmap -e 'keycode 14='" # Deactivate the 5 key
        self.waitTime = 10  # Change this value to adjust how long to wait for threads to catch up (10 is recommended)
        self.updateInterval = 15  # Change how often to update the txt file with new temperature data
        self.ylim = (15, 30)
        self.HC05Modules = [['98:D3:61:F5:C6:B9', 'blue'],['98:D3:71:F5:BE:B5', 'black'], ['98:D3:61:F5:C8:82', 'new ']]

        # Placeholder variables
        self.patientFolder = None
        self.patientInfo = []  # Empty List for patient info
        self.fileNotInitialized = True  # Variable for file status
        self.immediateTemperature = []  # Empty btDvcList for temperature
        self.immediateTime = []  # Empty btDvcList for time
        self.startTime = None  # Placeholder for start time
        self.updateTime = None  # Placeholder for update time
        self.filename = None  # Global place holder for filename
        self.client_sock = None  # Global place holder for client_sock
        self.keyPressed = False  # Global placeholder for keyPressed
        self.bluetooth = None
        self.onlyTemperatureList = []
        self.temperatureData = []
        self.timeList = []
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(1, 1, 1)


    def getPatientInfo(self):  # Function to acquire patient information
        print('\nPlease answer the following questions before beginning a scan, press the enter key after each response.\n')
        self.patientInfo.append('Patient ID: ' + input('Name: '))  # patientInfo[0] = patient id
        self.patientInfo.append('\nWeight: ' + input('Weight: '))  # patientInfo[1] = weight
        self.patientInfo.append('\nDate: ' + input('Date: '))  # patientInfo[2] = date
        print('\nPatient information recorded.\n')

    def createFolders(self):
        if not os.path.exists(self.patientDataDirectory):  # Creates patient data patientDataDirectory
            os.makedirs(self.patientDataDirectory)

        self.patientFolder = self.patientDataDirectory + self.patientInfo[2] + ":" + self.patientInfo[0]

        if not os.path.exists(self.patientFolder):   # Creates patient folder
            os.makedirs(self.patientFolder)

    def resetKeyboard(self):  # Function to reset keyboard
        subprocess.run('setxkbmap -layout us',shell=True)

    def deactivateTTLKey(self):
        subprocess.run(self.TTLKey, shell=True)

    def timer(self):  # self.waitTime second timer to allow all threads to finish
        # Timer loop
        print("\nThe device will be ready in:")
        for i in range(self.waitTime):
            print(self.waitTime - i)
            time.sleep(1)
        print('\nReady\n')

    def plotLabels(self):
        self.ax1.set_ylim(15,30)
        self.ax1.set_title("Temperature vs Time\n(" + self.patientInfo[0].strip() + " " + self.patientInfo[2].strip() + ")")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Temperature (°C)")

    def logData(self):
        try:
            if self.fileNotInitialized:
                self.fileNotInitialized = False
                header = '\n\nTime\t'
                self.filename = self.patientInfo[0] + " " + self.patientInfo[2] + '.txt'  # Filename is patient name .txt
                f = open(self.patientFolder + '/' + self.filename, 'a+')
                for i in range(len(self.patientInfo)):
                    f.write(self.patientInfo[i])  # Writes previously inputted patient info
                for i in range(len(self.temperatureData)):
                    header += '\t\t\t\t\t' + self.temperatureData[i][0] + "(°C)"  # Creates header based on device name
                f.write(header)
                f.close()

            elif time.time() - self.updateTime > self.updateInterval and not self.fileNotInitialized:
                f = open(self.patientFolder + "/" + self.filename, 'a+')  # Open file in append mode
                for i in range(len(self.onlyTemperatureList)):
                    f.write('\n' + str(round(self.timeList[i], 2)))  # Write the current time
                    for j in range(len(self.onlyTemperatureList[i])):
                        f.write('\t\t\t\t\t\t' + str(round(self.onlyTemperatureList[i][j], 2)))  # Write the current temperatures
                f.close()
                self.updateTime = time.time()
        except:
            pass

    def getTemperature(self):  # Function to receive bluetooth data and convert it to list form to graph
        self.usableData = True
        self.onlyTemperatureList = []

        try:
            self.temperatureData = self.bluetooth.readline().decode('utf-8')  # Receive data of form (name value | name2 value2 | etc)
            self.temperatureData = self.temperatureData.split("|")  # Splits data into each sensor
            del self.temperatureData[len(self.temperatureData) - 1]  # Deletes the extra entry of byte data
            for i in range(len(self.temperatureData)):
                self.temperatureData[i] = self.temperatureData[i].split(" ")  # Splits list element creating a 2d array in the structure of [name,value]
            self.temperatureData[i][1] = re.sub("[^0-9.]", "", self.temperatureData[i][1])  # Remove letters from the temperature
            self.temperatureData[i][0] = re.sub("[^a-zA-Z]", "", self.temperatureData[i][0])  # Remove numbers from label
            self.temperatureData[i][1] = float(self.temperatureData[i][1])  # Convert temperature to float
            if self.temperatureData[i][1] > 100:  # Sometimes upon connection there is a large spike in the value
               self.usableData = False
        except:
            self.usableData = False

        # Formatting Graph Data
        if self.usableData:
            try:
                timeData = float(time.time() - self.startTime)
                for i in range(len(self.temperatureData)):
                    self.onlyTemperatureList.append(self.temperatureData[i][1])  # Create a list of just temperatures
                self.immediateTime.append(timeData), self.immediateTemperature.append(self.onlyTemperatureList)  # Append that list of just temperatures
                if len(self.immediateTime) > self.updateInterval:  # Shows the last x points of data
                    del self.immediateTime[0]
                    del self.immediateTemperature[0]
            except:
                pass

    def bluetoothConnect(self):
        output = subprocess.check_output('hcitool scan', shell=True)  # Tool to scan for bluetooth device
        btDvcList = output.splitlines()  # Create a list of available devices
        for i in range(len(btDvcList)):
            btDvcList[i] = btDvcList[i].split()
            for j in range(len(btDvcList[i])):
                btDvcList[i][j] = str(btDvcList[i][j]).replace("'", "")
                btDvcList[i][j] = btDvcList[i][j][1:]

        del btDvcList[0]  # Deletes the scanning list element

        for i in range(len(btDvcList)):
            for j in range(len(self.HC05Modules)):
                if btDvcList[i][0] == self.HC05Modules[j][0]:
                    print('Connected to ' + self.HC05Modules[j][1] + "HC-05 module.")
                    bind = self.HC05Modules[j][0]

        subprocess.run('sudo rfcomm release 0', shell=True)  # Release the rfcomm (used for bluetooth), port 0
        command = 'sudo rfcomm bind 0 ' + bind  # Command to bind the found HC-05 to rfcomm 0
        subprocess.run(command, shell=True, )
        subprocess.run('sudo chmod 777 /dev/rfcomm0', shell=True)  # Allow any user to access rfcomm 0
        port = "/dev/rfcomm0"
        self.bluetooth = serial.Serial(port, 9600)  # Create a bluetooth rfcomm connection at baud of 9600
        self.bluetooth.flushInput()  # Ping the bluetooth module

    def receiveData(self):  # Function to detect 5 key from TTL box and begin to show the live graph

        for event in self.device.read_loop():
            if self.device.active_keys() == [6]:
                print('Scan Started')
                self.deactivateTTLKey()
                self.immediateTime = []
                self.immediateTemperature = []
                self.bluetooth.flushInput()
                self.updateTime = time.time()
                self.startTime = time.time()
                while True:
                    ani = animation.FuncAnimation(self.fig, animate, interval=1)  # Update graph
                    plt.show()  # Show graph

    def receiveDataTemp(self):
        self.immediateTime = []
        self.immediateTemperature = []
        self.bluetooth.flushInput()
        self.updateTime = time.time()
        self.startTime = time.time()
        print('starting animation loop')
        while True:
            animation.FuncAnimation(self.fig, animate, interval=1)  # Update graph
            plt.show()

stream = raspberryPiStreamConfig()
stream.resetKeyboard()
stream.getPatientInfo()
stream.plotLabels()
stream.createFolders()
stream.bluetoothConnect()
stream.timer()
stream.receiveDataTemp()

