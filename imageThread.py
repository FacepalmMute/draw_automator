from typing import Any
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from dataclasses import dataclass
import numpy as np
from skimage.measure import approximate_polygon, find_contours
from skimage import io
import cv2
import copy
import time

window = [0, 0, 640, 640]
# level = 180


@dataclass
class imgFormat:
    img: Any
    level: int
    contours: list
    size: list


class imageThread(QThread):

    newImage = pyqtSignal(imgFormat)

    requestedImage = None

    def __init__(self, parent=None):
        super(QThread, self).__init__(parent)

    def run(self):
        while self.requestedImage is None:
            time.sleep(0.01)

        self.processImage(self.requestedImage)

        self.requestedImage = None

    @pyqtSlot(bytes, int)
    def getImage(self, img: imgFormat) -> None:
        self.requestedImage = img

    def processImage(self, img: imgFormat) -> imgFormat:
        # print("Resize to {0} x {1} ...".format(size[0], size[1]))

        # cv2.imwrite('debug/converted.jpg', img.img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

        # new image without alpha channel...
        res_img = imageResize(img.img, width=img.size[0], height=img.size[1])

        conv_img = cv2.cvtColor(res_img, cv2.COLOR_BGRA2GRAY)

        # cv2.imwrite('debug/resized.jpg', res_img)

        extr_img, contours = extractLines(conv_img, img.level)

        ret = imgFormat(extr_img, img.level, contours, img.size)

        self.newImage.emit(ret)
        return ret


def extractLines(img, level):
    contours = find_contours(
        img, level, fully_connected="high", positive_orientation="low"
    )

    result_contour = np.zeros(img.shape + (3,), np.uint8)
    # result_polygon1 = np.zeros(img.shape + (3, ), np.uint8)
    # result_polygon2 = np.zeros(img.shape + (3, ), np.uint8)

    return_contour = []
    # return_polygon1 = []
    # return_polygon2 = []

    for contour in contours:
        # # reduce the number of lines by approximating polygons
        # polygon1 = approximate_polygon(contour, tolerance=2.5)

        # # increase tolerance to further reduce number of lines
        # polygon2 = approximate_polygon(contour, tolerance=15)

        contour = contour.astype(int).tolist()
        # polygon1 = polygon1.astype(int).tolist()
        # polygon2 = polygon2.astype(int).tolist()

        return_contour.append(contour)
        # return_polygon1.append(polygon1)
        # return_polygon2.append(polygon2)

        # draw contour lines
        for idx, coords in enumerate(contour[:-1]):
            y1, x1, y2, x2 = coords + contour[idx + 1]
            line = cv2.line(result_contour, (x1, y1), (x2, y2), (0, 255, 0), 1)
            result_contour = line
        # draw polygon 1 lines
        # for idx, coords in enumerate(polygon1[:-1]):
        #         y1, x1, y2, x2 = coords + polygon1[idx + 1]
        #         line = cv2.line(result_polygon1, (x1, y1), (x2, y2),
        #                                 (0, 255, 0), 1)
        #         result_polygon1 = line
        # # draw polygon 2 lines
        # for idx, coords in enumerate(polygon2[:-1]):
        #         y1, x1, y2, x2 = coords + polygon2[idx + 1]
        #         line = cv2.line(result_polygon2, (x1, y1), (x2, y2),
        #                                 (0, 255, 0), 1)
        #         result_polygon2 = line

    cv2.imwrite("debug/contour_lines.png", result_contour)
    # cv2.imwrite('debug/polygon1_lines.png', result_polygon1)
    # cv2.imwrite('debug/polygon2_lines.png', result_polygon2)

    return result_contour, return_contour


def imageResize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized
