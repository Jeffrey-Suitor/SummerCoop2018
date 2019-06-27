#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      lukea_000
#
# Created:     02/11/2013
# Copyright:   (c) lukea_000 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys, pygame
from pygame.locals import *

pygame.init()
size = width, height = 1920, 1080
white = 255, 255, 255
screen = pygame.display.set_mode(size)

class Crosshair(object):
    def __init__(self, speed = [1, 1], quadratic = True):
        self.quadratic = quadratic
        self.speed = speed
        self.cross = pygame.image.load('blackCircle.png')#pygame.image.load('bmpcrosshair.bmp')
        self.crossrect = self.cross.get_rect()
        self.result = []
        self.delay = 20
        self.userWantsToQuit = False
        self.draw()
        self.resetRansac = False

    def draw(self):
        self.remove()
        screen.blit(self.cross, self.crossrect)
        pygame.display.flip()

    def drawCrossAt(self, coords):
        self.crossrect.center = coords
        self.draw()

    def move(self):
        self.crossrect = self.crossrect.move(self.speed)
        if self.crossrect.left < 0 or self.crossrect.right > width:
            self.speed[0] = -self.speed[0]
        if self.crossrect.top < 0 or self.crossrect.bottom > height:
            self.speed[1] = -self.speed[1]

    def record(self, x, y):
        cx, cy = self.crossrect.centerx, self.crossrect.centery
        lis = [x, y, cx, cy]
        if self.quadratic == True:
            lis.append([cx * cx, cx * cy, cy * cy])
        self.result.append(lis)

    def record(self, inputTuple):
        self.result.append(list(inputTuple)+[self.crossrect.centerx,self.crossrect.centery])

    def write(self):
        fo = open("1920wxoffsetyoffsetxy.csv", "w")
        for line in self.result:
            print (line)
            result = ""
            for number in line:
                result += str(number) + str(',')
            fo.write(result + "\n")
        fo.close()

    #collects data, returns true if done looping
    def loop(self):
        self.move()
        pygame.time.delay(self.delay)
        self.draw()

    def remove(self):
        screen.fill(white)
        pygame.display.flip()

    def clearEvents(self):
        pygame.event.clear()

    def getClick(self):
        needClick = True
        while needClick:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.crossrect.center = pos
                    self.draw()
                    needClick = False
                else:
                    continue

    # Returns True, saves position, and draws the crosshairs if a click has occurred.
    # Returns False if not.
    def pollForClick(self):
        self.resetRansac = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                self.crossrect.center = pos
                self.draw()
                return True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.userWantsToQuit = True
                elif event.key == pygame.K_r:
                    self.result = []  # Reset command for the ransac function
                    self.resetRansac=True
                    print ('ransac reset')
                    return True
        return False

    def close(self):
        pygame.display.quit()
