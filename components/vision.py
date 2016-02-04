import multiprocessing
import time
import cv2
import numpy as np
from wpilib import Resource
import hal

import logging
video_width = 320
video_height = 240

class Vision:
    def __init__(self):
        self._data_array = multiprocessing.Array("d", [0.0, 0.0, 0.0, 0.0, 0.0])
        self.logger = logging.getLogger("vision")
        self._vision_process = VisionProcess(self._data_array)
        self._vision_process.start()
        self.logger.info("Vision process started")
        # Register with Resource so teardown works
        Resource._add_global_resource(self)

    def free(self):
        self._vision_process.terminate()

    def get(self):
        if self._data_array[2] > 0.0 and self._data_array[4] == 1.0:
            # New value and we have a target
            return self._data_array[0:4]
        else:
            return None

    def execute(self):
        pass


class VisionProcess(multiprocessing.Process):
    def __init__(self, data_array):
        super().__init__(args=(data_array,))
        self.vision_data_array = data_array
        self.logger = logging.getLogger("vision-process")
        if hal.HALIsSimulation():
            self.cap = VideoCaptureSim()
        else:
            self.cap = cv2.VideoCapture(-1)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, video_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, video_height)
        self.logger.info(self.cap)
        # Register with Resource so teardown works
        Resource._add_global_resource(self)

    def run(self):
        # counter = 0 # FPS counter
        tm = time.time()
        self.logger.info("Process started")
        while True:
            """ uncomment this and the counter above to get the fps
            counter += 1
            if counter >= 10:
                since = time.time()-tm
                self.logger.info("FPS: "+str(10.0/since))
                tm = time.time()
                counter = 0"""
            success, image = self.cap.read()
            if success:
                x, y, w, h, image = self.findTarget(image)
                self.vision_data_array[:] = [x, y, w, h, 1]
            else:
                self.vision_data_array[:] = [0.0, 0.0, 0.0, 0.0, 1]

    def findTarget(self, image):
        # Convert from BGR colourspace to HSV. Makes thresholding easier.
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # #Define the colours to look for (in HSV)
        lower_colour = np.array([40, 55, 210])
        upper_colour = np.array([110, 220, 255])
        # Create a mask that filters out only those colours
        mask = cv2.inRange(hsv_image, lower_colour, upper_colour)
        # Blur and average the mask - smooth the pixels out
        blurred = cv2.GaussianBlur(mask, (3, 3), 3, 3)
        # Errode and dialate the image to get rid of noise
        kernel = np.ones((4, 4), np.uint8)
        erosion = cv2.erode(blurred, kernel, iterations=1)
        dialated = cv2.dilate(erosion, kernel, iterations=1)
        # Get the information for the contours
        _, contours, __ = cv2.findContours(dialated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # sort the contours into a list
        areas = [cv2.contourArea(contour) for contour in contours]
        # and retrieve the largest contour in the list
        try:
            max_index = np.argmax(areas)
        except ValueError:
            result_image = image
            return 0.0, 0.0, 0.0, 0.0, result_image
        # define the largest contour
        cnt = contours[max_index]
        # get the area of the contour
        area = cv2.contourArea(cnt)
        # get the perimeter of the contour
        perimeter = cv2.arcLength(cnt, True)
        # get a rectangle and then a box around the largest countour
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        xy, wh, rotation_angle = cv2.minAreaRect(cnt)
        cv2.drawContours(image, [box], 0, (0, 0, 255), 2)
        (xy, wh, rotation_angle) = (rect[0], rect[1], rect[2])
        result_image = image
        # Converting the width and height variables to inbetween -1 and 1
        try:
            (x, y) = xy
            (w, h) = wh
        except ValueError:
            return 0.0, 0.0, 0.0, 0.0, result_image
        x = ((2 * x) / video_width) - 1
        y = ((2 * y) / video_height) - 1
        return x, y, w, h, result_image

class VideoCaptureSim():
    def read(self):
        return False, None
