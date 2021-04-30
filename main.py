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

window = []
level = 180
duration = 0
p_level = 0
g.PAUSE = 0

# Made pull request. Currently using my branch
g.DARWIN_CATCH_UP_TIME = 0.002
kill_threshold = 50

def data_uri_to_cv2_img(uri):
    encoded_data = uri.split(',')[1]
    nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    return img

def url_to_image(url):
    print("downloading {0}".format(url))
    img = io.imread(url)
    return img

def set_window(x, y, button, pressed):
    if (len(window) <= 2):
        print('{0} at {1}'.format(
            'Pressed' if pressed else 'Released',
            (x, y)))
        window.append(round(x))
        window.append(round(y))

    if not pressed and len(window) == 4:
        # Stop listener˚
        return False

def killswitch():
    print("TRIGGERED KILLSWITCH")
    quit()

def main():
    print(sys.argv[1])

    if ("data:image/" in sys.argv[1]):
        print("Use base64 image")
        img = data_uri_to_cv2_img(sys.argv[1])
    elif (("http://" in sys.argv[1]) or ("https://" in sys.argv[1])):
        print("Use web image")
        img = url_to_image(sys.argv[1])
    elif (sys.argv[1] != None):
        print("Use local image")
        img = cv2.imread(sys.argv[1])
    else:
        print("Invalid image source")
        return

    if (img.all() == None):
        print("Invalid image")
        return

    print("Listening")

    # Collect events until released
    with Listener(on_click=set_window) as listener:
            listener.join()
            listener.stop()

    print('Pressed {0} / {1}. Released {2} / {3}'.format(window[0], window[1], window[2], window[3]))

    res_img = resizeImage(img)
    lines, polygons1, polygons2 = extractLines(res_img)

    if (p_level == 0):
        draw(lines)
    elif (p_level == 1):
        draw(polygons1)
    elif (p_level == 2):
        draw(polygons2)

    g.moveTo(window[2], window[3])
    return True

def draw(polygons):
    print("Draw {0} polygons/lines". format(len(polygons)))
    for polygon in polygons:
        draw_polygon(polygon)

def draw_polygon(polygon):
    g.mouseDown(polygon[0][1] + window[0], polygon[0][0] + window[1], duration=duration, button='left')

    if (sum(np.absolute(np.subtract((polygon[0][1] + window[0], polygon[0][0] + window[1]), g.position()))) > kill_threshold):
        killswitch()

    for dot in polygon:
        g.moveTo(dot[1] + window[0], dot[0] + window[1], duration=duration)

        if (sum(np.absolute(np.subtract((dot[1] + window[0], dot[0] + window[1]), g.position()))) > kill_threshold):
            g.mouseUp(duration=duration, button='left')
            killswitch()

    print(g.position())
    g.mouseUp(duration=duration, button='left')

def __draw_polyhon2(polygon):
    with Controller() as controller:
        controller.press(Button.left)

        for dot in polygon:
            offset_dot = (dot[1] + window[0], dot[0] + window[1])
            relative_dot = np.subtract(offset_dot, controller.position)

            controller.move(relative_dot[0], relative_dot[1])

            time.sleep(duration / 2)

            print("{0} / {1}".format(offset_dot, controller.position))

            if (sum(np.absolute(np.subtract((offset_dot[0], offset_dot[1]), controller.position))) > kill_threshold):
                controller.release(Button.left)
                killswitch()

        controller.release(Button.left)
        g.mouseUp(duration=duration, button='left')
        time.sleep(duration / 2)

def draw_test():
    s_x = window[0]
    s_y = window[1]
    e_x = window[2]
    e_y = window[3]
    duration = 0.01
    scaler = 5

    if (window[0] > 0 and window[1] > 0 and window[2] > 0 and window[3] > 0):
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

def resizeImage(img):
    size = (window[2] - window[0], window[3] - window[1])

    print("Resize to {0} x {1}".format(size[0], size[1]))

    conv_img = cv2.imwrite('debug/converted.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

    #new image without alpha channel...
    conv_img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

    res_img = cv2.resize(conv_img, size)
    cv2.imwrite('debug/resized.jpg', res_img)
    return res_img

def extractLines(img):
        contours = find_contours(img, level, fully_connected='high', positive_orientation='low')

        result_contour = np.zeros(img.shape + (3, ), np.uint8)
        result_polygon1 = np.zeros(img.shape + (3, ), np.uint8)
        result_polygon2 = np.zeros(img.shape + (3, ), np.uint8)

        return_contour = []
        return_polygon1 = []
        return_polygon2 = []

        for contour in contours:

            # reduce the number of lines by approximating polygons
            polygon1 = approximate_polygon(contour, tolerance=2.5)

            # increase tolerance to further reduce number of lines
            polygon2 = approximate_polygon(contour, tolerance=15)

            contour = contour.astype(int).tolist()
            polygon1 = polygon1.astype(int).tolist()
            polygon2 = polygon2.astype(int).tolist()

            return_contour.append(contour)
            return_polygon1.append(polygon1)
            return_polygon2.append(polygon2)

            # draw contour lines
            for idx, coords in enumerate(contour[:-1]):
                    y1, x1, y2, x2 = coords + contour[idx + 1]
                    line = cv2.line(result_contour, (x1, y1), (x2, y2),
                                            (0, 255, 0), 1)
                    result_contour = line
            # draw polygon 1 lines
            for idx, coords in enumerate(polygon1[:-1]):
                    y1, x1, y2, x2 = coords + polygon1[idx + 1]
                    line = cv2.line(result_polygon1, (x1, y1), (x2, y2),
                                            (0, 255, 0), 1)
                    result_polygon1 = line
            # draw polygon 2 lines
            for idx, coords in enumerate(polygon2[:-1]):
                    y1, x1, y2, x2 = coords + polygon2[idx + 1]
                    line = cv2.line(result_polygon2, (x1, y1), (x2, y2),
                                            (0, 255, 0), 1)
                    result_polygon2 = line

        cv2.imwrite('debug/contour_lines.png', result_contour)
        cv2.imwrite('debug/polygon1_lines.png', result_polygon1)
        cv2.imwrite('debug/polygon2_lines.png', result_polygon2)

        return return_contour, return_polygon1, return_polygon2

if __name__ == "__main__":
    main()