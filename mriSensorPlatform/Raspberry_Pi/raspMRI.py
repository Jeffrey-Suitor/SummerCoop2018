# System Libraries
import re
import time
import os

# Program Libraries
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import bluetooth
import evdev
import subprocess
from pexpect import pxssh
import threading

def animate(i):
    global stream
    stream. getTemperature()

    # Plotting graph
    stream.ax1.clear()  # Clear plot
    try:  # try command because sometimes the initial connection throws a plot error
        for i in range(len(stream.immediateTemp[0])):
            lineList = []  # Reset list
            for j in range(len(stream.immediateTemp)):
                lineList.append(stream.immediateTemp[j][i])  # Create a list of temperature data of one sensor
            stream.ax1.plot(stream.immediateTime, lineList, color=stream.colourList[i], label=stream.tempData[i][0])  # Plot one sensor
            stream.ax1.legend()  # Create legend
    except:
        pass

    stream.logData()

def bluetoothProcess():
    global stream
    stream.setupPlot()
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    port = 1
    server_sock.bind(("", port))
    print('listening')
    server_sock.listen(1)  # Listen for the client to connection

    stream.client_sock, RFCOMMPort = server_sock.accept()
    for i in range(len(stream.bluetoothAddresses)):
        if RFCOMMPort[0] == stream.bluetoothAddresses[i][1]:
            print(stream.bluetoothAddresses + " on RFCOMM " + str(RFCOMMPort[1]))


    stream.timer()
    stream.updateTime = time.time()
    stream.startTime = time.time()

    for event in stream.dev.read_loop():  # This is where the TTL pulse is being waited on.
        if stream.dev.active_keys() == [6]:  # If the 5 key is pressed
            stream.keyPressed = True
            print('Scan Started')
            stream.deactivateTTLKey()
            stream.immediateTime = []
            stream.immediateTemp = []
            stream.updateTime = time.time()
            stream.startTime = time.time()
            while True:
                animation.FuncAnimation(stream.fig, animate, interval=1, fargs=(stream,))  # Update graph
                plt.show()  # Show graph
        else:
            stream.client_sock.recv(1024)

def autoSSH():
    global stream
    s = pxssh.pxssh()
    time.sleep(3)
    for i in range(len(stream.logins)):
        if not s.login(stream.logins[i][0], stream.logins[i][1], stream.logins[i][2]):
            print(stream.logins[i][1], " SSH session failed on login.")
            print(str(s))
        else:
            print(stream.logins[i][1], "SSH session login successful")
            for i in range(len(stream.commands)):
                s.sendline(stream.commands[i])

def receiveStream():
    global stream
    os.system(stream.netcatCommand)

def recordWindow():
    global stream
    time.sleep(2)
    os.system(stream.figureLocation)  # Sets the location of the live graph
    time.sleep(8)  # Time.sleep allows time for other loops to run
    os.system(stream.videoLocation)  # Sets the location of the video
    print("windows set")
    while True:
        if stream.keyPressed:  # if the scan has started
            recordCommand = "cd " + stream.patientFolder + " && recordmydesktop --windowid `xwininfo -name 'MPlayer' | grep 'id: 0x' | grep -Eo '0x[a-z0-9]+'` -o " + stream.patientDate + ":" + stream.patientName + ".ogv"  # Command to record the video
            os.system(recordCommand)
            stream.keyPressed = False
            break

def setup():
    global stream
    stream = raspberryPiStreamConfig()
    stream.resetKeyboard()
    stream.getPatientInfo()
    stream.createFolders()

class raspberryPiStreamConfig():

    def __init__(self):

        # Editable variables
        self.device = evdev.InputDevice('/dev/input/event18')  # Use cd /dev/input, ls and plug and unplug the device to find the TTL
        self.bluetoothAddresses = [['Athos', 'B8:27:EB:B8:71:43'], ['Porthos', 'B8:27:EB:8A:54:22'] ]  # Format of [name, bluetooth address]
        self.logins = [["Athos.local", "Athos", "deWinter"],
                  ["Aramis.local", "Aramis", "deChevreuse"],
                  ["Porthos.local", "Porthos",
                   "duVallon"]]  # Update with your raspberry pi info (hostname, user, password)
        self.commands = ['cd Desktop/pythonScripts', "python3 mainTest.py", ]  # list of bash commands to send to Pi
        self.figureLocation = 'wmctrl -r igure -b add,above -e 0,0,0,1000,700'  # G,X,Y,W,H   # Window placement
        self.videoLocation = 'wmctrl -r layer -b add,above -e 0,3000,0,1000,700'  # G,X,Y,W,H   # Window placement
        self.patientDataDirectory = "/home/jeff/PycharmProjects/MRIthon/patientData/"
        self.netcatCommand = "nc -l -p 2222 |mplayer -fps 200 -demuxer h264es -"
        self.resetKeyboardCommand = 'setxkbmap -layout us'
        self.colourList = [[0.458, 1.000, 0.984],  # Light Blue
                  [0.937, 0.043, 0.133],  # Red
                  [0.000, 0.050, 0.521],  # Dark Blue
                  [0.305, 0.911, 0.392],  # Light Green
                  [0.603, 0.556, 0.131],  # Light Brown
                  [0.431, 0.278, 0.027],  # Dark Brown
                  [1.000, 0.403, 0.039],  # Orange
                  [1.000, 0.996, 0.039],  # Yellow
                  [1.000, 0.039, 0.592]]  # Pink
        self.TTLKey = "xmodmap -e 'keycode 14='"
        self.waitTime = 10  # Change this value to adjust how long to wait for threads to catch up (10 is recommended)
        self.updateInterval = 15  # Change how often to update the txt file with new temperature data

        # Placeholder variables
        self.immediateTemp = []  # Empty btDvcList for temperature
        self.immediateTime = []  # Empty btDvcList for time
        self.startTime = None  # Placeholder for start time
        self.updateTime = None  # Placeholder for update time
        self.patientInfo = []  # Empty btDvcList for patient info
        self.fileNotInitialized = True  # Variable for file status
        self.filename = None  # Global place holder for filename
        self.client_sock = None  # Global place holder for client_sock
        self.keyPressed = False  # Global placeholder for keyPressed
        self.patientFolder = None
        self.tempList= []
        self.tempData = []
        self.timeList = []
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(1, 1, 1)
        self.ylim = (15, 30)

    def getPatientInfo(self):
        print('\nPlease answer the following questions before beginning a scan, press the enter key after each response.\n')
        self.patientInfo.append('Patient ID: ' + input('Name: '))  # patientInfo[0] = patient id
        self.patientInfo.append('\nWeight: ' + input('Weight: '))  # patientInfo[1] = weight
        self.patientInfo.append('\nDate: ' + input('Date: '))  # patientInfo[2] = date
        print('\nPatient information recorded..\n')



    def createFolders(self):
        if not os.path.exists(self.patientDataDirectory):  # Creates patient data patientDataDirectory
            os.makedirs(self.patientDataDirectory)

        self.patientFolder = self.patientDataDirectory + self.patientInfo[2] + ":" + self.patientInfo[0]

        if not os.path.exists(self.patientFolder):   # Creates patient folder
            os.makedirs(self.patientFolder)

    def resetKeyboard(self):  # Function to reset keyboard
        subprocess.run(self.resetKeyboardCommand,shell=True)

    def deactivateTTLKey(self):
        subprocess.run(self.TTLKey, shell=True)



    def setupPlot(self):
        plt.draw()
        plt.pause(0.01)
        self.ax1.set_ylim(self.ylim)
        self.ax1.set_title("Temperature vs Time\n(" + self.patientInfo[0].strip() + " " + self.patientInfo[2].strip() + ")")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Temperature (°C)")

    def timer(self):  # self.waitTime second timer to allow all threads to finish
        # Timer loop
        print("\nThe device will be ready in:")
        for i in range(self.waitTime):
            print(self.waitTime - i)
            time.sleep(1)
        print('\nReady\n')

    def logData(self):
        if self.fileNotInitialized:
            self.fileNotInitialized = False
            header = '\n\nTime\t'
            self.filename = self.patientInfo[0] + " " + self.patientInfo[2] + '.txt'  # Filename is patient name .txt
            f = open(self.patientFolder + '/' + self.filename, 'a+')
            for i in range(len(self.patientInfo)):
                f.write(self.patientInfo[i])  # Writes previously inputted patient info
            for i in range(len(self.tempData)):
                header += '\t\t\t\t\t' + self.tempData[i][0] + "(°C)"  # Creates header based on device name
            f.write(header)
            f.close()

        elif time.time() - self.updateTime > self.updateInterval and not self.fileNotInitialized:
            f = open(self.patientFolder + "/" + self.filename, 'a+')  # Open file in append mode
            for i in range(len(self.tempList)):
                f.write('\n' + str(round(self.timeList[i], 2)))  # Write the current time
                for j in range(len(self.tempList[i])):
                    f.write('\t\t\t\t\t\t' + str(round(self.tempList[i][j], 2)))  # Write the current temperatures
            f.close()
            self.updateTime = time.time()

    def getTemperature(self):  # TODO: Clean up this method by using decode
        self.usableData = True
        self.tempList = []

        rawTempData = self.client_sock.recv(1024).decode('utf-8')  # Receive data of form (name value | name2 value2 | etc)
        rawTempData = rawTempData.split("|")  # Splits data into each senscor

        del rawTempData[len(rawTempData) - 1]  # Deletes the extra entry of byte data
        for i in range(len(rawTempData)):
            rawTempData[i] = rawTempData[i].split(" ")  # Splits list element creating a 2d array in the structure of [name,value]
            rawTempData[0][0] = rawTempData[0][0][1:]  # Removes byte character from first element of the first list in 2d array
        timeData = float(time.time() - self.startTime)
        for i in range(len(rawTempData)):
            while len(rawTempData[i]) > 2:  # Remove additional byte elements in lists
                del rawTempData[i][0]
            try:  # try command because initial is unstable and can throw strange values
                rawTempData[i][1] = re.sub("[^0-9.]", "", rawTempData[i][1])  # Remove letters from the temperature
                rawTempData[i][1] = float(rawTempData[i][1])  # Convert temperature to float
                rawTempData[i][0] = re.sub("[^a-zA-Z]", "", rawTempData[i][0])  # Remove numbers from label
                self.tempData = rawTempData
                if rawTempData[i][1] > 100:  # Sometimes upon connection there is a large spike in the value
                   self.usableData = False
            except:
                self.usableData = False

        # Formatting Graph Data
        if self.usableData:
            for i in range(len(rawTempData)):
               self.tempList.append(rawTempData[i][1])  # Create a list of just temperatures
            self.immediateTime.append(timeData), self.immediateTemp.append(self.tempList)  # Append that list of just temperatures
            if len(self.immediateTime) > self.updateInterval:  # Shows the last x points of data
                del self.immediateTime[0]
                del self.immediateTemp[0]


# Run Threads
thread0 = threading.Thread(target=setup)
thread0.start()
thread0.join()
time.sleep(2)
thread1 = threading.Thread(target=autoSSH)
thread1.start()
thread2 = threading.Thread(target=receiveStream)
thread2.start()
thread3 = threading.Thread(target=bluetoothProcess)
thread3.start()
thread4 = threading.Thread(target=recordWindow)
thread4.start()
