import logging as log
from pathlib import Path
from threading import Thread, Lock
from time import sleep
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from .Detector import Detector, DetectResult
from .Camera import Camera
from .core.configer import YOLOConfiger
from typing import Dict, Union


class Frame:
    def __init__(self, b64image=None, detect_result: Union[None, DetectResult] = None):
        if detect_result is None:
            detect_result = DetectResult()
        self.b64image = b64image
        self.boxes = detect_result.boxes
        self.classes = detect_result.classes
        self.scores = detect_result.scores

    def is_available(self):
        return self.b64image is not None


class Streamer:
    def __init__(self, yolo_config_dir: Path, interval: float = 0.05, timeout=10, exc_info=False):
        self.camera = Camera()
        self.detector = Detector(yolo_config_dir)
        self.thread_pool = ThreadPoolExecutor(5)
        self.exc_info = exc_info
        self.__is_infer = False
        self.__is_stream = False
        self.__is_running = False
        self.interval = interval
        self.timeout = timeout
        self.lock = Lock()

    def __str__(self):
        return str(self.detector) + '\n' + str(self.camera)

    def start(self):
        self.camera.start()
        with self.lock:
            self.__is_running = True

    def join(self):
        self.camera.join()

    def reset(self):
        with self.lock:
            self.__is_infer = False
            self.__is_stream = False
            self.camera.reset()
            self.detector.reset()

    def close(self):
        with self.lock:
            self.__is_running = False
            self.__is_infer = False
            self.__is_stream = False
            self.camera.close()
            self.detector.close()

    def get(self) -> Frame:
        if not self.is_running():
            raise RuntimeError('Streamer already closed')

        with self.lock:
            is_stream = self.is_stream()
            is_infer = self.is_infer()

        try:
            if not is_stream:
                sleep(self.interval)
                return Frame(b64image=None, detect_result=None)

            is_image, image = self.camera.get()

            if not is_image:
                sleep(self.interval)
                return Frame(b64image=None, detect_result=None)

            if not (is_infer and self.detector.is_available()):
                b64image = self.camera.encode_image_to_b64(image)
                sleep(self.interval)
                return Frame(b64image, detect_result=None)

            frame = self.infer_and_encode_image(image)
            return frame

        except Exception as E:
            log.error(f'Streaming Fail {E.__class__.__name__}', exc_info=self.exc_info)

        return Frame(b64image=None, detect_result=None)

    def infer_and_encode_image(self, image) -> Frame:
        with self.thread_pool as pool:
            encoding = pool.submit(self.camera.encode_image_to_b64, image)
            detecting = pool.submit(self.detector.detect, image)

        try:
            b64image = encoding.result(timeout=self.timeout)
            detect_result = detecting.result(timeout=self.timeout)
            return Frame(b64image=b64image, detect_result=detect_result)
        except TimeoutError as TOE:
            log.error('Encode and infer image time out', exc_info=self.exc_info)
            return Frame(b64image='', detect_result=None)

    def set_stream(self, is_stream: bool):
        with self.lock:
            self.__is_stream = is_stream

    def set_infer(self, is_infer: bool):
        with self.lock:
            self.__is_infer = is_infer

    def set_config(self, config_name):
        thread = Thread(target=self.detector.load_model, args=(config_name,))
        thread.start()

    def set_quality(self, width, height):
        self.camera.set_quality(width, height)

    def get_configs(self) -> Dict[str, YOLOConfiger]:
        return self.detector.get_configs()

    def get_config(self) -> Union[None, YOLOConfiger]:
        return self.detector.get_config()

    def get_quality(self):
        return self.camera.get_quality()

    def is_stream(self):
        return self.__is_stream

    def is_infer(self):
        return self.__is_infer

    def is_running(self):
        return self.__is_running
