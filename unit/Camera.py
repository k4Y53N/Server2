import cv2
import logging
import numpy as np
from base64 import b64encode
from time import time, sleep
from threading import Thread

_width = 1280
_height = 720


def gstreamer_pipeline(
        capture_width=_width,
        capture_height=_height,
        display_width=_width,
        display_height=_height,
        framerate=59.,
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
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


class Camera:

    def __init__(self) -> None:
        self.__cap = cv2.VideoCapture(gstreamer_pipeline(
            flip_method=0), cv2.CAP_GSTREAMER)
        self.__grabbed, self.__image = False, None
        self.__streaming = True
        self.__is_client_stream = False
        self.__thread = Thread(target=self.__loop)

        if self.__cap.isOpened():
            self.__FPS = self.__cap.get(cv2.CAP_PROP_FPS)
            self.__delay = 1 / self.__FPS
            self.__width = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.__height = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            logging.info('Camera open successful')
        else:
            raise RuntimeError('Camera open fail')

    def activate(self):
        if self.__thread.is_alive():
            return

        try:
            self.reset()
            self.__thread.start()
        except RuntimeError:
            self.__thread = Thread(target=self.__loop, daemon=True)
            self.__thread.start()

    def __loop(self):
        while self.__streaming:
            start = time()
            self.__grabbed, self.__image = self.__cap.read()
            end = time()
            process_time = end - start

            if process_time < self.__delay:
                sleep(self.__delay - process_time)

        self.close()

    def get(self):
        return self.__grabbed, self.__image

    def reset(self):
        self.__width = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.__height = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.__is_client_stream = False

    def close(self):
        self.__streaming = False
        self.__cap.release()
        self.__grabbed, self.__image = False, None

    def get_JPG_base64(self, image: np.ndarray) -> str:
        if image.shape != (self.__width, self.__height, 3):
            image = cv2.resize(image, (self.__width, self.__height))

        ret, jpg = cv2.imencode('.jpg', image)

        if not ret:
            return None

        return b64encode(jpg.tobytes()).decode()

    def set_resolution(self, width: int, height: int):
        if width < 100 or height < 100:
            raise ValueError('Width or height is too small')
        try:
            width = int(width)
            height = int(height)
        except Exception:
            raise ValueError('Not effect value')

        self.__width = width
        self.__height = height

    def set_stream(self, command={}, *args, **kwargs):
        pass

    def get_resolution(self):
        return self.__width, self.__height

    def delay(self):
        return self.__delay

    def is_alive(self):
        return self.__thread.is_alive()

    def is_client_stream(self):
        return self.__is_client_stream
