'''
MReyeTracker.py
Jeff Suitor
McMaster University
St.Joseph's Imaging Research Center
Supervisor: Dr. Noseworthy
Tuesday August 14th 2018
Description: Program for eye tracking based of off Luke Allen's optimeyes, program uses raspberry pi camera.
You must draw a dot at the top of the bridge of the nose.
https://github.com/LukeAllen/optimeyes
'''

# Libraries
import struct
import socket
import io
import numpy as np
from numba import jit
import cv2
import ransac
from multiprocessing import Process
from pexpect import pxssh
import time
import random
import subprocess

########################################################################################################################
# Constants
port = random.randint(10000, 15000)  # Selects a random port between 10000 and 15000

doTraining = False  # Change this value to T or F if you want to activate the eyetracker

showMainImg = True

BLOWUP_FACTOR = 1  # Resizes image before doing the algorithm

dilationWidth = 1 + 2 * BLOWUP_FACTOR  # must be an odd number

dilationHeight = 1 + 2 * BLOWUP_FACTOR  # must be an odd number

dilationKernel = np.ones((dilationHeight, dilationWidth), 'uint8')  # creates a numpy array based off dilation height and width

haarFaceCascade = cv2.CascadeClassifier("./haarcascades/haarcascade_frontalface_alt.xml")  # location of haarcascades file

haarEyeCascade = cv2.CascadeClassifier("./haarcascades/haarcascade_eye.xml")

OffsetRunningAvg = None

PupilSpacingRunningAvg = None

writeEyeDebugImages = False  # enable to export image files showing pupil center probability

RANSAC_MIN_INLIERS = 7  # Numbers of clicks before the prediction is drawn

WINDOW_NAME = 'Training'  # Name of the training window

fileName = 'loginCredentials.txt'  # Name of the file where the credentials are kept

command = "python3 eyeTrackerSend.py " + str(port) + " n"  # Command to be sent via SSH, change n with f to flip video

directory = 'cd Desktop/pythonScripts'  # Directory where python script is located

########################################################################################################################

# Connection functions

def getCredentials(fileName):

    file = open(fileName)
    credentials = file.readlines()  # Split based on \n

    for i in range(len(credentials)):  # Remove all whitespace
        credentials[i] = credentials[i].split()

    return credentials  # Returns a list of credentials of form [hostname, username, password]



def login(fileName, command, directory):
    global port  # Import the randomly selected port
    time.sleep(1)  # Delay to ensure this code runs second
    sshLogin = pxssh.pxssh()

    loginCredentials = getCredentials(fileName)
    ipSearch = subprocess.check_output(["arp", "-a"]).decode('utf-8')  # Pings all available connections (There should only be one) and decodes the output
    ipSearch = ipSearch.split()  # Splits the lines

    for i in range(len(loginCredentials)):
        if ipSearch[0] == loginCredentials[i][0]:  # If the first item in ipSearch is equal to one of the Hostnames
            index = i

    sshLogin.login(loginCredentials[index][0], loginCredentials[index][1], loginCredentials[index][2])  # Login via SSH
    sshLogin.sendline(directory)  # Enter the proper directory where the scripts are located
    sshLogin.sendline(command)  # Send the command we previously created
    sshLogin.sendline(loginCredentials[index][2])  # Enter the sudo password (assuming you need to sudo a command)
    print('SSH Successful')
    while True:
        pass  # This keeps the SSH tunnel open



def socketConnection(port):  # Creates a socket connection to the Pi and and the port used is passed in
    server_socket = socket.socket()
    server_socket.bind(("", port))  # Bind to the port
    print("Listening")
    server_socket.listen(0)  # Listen for a connectoin
    connection = server_socket.accept()[0].makefile('rb')  # Save the connection
    print('Beginning to send data')
    return connection



def receiveFrame(connection):  # Connects to Pi stream and gets the image
    try:
        imgLen = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]  # Unpack the byte data from the connection
        imgStream = io.BytesIO()
        imgStream.write(connection.read(imgLen))  # Create the stream
        imgStream.seek(0)  # Rewind the stream

        data = np.fromstring(imgStream.getvalue(), dtype=np.uint8)
        imagedisp = cv2.imdecode(data, 1)  # Create an openCV image
        return imagedisp
    except:
        return False  # If stream fails return False


#Center Dot functions


def featureCenter(f):
    return .5*(f.mExtents[0]+f.mExtents[1]), .5*(f.mExtents[2]+f.mExtents[3])


def centeredBox(feature1, feature2, boxWidth, boxHeight, yOffsetToAdd = 0):
    f1 = np.array(featureCenterXY(feature1))
    f2 = np.array(featureCenterXY(feature2))
    center = (f1[:]+f2[:])/2
    center[1] += yOffsetToAdd
    offset = np.array([boxWidth/2,boxHeight/2])
    return np.concatenate( (center-offset, center+offset) )



def featureCenterXY(rect):
    #eyes are arrays of the form [minX, minY, maxX, maxY]
    return .5*(rect[0]+rect[2]), .5*(rect[1]+rect[3])


def contains(outerFeature, innerFeature):
    p = featureCenterXY(innerFeature)
    #eyes are arrays of the form [minX, minY, maxX, maxY]
    return p[0] > outerFeature[0] and p[0] < outerFeature[2] and p[1] > outerFeature[1] and p[1] < outerFeature[3]


def containsPoint(outerFeature, p):
    #eyes are arrays of the form [minX, minY, maxX, maxY]
    return p[0] > outerFeature[0] and p[0] < outerFeature[2] and p[1] > outerFeature[1] and p[1] < outerFeature[3]
# #
# # # Takes an ndarray of face rects, and an ndarray of eye rects.
# # # Returns the first eyes that are inside the face but not inside each other.
# # # Eyes are returned as the tuple (leftEye, rightEye)
# #
# #


def getLeftAndRightEyes(faces, eyes):
    # loop through detected faces. We'll do our processing on the first valid one.
    if len(eyes) == 0:
        return ()
    for face in faces:
        for i in range(eyes.shape[0]):
            for j in range(i + 1, eyes.shape[0]):
                leftEye = eyes[i]  # by left I mean camera left
                rightEye = eyes[j]
                # eyes are arrays of the form [minX, minY, maxX, maxY]
                if (leftEye[0] + leftEye[2]) > (rightEye[0] + rightEye[2]):  # leftCenter is > rightCenter
                    rightEye, leftEye = leftEye, rightEye  # swap
                if contains(leftEye, rightEye) or contains(rightEye,leftEye):  # they overlap. One eye containing another is due to a double detection; ignore it
                    continue
                if leftEye[3] < rightEye[1] or rightEye[3] < leftEye[
                    1]:  # top of one is below (>) bottom of the other. One is likely a mouth or something, not an eye.
                    continue
                ##                if leftEye.minY()>face.coordinates()[1] or rightEye.minY()>face.coordinates()[1]: #top of eyes in top 1/2 of face
                ##                    continue;
                if not (contains(face, leftEye) and contains(face,
                                                             rightEye)):  # face contains the eyes. This is our standard of humanity, so capture the face.
                    continue
                return (leftEye, rightEye)

    return ()


# # Returns (cy,cx) of the pupil center, where y is down and x is right. You should pass in a grayscale Cv2 image which
# # is closely cropped around the center of the eye (using the Haar cascade eye detector)
#


def getPupilCenter(gray, getRawProbabilityImage=False):
    gray = gray.astype('float32')
    if BLOWUP_FACTOR != 1:
        gray = cv2.resize(gray, (0, 0), fx=BLOWUP_FACTOR, fy=BLOWUP_FACTOR, interpolation=cv2.INTER_LINEAR)

    IRIS_RADIUS = gray.shape[
                      0] * 2 / 2  # conservative-large estimate of iris radius TODO: make this a tracked parameter--pass a prior-probability of radius based on last few iris detections. TUNABLE PARAMETER
    # debugImg(gray)
    dxn = cv2.Sobel(gray, cv2.CV_32F, 1, 0,
                    ksize=3)  # optimization opportunity: blur the image once, then just subtract 2 pixels in x and 2 in y. Should be equivalent.
    dyn = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitudeSquared = np.square(dxn) + np.square(dyn)

    # ########### Pupil finding
    magThreshold = magnitudeSquared.mean() * .05  # only retain high-magnitude gradients. <-- VITAL TUNABLE PARAMETER
    # The value of this threshold is critical for good performance.
    # todo: adjust this threshold using more images. Maybe should train our tuned parameters.
    # form a bool array, unrolled columnwise, which can index into the image.
    # we will only use gradients whose magnitude is above the threshold, and
    # (optionally) where the gradient direction meets characteristics such as being more horizontal than vertical.
    gradsTouse = (magnitudeSquared > magThreshold) & (np.abs(4 * dxn) > np.abs(dyn))
    lengths = np.sqrt(magnitudeSquared[gradsTouse])  # this converts us to double format
    gradDX = np.divide(dxn[gradsTouse], lengths)  # unrolled columnwise
    gradDY = np.divide(dyn[gradsTouse], lengths)
    ##    debugImg(gradsTouse*255)
    ##    ksize = 7 #kernel size = x width and y height of the filter
    ##    sigma = 4
    ##    blurredGray = cv2.GaussianBlur(gray, (ksize,ksize), sigma, borderType=cv2.BORDER_REPLICATE)
    ##    debugImg(gray)
    ##    blurredGray = cv2.blur(gray, (ksize,ksize)) #x width and y height. TODO: try alternately growing and eroding black instead of blurring?
    # isDark = blurredGray < blurredGray.mean()
    isDark = gray < (gray.mean() * .8)  # <-- TUNABLE PARAMETER
    global dilationKernel
    isDark = cv2.dilate(isDark.astype('uint8'), dilationKernel)  # dilate so reflection goes dark too
    ##    isDark = cv2.erode(isDark.astype('uint8'), dilationKernel)
    ##    debugImg(isDark*255)
    gradXcoords = np.tile(np.arange(dxn.shape[1]), [dxn.shape[0], 1])[
        gradsTouse]  # build arrays holding the original x,y position of each gradient in the list.
    gradYcoords = np.tile(np.arange(dxn.shape[0]), [dxn.shape[1], 1]).T[
        gradsTouse]  # These lines are probably an optimization target for later.
    minXForPupil = 0  # int(dxn.shape[1]*.3)
    ##    #original method
    ##    centers = np.array([[phi(cx,cy,gradDX,gradDY,gradXcoords,gradYcoords) if isDark[cy][cx] else 0 for cx in range(dxn.shape[1])] for cy in range(dxn.shape[0])])
    # histogram method
    centers = np.array([[phiWithHist(cx, cy, gradDX, gradDY, gradXcoords, gradYcoords, IRIS_RADIUS) if isDark[cy][
        cx] else 0 for cx in range(minXForPupil, dxn.shape[1])] for cy in range(dxn.shape[0])]).astype('float32')
    # display outputs for debugging
    ##    centers = np.array([[phiTest(cx,cy,gradDX,gradDY,gradXcoords,gradYcoords) for cx in range(dxn.shape[1])] for cy in range(dxn.shape[0])])
    ##    debugImg(centers)
    maxInd = centers.argmax()
    (pupilCy, pupilCx) = np.unravel_index(maxInd, centers.shape)
    pupilCx += minXForPupil
    pupilCy /= BLOWUP_FACTOR
    pupilCx /= BLOWUP_FACTOR
    if writeEyeDebugImages:
        global eyeCounter
        eyeCounter = (eyeCounter + 1) % 5  # write debug image every 5th frame
        if eyeCounter == 1:
            cv2.imwrite("eyeGray.png", gray / gray.max() * 255)  # write probability images for our report
            cv2.imwrite("eyeIsDark.png", isDark * 255)
            cv2.imwrite("eyeCenters.png", centers / centers.max() * 255)
    if getRawProbabilityImage:
        return (pupilCy, pupilCx, centers)
    else:
        return (pupilCy, pupilCx)



#
#
# # Estimates the probability that the given cx,cy is the pupil center, by taking
# # (its vector to each gradient location) dot (the gradient vector)
# # only uses gradients which are near the peak of a histogram of distance
# # cx and cy may be integers or floating point.


def phiWithHist(cx, cy, gradDX, gradDY, gradXcoords, gradYcoords, IRIS_RADIUS):
    vecx = gradXcoords - cx
    vecy = gradYcoords - cy
    lengthsSquared = np.square(vecx) + np.square(vecy)
    # bin the distances between 1 and IRIS_RADIUS. We'll discard all others.
    binWidth = 1  # TODO: account for webcam resolution. Also, maybe have it transform ellipses to circles when on the sides? (hard)
    numBins = int(np.ceil((IRIS_RADIUS - 1) / binWidth))
    bins = [(1 + binWidth * index) ** 2 for index in
            range(numBins + 1)]  # express bin edges in terms of length squared
    hist = np.histogram(lengthsSquared, bins)[0]
    maxBin = hist.argmax()
    slop = binWidth
    valid = (lengthsSquared > max(1, bins[maxBin] - slop)) & (
                lengthsSquared < bins[maxBin + 1] + slop)  # use only points near the histogram distance
    dotProd = np.multiply(vecx, gradDX) + np.multiply(vecy, gradDY)
    valid = valid & (
                dotProd > 0)  # only use vectors in the same direction (i.e. the dark-to-light transition direction is away from us. The good gradients look like that.)
    dotProd = np.square(dotProd[valid])  # dot products squared
    dotProd = np.divide(dotProd, lengthsSquared[valid])  # make normalized squared dot products
    ##    dotProd = dotProd[dotProd > .9] #only count dot products that are really close
    dotProd = np.square(dotProd)  # squaring puts an even higher weight on values close to 1
    return np.sum(dotProd)  # this is equivalent to normalizing vecx and vecy, because it takes dotProduct^2 / length^2


#
# # multiplies newProb and priorToMultiply
# # YXoffsetOfSecondWithinFirst - priorToMultiply will be shifted by this amount in space
# # defaultPriorValue - if not all of newProb is covered by priorToMultiply, this scalar goes in the uncovered areas.

def multiplyProbImages(newProb, priorToMultiply, YXoffsetOfSecondWithinFirst, defaultPriorValue):
    if np.any(YXoffsetOfSecondWithinFirst > newProb.shape) or np.any(
            -YXoffsetOfSecondWithinFirst > priorToMultiply.shape):
        ##        print "multiplyProbImages aborting - zero overlap. Offset and matrices:"
        ##        print YXoffsetOfSecondWithinFirst
        ##        print newProb.shape
        ##        print priorToMultiply.shape
        return newProb * defaultPriorValue
    prior = np.ones(
        newProb.shape) * defaultPriorValue  # Most of this will get overwritten. For areas that won't be, with fill with default value.
    # offsets
    startPrior = [0, 0]
    endPrior = [0, 0]
    startNew = [0, 0]
    endNew = [0, 0]
    for i in range(2):
        # offset=0
        # NOT THIS: x[1:2][1:2]
        # THIS: x[1:2,1:2]
        offset = int(round(
            YXoffsetOfSecondWithinFirst[i]))  # how much to offset 'prior' within 'newProb', for the current dimension
        ##        print offset
        if offset >= 0:  # prior goes right of 'newProb', in the world. So prior will be copied into newProb at a positive offset
            startPrior[i] = 0  # index within prior
            endPrior[i] = min(priorToMultiply.shape[i], newProb.shape[i] - offset)  # how much of prior to copy
            startNew[i] = offset
            endNew[i] = offset + endPrior[i]
        else:  # prior goes left of 'newProb', in the world.
            startPrior[i] = -offset
            endPrior[i] = min(priorToMultiply.shape[i], startPrior[i] + newProb.shape[i])
            startNew[i] = 0
            endNew[i] = endPrior[i] - startPrior[i]
    prior[startNew[0]:endNew[0], startNew[1]:endNew[1]] = priorToMultiply[startPrior[0]:endPrior[0],
                                                          startPrior[1]:endPrior[1]]
    # prior[1:10,1:10] = priorToMultiply[1:10,1:10]
    # now, prior holds the portion of priorToMultiply which overlapped newProb.
    return newProb * prior


## img: cv2 image in uint8 format
## cascade: object you made with cv2.CascadeClassifier("./haarcascades/haarcascade_frontalface_alt.xml")
## minimumFeatureSize (ySize,xSize) tuple holding the smallest object you'd be looking for. E.g. (30,30)
## returns a numpy ndarray where rects[0] is the first detection, and holds [minX, minY, maxX, maxY] where +Y = downward


def detect(img, cascade, minimumFeatureSize=(20, 20)):
    if cascade.empty():
        raise (Exception("There was a problem loading your Haar Cascade xml file."))
    rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=1, minSize=minimumFeatureSize)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]  # convert last coord from (width,height) to (maxX, maxY)
    return rects



def draw_rects(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


# init the filters we'll use below

# img.listHaarFeatures() displays these Haar options:
# ['eye.xml', 'face.xml', 'face2.xml', 'face3.xml', 'face4.xml', 'fullbody.xml', 'glasses.xml', 'lefteye.xml', #'left_ear.xml', 'left_eye2.xml', 'lower_body.xml', 'mouth.xml', 'nose.xml', 'profile.xml',
# 'right_ear.xml', 'right_eye.xml', 'right_eye2.xml', 'two_eyes_big.xml', 'two_eyes_small.xml', 'upper_body.xml', #'upper_body2.xml']



# *********  getOffset  **********
# INPUTS:
# frame - a color numpy image.
# allowDebugDisplay - pass True if you want it to draw pupil centers, etc on "frame" and then display it.
# Display requires that you called this line to create the window: previewWindow = cv2.namedWindow(WINDOW_NAME)
# trackAverageOffset - output will be a moving average rather than instantaneous value
# directInferenceLeftRight - combines probability images from left and right to hopefully reduce noise in estimation of pupil offset
# Returns a list of two tuples of pupil offsets from the forehead dot. Specifically:
# [(cameraLeftEyeOffsetX, cameraLeftEyeOffsetY),  (cameraRightEyeOffsetX, cameraRightEyeOffsetY) ]
# If no valid face is found, returns None.
# Requires the functions above.

def getOffset(frame, allowDebugDisplay=True, trackAverageOffset=True, directInferenceLeftRight=True):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    # find faces and eyes
    minFaceSize = (80, 80)  # Values for minimum size of the face
    minEyeSize = (25, 25)  # Values for the minimum size of the eyes
    faces = detect(gray, haarFaceCascade, minFaceSize)
    eyes = detect(gray, haarEyeCascade, minEyeSize)
    drawKeypoints = allowDebugDisplay  # can set this false if you don't want the keypoint ID numbers
    if allowDebugDisplay:
        output = frame
        draw_rects(output, faces, (0, 255, 0))  # BGR format
    else:
        output = None
    ##        draw_rects(output,eyes,(255,0,0))
    leftEye_rightEye = getLeftAndRightEyes(faces, eyes)
    if leftEye_rightEye:  # if we found valid eyes in a face
        ##            draw_rects(output,leftEye_rightEye,(0,0,255)) #BGR format
        xDistBetweenEyes = (leftEye_rightEye[0][0] + leftEye_rightEye[0][1] + leftEye_rightEye[1][0] +
                            leftEye_rightEye[1][1]) / 4  # for debugging reference point
        pupilXYList = []
        pupilCenterEstimates = []
        for eyeIndex, eye in enumerate(leftEye_rightEye):
            corner = eye.copy()

            # eyes are arrays of the form [minX, minY, maxX, maxY]
            eyeWidth = eye[2] - eye[0]
            eyeHeight = eye[3] - eye[1]
            eye[0] += eyeWidth * .20
            eye[2] -= eyeWidth * .15
            eye[1] += eyeHeight * .3
            eye[3] -= eyeHeight * .2
            eye = np.round(eye)
            eyeImg = gray[eye[1]:eye[3], eye[0]:eye[2]]
            if directInferenceLeftRight:
                (cy, cx, centerProb) = getPupilCenter(eyeImg, True)
                pupilCenterEstimates.append(centerProb.copy())
            else:
                (cy, cx) = getPupilCenter(eyeImg, True)
            pupilXYList.append((int(cx + eye[0]), int(cy + eye[1])))
            if allowDebugDisplay:
                cv2.rectangle(output, (eye[0], eye[1]), (eye[2], eye[3]), (0, 255, 0), 1)
                cv2.circle(output, pupilXYList[eyeIndex], 3, (255, 0, 0), thickness=1)  # BGR format

        # direct inference combination of the two eye probability images.
        global PupilSpacingRunningAvg
        if directInferenceLeftRight:
            # these vectors are in XY format
            pupilSpacing = np.array(pupilXYList[1]) - np.array(pupilXYList[0])  # vector from pupil 0 to pupil 1
            if PupilSpacingRunningAvg is None:
                PupilSpacingRunningAvg = pupilSpacing
            else:
                weightOnNew = .03
                PupilSpacingRunningAvg = (
                                                     1 - weightOnNew) * PupilSpacingRunningAvg + weightOnNew * pupilSpacing  # vector from pupil 0 to pupil 1
            if allowDebugDisplay:
                cv2.line(output, (int(pupilXYList[0][0]), int(pupilXYList[0][1])), (
                int(pupilXYList[0][0] + PupilSpacingRunningAvg[0]), int(pupilXYList[0][1] + PupilSpacingRunningAvg[1])),
                         (0, 100, 100))
            imageZeroToOneVector = leftEye_rightEye[1][0:2] - leftEye_rightEye[0][0:2]  # vector from eyeImg 0 to 1
            positionOfZeroWithinOne = PupilSpacingRunningAvg - imageZeroToOneVector;  # the extra distance that wasn't covered by the bounding boxes should be applied as an offset when multiplying images.
            ksize = 5  # kernel size = x width and y height of the filter
            sigma = 2
            for i, centerEstimate in enumerate(pupilCenterEstimates):
                pupilCenterEstimates[i] = cv2.GaussianBlur(pupilCenterEstimates[i], (ksize, ksize), sigma,
                                                           borderType=cv2.BORDER_REPLICATE)
            jointPupilProb = multiplyProbImages(pupilCenterEstimates[1], pupilCenterEstimates[0], positionOfZeroWithinOne[::-1],0)
            maxInd = jointPupilProb.argmax()

            (pupilCy, pupilCx) = np.unravel_index(maxInd,
                                                  jointPupilProb.shape)  # coordinates in the eye 1 (camera-right eye) image
            pupilXYList[0] = pupilXYList[1] = (
            pupilCx + leftEye_rightEye[1][0], pupilCy + leftEye_rightEye[1][1])  # convert to absolute image coordinates

        dotSearchBox = np.round(
            centeredBox(leftEye_rightEye[0], # feature 1
                        leftEye_rightEye[1], # feature 2
                        xDistBetweenEyes * .1, # boxwidth
                        xDistBetweenEyes * .1, # boxheight
                        -xDistBetweenEyes * .03 # box y offset
                        )).astype('int')

        (refY, refX) = getPupilCenter(gray[dotSearchBox[1]:dotSearchBox[3], dotSearchBox[0]:dotSearchBox[2]])
        refXY = (int(refX + dotSearchBox[0]), int(refY + dotSearchBox[1]))
        if allowDebugDisplay:
            cv2.rectangle(output, (dotSearchBox[0], dotSearchBox[1]), (dotSearchBox[2], dotSearchBox[3]),
                          (128, 0, 128), 1)
            cv2.circle(output, refXY, 2, (0, 0, 100), thickness=1)  # BGR format

        for i in range(len(pupilXYList)):
            pupilXYList[i] = (pupilXYList[i][0] - refXY[0], pupilXYList[i][1] - refXY[1])
        pupilXYList = list(pupilXYList[0]) + list(pupilXYList[
                                                      1])  # concatenate cam-left and cam-right coordinate tuples to make a single length 4 vector [x,y,x,y]

        if trackAverageOffset:  # this frame's estimated offset will be a weighted average of the new measurement and the last frame's estimated offset
            global OffsetRunningAvg
            if OffsetRunningAvg is None:
                OffsetRunningAvg = np.array([0, 0])
            weightOnNew = .4;  # Tuned parameter, must be >0 and <=1.0. Increase for faster response, decrease for better noise rejection.
            currentOffset = (np.array(pupilXYList[:2]) + np.array(pupilXYList[2:])) / 2
            OffsetRunningAvg = (1.0 - weightOnNew) * OffsetRunningAvg + weightOnNew * currentOffset
            pupilXYList = OffsetRunningAvg
            for i in range(len(pupilXYList)):
                pupilXYList[i] = int(pupilXYList[i])
            ##            import pdb; pdb.set_trace()
            if allowDebugDisplay:
                cv2.line(output, (int(refXY[0]), int(refXY[1])),
                         (int(refXY[0] + pupilXYList[0]), int(refXY[1] + pupilXYList[1])), (0, 255, 100))

        if allowDebugDisplay and showMainImg:
            # Double size
            cv2.imshow(WINDOW_NAME, cv2.resize(output, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
            # original size
        print(pupilXYList)
        return tuple(
            pupilXYList)  # if trackAverageOffset, it's length 2 and holds the average offset. Else, it's length 4 (old code)

    else:  # no valid face was found
        if allowDebugDisplay:
            cv2.imshow(WINDOW_NAME, cv2.resize(output, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
        return None


class LinearLeastSquaresModel:
    """linear system solved using linear least squares

    This class fulfills the model interface needed by the ransac() function.

    """

    # lists of indices of input and output columns
    def __init__(self, input_columns, output_columns, debug=False):
        self.input_columns = input_columns
        self.output_columns = output_columns
        self.debug = debug

    def fit(self, data):
        ##        A = numpy.vstack([data[:,i] for i in self.input_columns]).T
        ##        B = numpy.vstack([data[:,i] for i in self.output_columns]).T
        ##        x,resids,rank,s = scipy.linalg.lstsq(A,B)
        ##        return x
        HT = np.linalg.lstsq(data[:, self.input_columns], data[:, self.output_columns])[
            0]  # returns a tuple, where index 0 is the solution matrix.
        return HT

    def get_error(self, data, model):
        B_fit = data[:, self.input_columns].dot(model)
        err_per_point = np.sum((data[:, self.output_columns] - B_fit) ** 2, axis=1)  # sum squared error per row
        err_per_point = np.sqrt(err_per_point)  # I'll see if this helps. If not remove for speed.
        return err_per_point


def getFeatures(XYOffsets, quadratic=True):
    ##    print XYOffsets
    if len(XYOffsets.shape) == 1:
        numRows = 1
        XYOffsets.shape = (numRows, XYOffsets.shape[0])
    else:
        numRows = XYOffsets.shape[0]
    numCols = XYOffsets.shape[1]

    data = np.concatenate((XYOffsets, np.ones((XYOffsets.shape[0], 1))), axis=1)  # [x,y,1]
    if quadratic:
        squaredFeatures = np.square(XYOffsets)
        squaredFeatures.shape = (numRows, numCols)
        xy = XYOffsets[:, 0] * XYOffsets[:, 1]
        xy.shape = (numRows, 1)
        ##        print(xy.shape)

        data = np.concatenate((data, squaredFeatures, xy), axis=1)  # [x,y,1,x^2,y^2,xy]
    return data


def RANSACFitTransformation(OffsetsAndPixels):
    numInputCols = OffsetsAndPixels.shape[1] - 2
    data = np.concatenate((OffsetsAndPixels[:, 0:numInputCols], OffsetsAndPixels[:, numInputCols:]), axis=1)

    model = LinearLeastSquaresModel(range(numInputCols), (numInputCols, numInputCols + 1))
    minSeedSize = 5
    iterations = 800
    maxInlierError = 240  # **2
    HT = ransac.ransac(data, model, minSeedSize, iterations, maxInlierError, RANSAC_MIN_INLIERS)
    return HT


def mainForDebug():
    global port
    print('main')
    connection = socketConnection(port)
    print (port)
    cv2.namedWindow(WINDOW_NAME)  # Open a window to show debugging images
    while True:
        frame = receiveFrame(connection)  # Get frame from Pi
        getOffset(frame, allowDebugDisplay=True)  # Debug image set to true
        try:
            frame = receiveFrame(connection)  # Get frame from Pi
            getOffset(frame, allowDebugDisplay=True)  # Debug image set to true
        except:
            print('failed frame')
            pass
        key = cv2.waitKey(10)
        if key == 27:  # exit on ESC
            cv2.imwrite("lastOutput.png", frame)  # save the last-displayed image to file, for our report
            break


def mainForTraining():
    import pygamestuff
    global port
    crosshair = pygamestuff.Crosshair([7, 2], quadratic=False)
    connection = socketConnection(port)
    frame = receiveFrame(connection)
    MAX_SAMPLES_TO_RECORD = 999999  # Number of samples to record before crashing
    recordedEvents = 0  # Numbers of times you have clicked
    HT = None
    try:
        while recordedEvents < MAX_SAMPLES_TO_RECORD and not crosshair.userWantsToQuit:
            pupilOffsetXYList = getOffset(frame, allowDebugDisplay=False)
            if pupilOffsetXYList is not None:  # If we got eyes, check for a click. Else, wait until we do.
                if crosshair.pollForClick():  # Looks for click
                    print(crosshair.resetRansac)

                    crosshair.clearEvents()  # Resets any events
                    crosshair.record(pupilOffsetXYList)  # Relates the XY Offset to the XY Screen
                    crosshair.remove()  # Removes the corsshair
                    recordedEvents += 1  # Increase recorded event counter
                    if recordedEvents > RANSAC_MIN_INLIERS:  # If enough points have been used for the ransac
                        resultXYpxpy = np.array(crosshair.result)  # Creates an array of all the click locations
                        features = getFeatures(resultXYpxpy[:, :-2])
                        featuresAndLabels = np.concatenate((features, resultXYpxpy[:, -2:]), axis=1)
                        HT = RANSACFitTransformation(featuresAndLabels)
                    ##                        print (HT)
                    if crosshair.resetRansac == True:
                        recordedEvents = 0
                        HT = None
                        print('everything reset')
                if HT is not None:  # draw predicted eye position
                    currentFeatures = getFeatures(np.array((pupilOffsetXYList[0], pupilOffsetXYList[1])))
                    gazeCoords = currentFeatures.dot(HT)
                    crosshair.drawCrossAt((gazeCoords[0, 0], gazeCoords[0, 1]))
            frame = receiveFrame(connection)
        crosshair.write()  # writes data to a csv for MATLAB
        crosshair.close()
        resultXYpxpy = np.array(
            crosshair.result)  # This should be able to be saved and inputed in to create a pre-calibrated method
    finally:
        pass


if __name__ == '__main__':  # This call format is used for multiprocessing, check the readme for more info
    if doTraining:
        thread1 = Process(target=mainForTraining)
    else:
        thread1 = Process(target=mainForDebug)

    thread2 = Process(target=login, args=(fileName, command, directory))

    thread1.start()
    thread2.start()
