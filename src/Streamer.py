import logging as log
from threading import Thread, Lock
from time import sleep, perf_counter
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
from .Detector import ConfigManager, DetectResult, YOLOConfiger, RemoteConfigManager
from .Camera import Camera


class Frame:
    def __init__(self, b64image='', detect_result: Optional[DetectResult] = None):
        if detect_result is None:
            detect_result = DetectResult()
        self.b64image = b64image
        self.boxes = detect_result.boxes
        self.classes = detect_result.classes
        self.scores = detect_result.scores

    def is_available(self) -> bool:
        return bool(self.b64image)


class Streamer:
    def __init__(
            self,
            max_fps=30,
            idle_interval=1,
            stream_timeout=10,
            jpg_encode_rate=50,
            is_local_detector=False,
            yolo_configs_dir='./configs/',
            remote_detector_ip='127.0.0.1',
            remote_detector_port=5050,
            remote_detector_timeout=10,
            is_show_exc_info=False
    ):
        self.camera = Camera(jpg_encode_rate)
        if is_local_detector:
            self.detector = ConfigManager(
                yolo_configs_dir,
                is_show_exc_info=is_show_exc_info
            )
        else:
            self.detector = RemoteConfigManager(
                remote_detector_ip,
                remote_detector_port,
                remote_detector_timeout,
                is_show_exc_info=is_show_exc_info
            )

        self.thread_pool = ThreadPoolExecutor(5)
        self.exc_info = is_show_exc_info
        self.__is_infer = False
        self.__is_stream = False
        self.interval = 1 / max_fps if max_fps > 0 else 1
        self.idle_interval = idle_interval
        self.timeout = stream_timeout
        self.lock = Lock()

    def __str__(self):
        return str(self.detector) + '\n' + str(self.camera)

    def start(self):
        self.camera.start()

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
            self.__is_infer = False
            self.__is_stream = False
            self.camera.close()
            self.detector.close()
        self.thread_pool.shutdown(True)

    def get(self) -> Frame:
        init_time = perf_counter()
        with self.lock:
            is_stream = self.is_stream()
            is_infer = self.is_infer()

        frame = Frame()
        if is_stream and is_infer:
            is_image, image = self.camera.get()
            if is_image:
                frame = self.infer_and_encode_image(image)
        elif is_stream:
            is_image, image = self.camera.get()
            if is_image:
                frame.b64image = self.camera.encode_image_to_b64(image)

        if frame.is_available():
            ptime = perf_counter() - init_time
            if self.interval > ptime:
                sleep(self.interval - ptime)
        else:
            sleep(self.idle_interval)

        return frame

    def infer_and_encode_image(self, image) -> Frame:
        detecting = self.thread_pool.submit(self.detector.detect, image)
        encoding = self.thread_pool.submit(self.camera.encode_image_to_b64, image)
        try:
            b64image = encoding.result(timeout=self.timeout)
            detect_result = detecting.result(timeout=self.timeout)
            return Frame(b64image=b64image, detect_result=detect_result)
        except Exception as E:
            log.error(f'Encode and infer image error {E.__class__.__name__}', exc_info=self.exc_info)
            return Frame(b64image='', detect_result=None)

    def set_stream(self, is_stream: bool):
        with self.lock:
            self.__is_stream = is_stream

    def set_infer(self, is_infer: bool):
        with self.lock:
            self.__is_infer = is_infer

    def set_config(self, config_name):
        thread = Thread(target=self.detector.set_config, args=(config_name,))
        thread.start()

    def set_quality(self, width, height):
        self.camera.set_quality(width, height)

    def get_configs(self) -> Dict[str, YOLOConfiger]:
        return self.detector.get_configs()

    def get_config(self) -> Optional[YOLOConfiger]:
        return self.detector.get_config()

    def get_quality(self):
        return self.camera.get_quality()

    def is_stream(self):
        return self.__is_stream

    def is_infer(self):
        return self.__is_infer
