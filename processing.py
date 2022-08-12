from math import atan2, degrees
from cv2 import COLOR_RGB2GRAY, THRESH_BINARY, COLOR_GRAY2RGB
import numpy as np
import cv2

TOLERANCE = 10
LONGSIDE = 300
SHORTSIDE = 205
THETA = 45

PROC_WIDTH = 350
PROC_HEIGHT = 301
BLACK_SPACES = 20

INPUT_PTS = np.float32([[248, 141],
                        [242, 295],
                        [412, 297],
                        [399, 142]])

# INPUT_PTS = np.float32([[255, 91],
#                         [245, 241],
#                         [415, 240],
#                         [408, 92]])
OUTPUT_PTS = np.float32([[0, 0],
                         [0, PROC_HEIGHT - 1],
                         [PROC_WIDTH - 1, PROC_HEIGHT - 1],
                         [PROC_WIDTH - 1, 0]])
transformMatrix = cv2.getPerspectiveTransform(INPUT_PTS, OUTPUT_PTS)
backTransformMatrix = cv2.getPerspectiveTransform(OUTPUT_PTS, INPUT_PTS)


class Processing:

    def __init__(self, src):
        self.source = src

    def addBorder(self, src):
        shape = src.shape
        _shape = list(shape)
        _shape[0] = shape[0] + BLACK_SPACES*2
        _shape[1] = shape[1] + BLACK_SPACES*2

        out = np.zeros(_shape, np.uint8)
        out[BLACK_SPACES:_shape[0]-BLACK_SPACES,
            BLACK_SPACES:_shape[1]-BLACK_SPACES] = src
        return out

    def removeBorder(self, src):
        shape = src.shape
        out = src[BLACK_SPACES:shape[0]-BLACK_SPACES,
                  BLACK_SPACES:shape[1]-BLACK_SPACES]
        return out

    def readFromSource(self):
        buf = self.source.read()
        self.img = buf
        return self.img

    def transform(self):
        transformed = cv2.warpPerspective(
            self.img, transformMatrix, [PROC_WIDTH, PROC_HEIGHT])
        medFilter = self.addBorder(transformed)
        medFilter = cv2.cvtColor(medFilter, COLOR_RGB2GRAY)
        medFilter = cv2.medianBlur(medFilter, 3)
        medFilter = self.removeBorder(medFilter)
        self.img = medFilter
        return cv2.cvtColor(self.img, COLOR_GRAY2RGB)

    def setBackground(self):
        self.readFromSource()
        self.transform()
        self.background = self.img
        return cv2.cvtColor(self.img, COLOR_GRAY2RGB)

    def subtractBackground(self):
        difference = cv2.absdiff(self.img, self.background)
        difference = self.addBorder(difference)
        diffBlur = cv2.medianBlur(difference, 23)
        diffBlur = self.removeBorder(diffBlur)
        _, diffBlur = cv2.threshold(
            diffBlur, 7, 255, THRESH_BINARY)
        self.img = diffBlur
        return self.img, cv2.cvtColor(self.img, COLOR_GRAY2RGB)

    def findTray(self):
        cont = np.zeros(self.img.shape, np.uint8)
        cont = cv2.cvtColor(cont, COLOR_GRAY2RGB)
        contours, _ = cv2.findContours(
            self.img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(cont, contours, -1, (255, 0, 0),
                         thickness=1, lineType=cv2.LINE_AA)
        if len(contours) > 0:
            rect = cv2.minAreaRect(max(contours, key=cv2.contourArea))
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(cont, [box], 0, (0, 255, 0),
                             thickness=1, lineType=cv2.LINE_AA)
            v1 = box[0] - box[1]
            v2 = box[3] - box[0]
            length = int(np.linalg.norm(v1))
            width = int(np.linalg.norm(v2))
            if length > width:
                v = v1
            else:
                v = v2
                length, width = width, length
            deg = abs(90 - int(degrees(atan2(v[1], v[0]))))
            return (length, width, deg), cont, box
        else:
            return (0, 0, 0), cont, np.array([[0, 0], [0, 0], [0, 0], [0, 0]])
