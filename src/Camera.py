import cv2
import logging as log
import numpy as np
from base64 import b64encode
from typing import Union
from .RepeatTimer import RepeatTimer

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


class Camera(RepeatTimer):
    def __init__(self, encode_quality=50):
        RepeatTimer.__init__(self, interval=0., name='Camera')
        self.__cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
        if not self.__cap.isOpened():
            raise RuntimeError('Camera open fail')
        log.info('Camera open successful')
        self.__FPS = self.__cap.get(cv2.CAP_PROP_FPS)
        self.__delay = 1 / self.__FPS
        self.__width = int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.__height = int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.__is_image = False
        self.__image: Union[np.ndarray, None] = None
        self.lightness_text = ' .:-=+*#%@'
        self.light_lv = len(self.lightness_text) - 1
        self.encode_quality = [cv2.IMWRITE_JPEG_QUALITY, encode_quality]

    def __str__(self):
        s = 'FPS: %d  Delay: %f  Width: %d  Height: %d\n' % (self.__FPS, self.__delay, self.__width, self.__height)
        ret, image = self.__is_image, self.__image
        if not ret:
            s += '**NO IMAGE**'
            return s
        s += '+' + '-' * _ascii_w + '+\n'
        image = cv2.resize(image, (_ascii_w, _ascii_h))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        for row in image:
            s += '|'
            for pixel in row:
                s += self.lightness_text[round(pixel / 255 * self.light_lv)]
            s += '|\n'
        s += '+' + '-' * _ascii_w + '+\n'
        return s

    def init_phase(self):
        pass

    def execute_phase(self):
        is_image, image = self.__cap.read()
        if not is_image:
            image = None
        self.__is_image, self.__image = is_image, image

    def close_phase(self):
        self.__cap.release()
        self.__is_image, self.__image = False, None

    def get(self):
        is_image, image = self.__is_image, self.__image
        width, height = self.__width, self.__height

        if not is_image:
            return False, None
        if image.shape != (height, width, 3):
            return is_image, cv2.resize(image, (width, height), interpolation=cv2.INTER_NEAREST)
        return is_image, image

    def get_quality(self):
        return self.__width, self.__height

    def set_quality(self, width, height):
        self.__width = int(width)
        self.__height = int(height)

    def reset(self):
        self.__width = int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.__height = int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def encode_image_to_b64(self, image: np.ndarray):
        ret, jpg = cv2.imencode('.jpg', image, self.encode_quality)
        if not ret:
            return ''
        return b64encode(jpg.tobytes()).decode()
