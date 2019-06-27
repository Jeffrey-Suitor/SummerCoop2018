Jeff Suitor
McMaster University
St. Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
August 14th 2018

Description: This a program that utilizes the raspberry 3B+ and a Pi Camera module to do eye tracking. This code is
inspired by Luke Allen's optimeyes code. https://github.com/LukeAllen/optimeyes

To use the code:

1. Update the loginCredentials.txt file, with the hostname, username, and password of your raspberry pi. Note that your
   Pi does not need a static ip address assuming you use hostname.local which locates the hostname on the local area
   network

2. Ensure you have all libraries installed. You will need the haarcascades folder from Luke Allen's optimeyes project.
   pexpect
   scipy
   numpy
   numba
   openCV (You will need the library with community contributions)
   pygame
   PIL or Pillow (PIL is the little brother of Pillow)

3. Place the pythonScripts folder on the Desktop of the Raspberry Pi, if you change the location make sure to change the
   directory constant in MReyeTracker.py.

4. Set the doTraining constant in MReyeTracker.py to be False and a debug display will appear. You want to draw a dark
   circle at the top of the bridge of the nose which serves as a reference point. Tune the paramaters in the
   tunable constants section in MReyeTracker.py until it tracks the dot and your eyes.

5. Set doTraining to True in MReyeTracker.py and a white window will appear. To train the model place the mouse cursor
   at different extremes of the window and without moving your head look at the cursor wait 1-2 seconds and the click
   left mouse button. Repeat this several times and eventually a black dot will appear. The more you click the better
   the fill be. Once satisfied press the escape key which saves a csv file. This csv file is the trained model of that
   ransac fit and now you have a trained eyetracker which with a bit of work can be applied to any study setup.

Reasons the code isn't working:

1. If using Wifi ensure that the Pi and the computer are on the same network.

2. If using ethernet make sure to turn off the raspberry Pi Wifi (right click the wifi icon in the top right and click
   "turn off"). Make sure you are using either a crossover cable or adapter from the PC to the Pi. If on linux make sure
   that the ethernet connection is setup in your options menu.

3. Note that this code has only been tested on linux Ubuntu 18.04. There may be errors with other distributions,
   Windows, or Mac.