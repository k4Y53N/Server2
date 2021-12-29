import cv2
import logging
import numpy as np
from base64 import b64encode
from threading import Thread

_width = 1280
_height = 720


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


class Camera:

    def __init__(self) -> None:
        self.__cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
        self.__streaming = True

        if self.__cap.isOpened():
            self.__FPS = self.__cap.get(cv2.CAP_PROP_FPS)
            self.__delay = 1 / self.__FPS
            self.__width = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.__height = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            logging.info('Camera open successful')
        else:
            raise RuntimeError('Camera open fail')

    def get(self):
        return self.__cap.read()

    def reset(self):
        self.__width = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.__height = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def close(self):
        self.__streaming = False
        self.__cap.release()

    def get_encode_thread(self, des_dict: dict, dic_key: str, image) -> Thread:
        return Thread(target=self.encode, args=(des_dict, dic_key, image), daemon=True)

    def encode(self, des_dic: dict, dic_key: str, image):
        des_dic[dic_key] = self.get_jpg_base64(image)

    def get_jpg_base64(self, image: np.ndarray) -> str:
        if image.shape != (self.__width, self.__height, 3):
            image = cv2.resize(image, (self.__width, self.__height))
        ret, jpg = cv2.imencode('.jpg', image)
        if not ret:
            return ''
        return b64encode(jpg.tobytes()).decode()

    def set_quality(self, width: int, height: int):
        if width < 100 or height < 100:
            raise ValueError('Width or height is too small')
        try:
            width = int(width)
            height = int(height)
        except Exception:
            raise ValueError('Not effect value')

        self.__width = width
        self.__height = height

    def get_resolution(self):
        return self.__width, self.__height

    def delay(self):
        return self.__delay
