# System Libraries
import time
import os
import subprocess


# Program Libraries
import evdev
from pexpect import pxssh
import threading


def ttlPulseWait():
    ssh = pxssh.pxssh()
    while stream.device.read_loop():  # Infinite loop that reads input events.
        if stream.device.active_keys() == [6]:  # If the 5 key is pressed
            stream.deactivateTTLKey()  # Deactivate the 5 key
            print('Scan Started')
            for i in range(len(stream.logins)):
                if not ssh.login(stream.logins[i][0], stream.logins[i][1], stream.logins[i][2]):
                    print(stream.logins[i][1], " SSH session failed on login.")
                else:
                    print(stream.logins[i][1], "SSH session login successful")
                    ssh.sendline(stream.command)
                    ssh.prompt()

def receiveStream():
    global stream
    print("Waiting on stream")
    subprocess.run(stream.netcatCommand, shell=True,)

def setup():
    global stream
    stream = raspberryPiStreamConfig()
    stream.resetKeyboard()
    stream.getPatientInfo()
    stream.createFolders()
    print("Setup complete")


class raspberryPiStreamConfig():

    def __init__(self):

        # Editable variables
        self.device = evdev.InputDevice('/dev/input/event15')  # Use cd /dev/input, ls and plug and unplug the device to find the TTL
        self.logins = [
            ["Athos.local", "Athos", "deWinter"],
            ["Aramis.local", "Aramis", "deChevreuse"],
            ["Porthos.local", "Porthos","duVallon"]]  # Update with your raspberry pi info (hostname, user, password)
        self.port = 2223  # Port you wish to use
        self.patientDataDirectory = "/home/jeff/code/python/MRIthon/patientData/" # Change to appropriate directory
        self.netcatCommand = "nc -l -p " + str(self.port) + " | mplayer -fps 200 -demuxer h264es -"
        self.resetKeyboardCommand = 'setxkbmap -layout us'  # Reset the keyboard to standard US layout 
        self.TTLKey = "xmodmap -e 'keycode 14='"  # Change the 5 key to a null value
        self.command = "cd pythonScripts && python3 raspMain.py " + str(self.port)  # Command with localtion of raspberry pi code

        # Placeholder variables
        self.patientInfo = []  # Empty list for patient info
        self.patientFolder = None  # Placeholder for patient data

    def getPatientInfo(self):
        print('\nPlease answer the following questions before beginning a scan, press the enter key after each response.\n')
        self.patientInfo.append(input('Patient ID: '))  # patientInfo[0] = patient id
        self.patientInfo.append(input('Date: '))  # patientInfo[1] = date
        print('\nPatient information recorded..\n')

    def createFolders(self):
        if not os.path.exists(self.patientDataDirectory):  # Creates patient data patientDataDirectory
            os.makedirs(self.patientDataDirectory)

        self.patientFolder = self.patientDataDirectory + self.patientInfo[1] + ":" + self.patientInfo[0]

        if not os.path.exists(self.patientFolder):   # Creates patient folder
            os.makedirs(self.patientFolder)

    def resetKeyboard(self):  # Function to reset keyboard
        subprocess.run(self.resetKeyboardCommand, shell=True)

    def deactivateTTLKey(self):  # Function to turn off the 5 key which is the TTL key for our MRI
        subprocess.run(self.TTLKey, shell=True)
    
# Run Threads
thread0 = threading.Thread(target=setup)
thread0.start()
thread0.join()
time.sleep(2)
thread1 = threading.Thread(target=ttlPulseWait)
thread1.start()
thread2 = threading.Thread(target=receiveStream)
thread2.start()
