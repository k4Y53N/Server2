import cv2
import logging as log
import numpy as np
from base64 import b64encode
from .RepeatTimer import RepeatTimer
from typing import Tuple

_width = 1280
_height = 720
_ascii_w = 70
_ascii_h = 35


def gstreamer_pipeline(
        capture_width=_width,
        capture_height=_height,
        display_width=_width,
        display_height=_height,
        fps=59.,
        flip_method=0,
):
    return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                capture_width,
                capture_height,
                fps,
                flip_method,
                display_width,
                display_height,
            )
    )


def encode_image_to_b64(image: np.ndarray, size: Tuple[int, int]) -> str:
    if image.shape != size:
        image = cv2.resize(image, size)
    ret, jpg = cv2.imencode('.jpg', image)
    if not ret:
        return ''
    return b64encode(jpg.tobytes()).decode()


class Camera(RepeatTimer):
    def __init__(self):
        self.__cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
        if not self.__cap.isOpened():
            raise RuntimeError('Camera open fail')
        log.info('Camera open successful')
        self.__FPS = self.__cap.get(cv2.CAP_PROP_FPS)
        self.__delay = 1 / self.__FPS
        self.__width = int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.__height = int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.__ret = False
        self.__image: np.ndarray = None
        self.lightness_text = " .:-=+*#%@"
        self.light_lv = len(self.lightness_text) - 1
        RepeatTimer.__init__(self, interval=0.)

    def __str__(self):
        s = 'FPS: %d  Delay: %f  Width: %d  Height: %d\n' % (self.__FPS, self.__delay, self.__width, self.__height)
        ret, image = self.__ret, self.__image
        if not ret:
            s += '**NO IMAGE**'
            return s
        s += '-' * (_ascii_w + 2) + '\n'
        image = cv2.resize(image, (_ascii_w, _ascii_h))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        for row in image:
            s += '|'
            for pixel in row:
                s += self.lightness_text[round(pixel / 255 * self.light_lv)]
            s += '|\n'
        s += '-' * (_ascii_w + 2)
        return s

    def init_phase(self):
        pass

    def execute_phase(self):
        self.__ret, self.__image = self.__cap.read()

    def close_phase(self):
        self.__cap.release()
        self.__ret = False
        self.__image = None

    def get(self):
        if (not self.__ret) or self.__image is None:
            return False, None
        if self.__image.shape != (self.__height, self.__width, 3):
            return self.__ret, cv2.resize(self.__image, (self.__height, self.__width))
        return self.__ret, self.__image

    def get_quality(self):
        return self.__width, self.__height

    def set_quality(self, width, height):
        self.__width = int(width)
        self.__height = int(height)

    def reset(self):
        self.__width = int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.__height = int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_b64image(self, image):
        return encode_image_to_b64(image, (self.__width, self.__height))
