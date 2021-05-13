from typing import Optional
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QWidget,
    QTableView,
    QAbstractItemView,
    QSlider,
    QVBoxLayout,
)
from PyQt5.QtGui import (
    QIcon,
    QPicture,
    QPixmap,
    QKeySequence,
    QKeyEvent,
    QImage,
    QDragEnterEvent,
    QPalette,
)
from PyQt5.QtCore import Qt

from imageThread import *
from drawThread import *

# Knows Bugs:
# Preview image is broken after killswitch triggered. drawThread possibly broke the reference.
# Preview background shows garbage after rescaling


class Gui(QWidget):

    defaultLevel = 10

    __imgThread_ready = True

    def __init__(self):
        super().__init__()
        self.title = "PyQt5 image - pythonspot.com"
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 640
        self.setAcceptDrops(True)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.layout = QVBoxLayout(self)

        # Image label
        self.imageLabel = QLabel(self)
        self.imageLabel.setBackgroundRole(QPalette.Base)
        pixmap = QPixmap("examples/ein_hauch_von_tuell.jpg")
        self.resize(pixmap.width(), pixmap.height())
        self.layout.addWidget(self.imageLabel)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 300)
        self.slider.setFocusPolicy(Qt.NoFocus)
        self.slider.setPageStep(5)
        self.slider.setValue(self.defaultLevel)
        self.slider.valueChanged.connect(self.sliderCallback)
        self.layout.addWidget(self.slider)

        # Button
        self.button = QPushButton(self)
        self.button.clicked.connect(self.drawCallback)
        self.layout.addWidget(self.button)

        self.imgThread = imageThread(self)
        self.imgThread.newImage.connect(self.refreshImage)
        self.imgThread.start()

        self.blockUI()
        self.show()

    def dragEnterEvent(self, e: QDragEnterEvent):
        print("Drag Event : ", end="")
        mime = e.mimeData()

        if mime.hasImage():
            print("Image")
            self.currentImage = imgFormat(
                QImageTocvmat(mime.imageData()),
                self.defaultLevel,
                None,
                (self.width, self.height),
            )
            self.requestImage(self.currentImage)
        elif mime.hasUrls():
            print("URL")
            self.currentImage = imgFormat(
                self.fetchImage(mime.urls()[0].toString()),
                self.defaultLevel,
                None,
                (self.width, self.height),
            )
            self.requestImage(self.currentImage)
            pass

    def keyPressEvent(self, event: QKeyEvent):
        clipboard = QApplication.clipboard()

        if event.matches(QKeySequence.Copy):
            print("Ctrl + C")
            clipboard.setText("some text")
        if event.matches(QKeySequence.Paste):
            print("Clip Event : ", end="")
            mime = clipboard.mimeData()

            if mime.hasImage():
                print("Image")
                self.currentImage = imgFormat(
                    QImageTocvmat(clipboard.image()),
                    self.defaultLevel,
                    None,
                    (self.width, self.height),
                )
                self.requestImage(self.currentImage)
            elif mime.hasUrls():
                print("URL")
            elif mime.hasText():
                print("Text")
                self.currentImage = imgFormat(
                    self.fetchImage(clipboard.text()),
                    self.defaultLevel,
                    None,
                    (self.width, self.height),
                )
                self.requestImage(self.currentImage)
            else:
                print("Unknown type")

    def fetchImage(self, data: Any) -> Optional[Any]:
        if "data:image/" in data:
            print("Use base64 image")
            img = uriTocvmat(data)
        elif ("http://" in data) or ("https://" in data):
            print("Use web image")
            img = urlToImage(data)
        elif "file://" in data:
            print("Use local image")
            img = cv2.imread(data[6:])
        else:
            print("Invalid image source")
            return None

        return img

    def refreshImage(self, img: imgFormat):
        self.imageLabel.clear()
        self.imageLabel.setPixmap(QPixmap.fromImage(cvmatToQImage(img.img)))
        self.__imgThread_ready = True
        self.releaseUI()

    def requestImage(self, img: imgFormat):
        if self.currentImage is not None and self.__imgThread_ready:
            self.__imgThread_ready = False
            self.imgThread.getImage(img)
            self.imgThread.start()
            self.blockUI()

    def sliderCallback(self, value):
        self.currentImage.level = value
        self.requestImage(self.currentImage)

    def drawCallback(self):
        self.currentImage.level = self.slider.value()
        self.blockUI()
        self.drawWorker = drawThread(self.currentImage, self)
        self.drawWorker.status.connect(self.releaseUI)
        self.drawWorker.start()

    def blockUI(self):
        self.button.setEnabled(False)
        self.slider.setEnabled(False)

    def releaseUI(self):
        self.button.setEnabled(True)
        self.slider.setEnabled(True)


def uriTocvmat(uri):
    encoded_data = uri.split(",")[1]
    nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.COLOR_BGRA2GRAY)
    return img


def urlToImage(url):
    print("downloading {0}".format(url))
    img = io.imread(url)
    return img


def QImageTocvmat(img: QImage):
    img = img.convertToFormat(QImage.Format_RGBX8888)
    width = img.width()
    height = img.height()
    ptr = img.bits()
    ptr.setsize(height * width * 4)

    # copy image data from ptr to avoid changes while runtime
    ret = np.fromstring(ptr, np.uint8).reshape((height, width, 4))
    ret.flags.writeable = False
    return ret


def cvmatToQImage(img: Any) -> QImage:
    bytesPerLine = 3 * 640
    qImg = QImage(img, 640, 640, bytesPerLine, QImage.Format_RGB666)
    return qImg


def to_tuple(lst):
    return tuple(to_tuple(i) if isinstance(i, list) else i for i in lst)


app = QApplication([])
gui = Gui()

# # Window should stay on top
# # TODO seems not to be working propertly
# gui.setWindowFlags(gui.windowFlags() | Qt.WindowStaysOnTopHint)
app.exec_()
