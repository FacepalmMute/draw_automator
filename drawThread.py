from PyQt5.QtCore import (QCoreApplication, QObject, QRunnable, QThread,
                          QThreadPool, pyqtSignal, pyqtSlot)

import pyautogui as g
import sys
import cv2
import time
import base64
from pynput.mouse import Button, Controller, Listener
from pyscreeze import _screenshot_osx

import numpy as np
from skimage.measure import approximate_polygon, find_contours
from skimage import io

from imageThread import *

duration = 0.01
p_level = 0
g.PAUSE = 0

# Made pull request. Currently using my branch
g.DARWIN_CATCH_UP_TIME = 0.005
kill_threshold = 100

class drawThread(QThread):

    status = pyqtSignal()
    window = []

    def __init__(self, img: imgFormat, parent=None):
        super(QThread, self).__init__()
        self.img = img

    def run(self):
        print("Draw worker started")

        # Collect events until released
        with Listener(on_click=self.set_window) as listener:
            listener.join()
            listener.stop()

        print('Pressed {0} / {1}. Released {2} / {3}'.format(self.window[0], self.window[1], self.window[2], self.window[3]))
        self.img.size = (self.window[2] - self.window[0], self.window[3] - self.window[1])

        worker = imageThread(self)
        img = worker.processImage(self.img)
        worker.terminate()

        print("Draw {0} polygons/lines". format(len(img.contours)))
        for polygon in img.contours:
            self.draw_polygon(polygon)
        
        g.moveTo(self.window[2], self.window[3])
        self.window.clear()
        self.status.emit()

    def set_window(self, x, y, button, pressed):
        print(button)
        if (len(self.window) <= 2):
            print('{0} at {1}'.format(
                'Pressed' if pressed else 'Released',
                (x, y)))
            self.window.append(round(x))
            self.window.append(round(y))

        if not pressed and len(self.window) == 4:
            # Stop listener˚
            return False

    def killswitch(self):
        print("TRIGGERED KILLSWITCH")
        self.status.emit()
        # self.quit()

    def draw_polygon(self, polygon):
        g.mouseDown(polygon[0][1] + self.window[0], polygon[0][0] + self.window[1], duration=duration, button='left')

        if (sum(np.absolute(np.subtract((polygon[0][1] + self.window[0], polygon[0][0] + self.window[1]), g.position()))) > kill_threshold):
            self.killswitch()

        for dot in polygon:
            g.moveTo(dot[1] + self.window[0], dot[0] + self.window[1], duration=duration)

            if (sum(np.absolute(np.subtract((dot[1] + self.window[0], dot[0] + self.window[1]), g.position()))) > kill_threshold):
                g.mouseUp(duration=duration, button='left')
                self.killswitch()

        print(g.position())
        g.mouseUp(duration=duration, button='left')

    # def __draw_polyhon2(polygon):
    #     with Controller() as controller:
    #         controller.press(Button.left)

    #         for dot in polygon:
    #             offset_dot = (dot[1] + self.window[0], dot[0] + self.window[1])
    #             relative_dot = np.subtract(offset_dot, controller.position)

    #             controller.move(relative_dot[0], relative_dot[1])

    #             time.sleep(duration / 2)

    #             print("{0} / {1}".format(offset_dot, controller.position))

    #             if (sum(np.absolute(np.subtract((offset_dot[0], offset_dot[1]), controller.position))) > kill_threshold):
    #                 controller.release(Button.left)
    #                 killswitch()

    #         controller.release(Button.left)
    #         g.mouseUp(duration=duration, button='left')
    #         time.sleep(duration / 2)

    def draw_test(self):
        s_x = self.window[0]
        s_y = self.window[1]
        e_x = self.window[2]
        e_y = self.window[3]
        duration = 0.01
        scaler = 5

        if (self.window[0] > 0 and self.window[1] > 0 and self.window[2] > 0 and self.window[3] > 0):
            g.mouseDown(s_x, s_y, duration=duration)

            while (e_x > s_x or e_y > s_y):
                g.moveTo(e_x, s_y, duration=duration)
                g.moveTo(e_x, e_y, duration=duration)
                g.moveTo(s_x, e_y, duration=duration)
                s_y += scaler
                g.moveTo(s_x, s_y, duration=duration)
                s_x += scaler
                e_y -= scaler
                e_x -= scaler

            g.mouseUp(s_x, s_y)