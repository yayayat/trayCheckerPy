import numpy as np
import cv2
import v4l2
from fcntl import ioctl
import os
from threading import Lock, Thread

V4L2_CID_AUTO_N_PRESET_WHITE_BALANCE = v4l2.V4L2_CID_CAMERA_CLASS_BASE + 20
V4L2_WHITE_BALANCE_MANUAL = 0


class Camera:
    def setCameraSetting(self, id, value):
        ctrl = v4l2.v4l2_control()
        ctrl.id = id
        ctrl.value = value
        if ioctl(self.descriptor, v4l2.VIDIOC_S_CTRL, ctrl):
            print("error")
        else:
            print("done")

    def __init__(self, exp=2000):
        # --- INITIALIZE VIDEO DEVICE
        self.descriptor = os.open('/dev/video0',  os.O_RDWR, 0)
        print("Setting exposure time {0}..".format(exp))
        self.setCameraSetting(v4l2.V4L2_CID_EXPOSURE_ABSOLUTE, exp)
        print("Setting manual exposure mode..")
        self.setCameraSetting(v4l2.V4L2_CID_EXPOSURE_AUTO,
                              v4l2.V4L2_EXPOSURE_MANUAL)
        print("Setting manual white balance mode..")
        self.setCameraSetting(V4L2_CID_AUTO_N_PRESET_WHITE_BALANCE,
                              V4L2_WHITE_BALANCE_MANUAL)
        # --- INITIALIZE VIDEOCAPTURE
        deviceID = 0          # 0 = open default camera
        apiID = cv2.CAP_V4L2  # 0 = autodetect default API
        self.capture = cv2.VideoCapture(deviceID + apiID)
        _, img = self.capture.read()
        self.shape = img.shape
        print('Input image shape is {0}'.format(self.shape))

    def read(self, n=5):
        # _, input = self.capture.read()
        img = np.zeros(self.shape, np.float32)
        for i in range(n):
            _, buf = self.capture.read()
            img += buf
        img /= 5
        img = np.uint8(img)
        return img
