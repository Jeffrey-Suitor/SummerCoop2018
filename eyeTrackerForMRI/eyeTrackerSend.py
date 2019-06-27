'''
eyeTrackerSend.py
Jeff Suitor
McMaster University
St.Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
Tuesday August 14th 2018
Description: Program to send picamera data from the raspberry pi to MReyeTracker.py with socket connection.
Based on Picamera basic recipe 4.9 capturing to a network stream
https://picamera.readthedocs.io/en/release-1.9/recipes1.html#capturing-to-a-network-stream
'''

#Libraries
import io
import socket
import struct
import time
import picamera
import sys

print('Connected over SSH')
client_socket = socket.socket()
client_socket.connect(('10.0.0.1', int(sys.argv[1])))  # second argument sent other than self is the port number (first is self)

# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        if sys.argv[2] == 'f':  # if f is sent flip the video is sent in connection command flip the video
            camera.rotation = 180
        else:
            camera.rotation = 0
        # Start a preview and let the camera warm up for 2 seconds
        camera.start_preview()
        time.sleep(2)

        # Note the start time and construct a stream to hold image data
        # temporarily
        start = time.time()
        stream = io.BytesIO()
        for enumerate in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            # Write the length of the capture to the stream and flush to
            # ensure it actually gets sent
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()

            # Rewind the stream and send the image data over the wire
            stream.seek(0)
            connection.write(stream.read())

            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
    # Write a length of zero to the stream to signal we're done
    connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    client_socket.close()
