import cv2
import numpy as np
import logging as log
from typing import Dict, Optional
from base64 import b64encode
from .DetectorInterface import DetectorInterface
from .DetectResult import DetectResult
from .DetectorAPI import LOAD_MODEL, DETECT, RESET, CLOSE, GET_CONFIG, GET_CONFIGS
from .core import YOLOConfiger
from ..Client import Client

image_resize_w = 416
image_resize_h = 416


def encode_b64image(image: np.ndarray, width, height) -> str:
    image = cv2.resize(image, (width, height))
    ret, jpg = cv2.imencode('.jpg', image)
    return b64encode(jpg.tobytes()).decode()


class RemoteDetector(DetectorInterface):
    def __init__(self, ip, port, timeout, is_show_exc_info):
        self.client = Client(ip, port, timeout, is_show_exc_info)
        self.is_show_exc_info = is_show_exc_info

    def __str__(self):
        return 'Remote Detector address => %s:%s' % (self.client.ip, self.client.port)

    def load_model(self, config_name):
        cmd = LOAD_MODEL.copy()
        cmd['CONFIG_NAME'] = config_name
        self.client.send(cmd)

    def detect(self, image: np.ndarray) -> DetectResult:
        original_h, original_w = image.shape[:2]
        cmd = DETECT.copy()
        cmd['IMAGE'] = encode_b64image(image, image_resize_w, image_resize_h)
        result = self.client.send_and_recv(cmd)
        bbox = result.get('BBOX', [])
        scores = result.get('SCORE', [])
        classes = result.get('CLASS', [])
        x_scale = original_w / image_resize_w
        y_scale = original_h / image_resize_h
        real_boxes = [
            [
                round(box[0] * x_scale),
                round(box[1] * y_scale),
                round(box[2] * x_scale),
                round(box[3] * y_scale),
                box[4]
            ]
            for box in bbox
        ]
        detect_result = DetectResult(boxes=real_boxes, scores=scores, classes=classes)
        return detect_result

    def reset(self):
        cmd = RESET.copy()
        self.client.send(cmd)

    def close(self):
        cmd = CLOSE.copy()
        self.client.send(cmd)
        self.client.close()

    def get_configs(self) -> Dict[str, YOLOConfiger]:
        cmd = GET_CONFIGS.copy()
        configs = self.client.send_and_recv(cmd)
        configs = configs.get('CONFIGS', {})
        configer_group = {}
        for config in configs.values():
            try:
                yolo_configer = YOLOConfiger(config)
                configer_group[yolo_configer.name] = yolo_configer
            except Exception:
                log.error('Parse config to YOLOConfiger fail', exc_info=self.is_show_exc_info)
                continue
        return configer_group

    def get_config(self) -> Optional[YOLOConfiger]:
        cmd = GET_CONFIG.copy()
        config = self.client.send_and_recv(cmd)
        config = config.get('CONFIG')
        if not config:
            return None
        try:
            yolo_configer = YOLOConfiger(config)
            return yolo_configer
        except Exception:
            log.error('Get YOLOConfig fail', exc_info=self.is_show_exc_info)
            return None
