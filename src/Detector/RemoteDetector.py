import numpy as np
import cv2
import logging as log
from .DetectorInterface import DetectorInterface
from .DetectResult import DetectResult
from .Connection import ClientConnection
from .core import YOLOConfiger
from .Commands import LOAD_MODEL, DETECT, RESET, CLOSE, GET_CONFIG, GET_CONFIGS
from typing import Dict, Optional
from base64 import b64encode

image_resize_w = 416
image_resize_h = 416


def encode_b64image(image: np.ndarray, width, height) -> str:
    image = cv2.resize(image, (width, height))
    ret, jpg = cv2.imencode('.jpg', image)
    return b64encode(jpg.tobytes()).decode()


class RemoteDetector(DetectorInterface):
    def __init__(self, ip, port, is_show_exc_info):
        self.conn = ClientConnection(ip, port)
        self.is_show_exc_info = is_show_exc_info

    def __str__(self):
        return '**Remote Detector**'

    def load_model(self, config_name: str):
        cmd = LOAD_MODEL.copy()
        cmd['CONFIG_NAME'] = config_name
        self.conn.send_message(cmd)

    def detect(self, image: np.ndarray) -> DetectResult:
        original_h, original_w = image.shape[:2]
        cmd = DETECT.copy()
        cmd['IMAGE'] = encode_b64image(image, image_resize_w, image_resize_h)
        result = self.conn.send_and_recv(cmd)
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
        self.conn.send_message(cmd)

    def close(self):
        cmd = CLOSE.copy()
        self.conn.send_message(cmd)
        self.conn.close()

    def get_configs(self) -> Dict[str, YOLOConfiger]:
        cmd = GET_CONFIGS.copy()
        configs = self.conn.send_and_recv(cmd)
        configs = configs.get('CONFIGS', {})
        configer_group = {}
        for config in configs.values():
            try:
                yolo_configer = YOLOConfiger(config)
                configer_group[yolo_configer.name] = yolo_configer
            except Exception as E:
                log.error('Parse config to YOLOConfiger fail', exc_info=self.is_show_exc_info)
                continue
        return configer_group

    def get_config(self) -> Optional[YOLOConfiger]:
        cmd = GET_CONFIG.copy()
        config = self.conn.send_and_recv(cmd)
        config = config.get('CONFIG')
        if not config:
            return None
        try:
            yolo_configer = YOLOConfiger(config)
            return yolo_configer
        except Exception as E:
            log.error('Get YOLOConfig fail', exc_info=self.is_show_exc_info)
            return None
