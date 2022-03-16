import cv2
import tensorflow as tf
import numpy as np
import logging as log
from pathlib import Path
from threading import Lock
from typing import Union, Dict, Tuple
from .core.yolov4 import YOLO, decode, filter_boxes
from .core.configer import YOLOConfiger


def load_configer(configs_dir: Path, config_suffix='*.json') -> Dict[str, YOLOConfiger]:
    config_group = {}
    for config_file_path in configs_dir.glob(config_suffix):
        try:
            configer = YOLOConfiger(str(config_file_path))
            config_group[config_file_path.name] = configer
        except KeyError:
            log.warning(f'Parse json file {config_file_path} to YOLO-Configer fail')

    return config_group


def build_model(configer: YOLOConfiger):
    size = configer.size
    frame_work = configer.frame_work
    tiny = configer.tiny
    model_type = configer.model_type
    score_threshold = configer.score_threshold
    num_class = configer.num_class
    weight_path = configer.weight_path
    strides = configer.strides
    anchors = configer.anchors
    xyscale = configer.xyscale
    input_layer = tf.keras.layers.Input([size, size, 3])
    feature_maps = YOLO(input_layer, num_class, model_type, tiny)
    bbox_tensors = []
    prob_tensors = []

    if tiny:
        for i, fm in enumerate(feature_maps):
            if i == 0:
                output_tensors = decode(fm, size // 16, num_class, strides, anchors, i, xyscale, frame_work)
            else:
                output_tensors = decode(fm, size // 32, num_class, strides, anchors, i, xyscale, frame_work)
            bbox_tensors.append(output_tensors[0])
            prob_tensors.append(output_tensors[1])
    else:
        for i, fm in enumerate(feature_maps):
            if i == 0:
                output_tensors = decode(fm, size // 8, num_class, strides, anchors, i, xyscale, frame_work)
            elif i == 1:
                output_tensors = decode(fm, size // 16, num_class, strides, anchors, i, xyscale, frame_work)
            else:
                output_tensors = decode(fm, size // 32, num_class, strides, anchors, i, xyscale, frame_work)
            bbox_tensors.append(output_tensors[0])
            prob_tensors.append(output_tensors[1])
    pred_bbox = tf.concat(bbox_tensors, axis=1)
    pred_prob = tf.concat(prob_tensors, axis=1)
    if frame_work == 'tflite':
        pred = (pred_bbox, pred_prob)
    else:
        boxes, pred_conf = filter_boxes(pred_bbox, pred_prob, score_threshold=score_threshold,
                                        input_shape=tf.constant([size, size]))
        pred = tf.concat([boxes, pred_conf], axis=-1)
    model = tf.keras.Model(input_layer, pred)
    model.load_weights(weight_path)

    return model


class Detector:
    def __init__(self, config_dir: Path) -> None:
        self.configer_group: Dict[str, YOLOConfiger] = load_configer(config_dir)
        self.configer: Union[None, YOLOConfiger] = None
        self.lock = Lock()
        self.model: Union[tf.keras.Model, None] = None
        self.size = 0
        self.classes = []
        self.iou_threshold = 0.5
        self.score_threshold = 0
        self.max_total_size = 50
        self.max_output_size_per_class = 20
        self.timeout = 1
        self.__is_available = False

    def load_model(self, config_name):
        if config_name not in self.configer_group.keys():
            log.info(f'Config not exist {config_name}')
            return
        log.info(f'Loading model {config_name}')
        acquired = self.lock.acquire(True, self.timeout)
        if not acquired:
            log.info(f'Loading model timeout, another model is loading')
            return
        try:
            self.__release()
            configer = self.configer_group[config_name]
            self.configer = configer
            self.model = build_model(configer)
            self.size = configer.size
            self.classes = configer.classes
            self.iou_threshold = configer.iou_threshold
            self.score_threshold = configer.score_threshold
            self.max_total_size = configer.max_total_size
            self.max_output_size_per_class = configer.max_output_size_per_class
            self.__is_available = True
        except Exception as E:
            log.error('Loading model fail', exc_info=E)
            self.__release()
        finally:
            self.lock.release()

    def detect(self, image: np.ndarray, is_cv2=True) -> Tuple[list, list]:
        acquired = self.lock.acquire(False)
        if not acquired:
            return [], []
        try:
            return self.infer(image, is_cv2=is_cv2), self.classes
        except Exception as E:
            return [], []
        finally:
            self.lock.release()

    def infer(self, image: np.ndarray, is_cv2=True) -> list:
        if self.model is None:
            return []
        height, width = image.shape[:2]
        data = self.normalization(image, is_cv2=is_cv2)
        pred = self.model(data)
        batch_size, num_boxes = pred.shape[:2]

        nms_boxes, nms_scores, nms_classes, valid_detections = tf.image.combined_non_max_suppression(
            boxes=tf.reshape(pred[:, :, :4], (batch_size, num_boxes, 1, 4)),
            scores=pred[:, :, 4:],
            max_output_size_per_class=self.max_output_size_per_class,
            max_total_size=self.max_total_size,
            iou_threshold=self.iou_threshold,
            score_threshold=self.score_threshold,
        )
        nms_boxes = tf.reshape(nms_boxes, (-1, 4))
        nms_classes = tf.reshape(nms_classes, (-1, 1))
        valid_data = tf.concat(
            (nms_boxes, nms_classes),
            axis=1
        )[:valid_detections[0]]
        result = np.empty(valid_data.shape, dtype=np.int)
        for index, valid in enumerate(valid_data):
            # pred boxes = [y1, x1, y2, x2]
            # true boxes = [x1, y1, x2, y2]
            result[index][0] = valid[1] * width
            result[index][1] = valid[0] * height
            result[index][2] = valid[3] * width
            result[index][3] = valid[2] * height
            result[index][4] = valid[4]

        return result.tolist()

    def normalization(self, image: np.ndarray, is_cv2=True) -> np.ndarray:
        if is_cv2:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        return cv2.resize(image, (self.size, self.size))[np.newaxis, :] / 255.

    def reset(self):
        with self.lock:
            self.__release()

    def close(self):
        self.reset()
        self.configer_group = None

    def __release(self):
        self.__is_available = False
        self.model = None
        self.size = 0
        self.classes = []
        self.score_threshold = 0
        self.max_total_size = 20
        tf.keras.backend.clear_session()

    def get_configs(self):
        return {
            key: {
                'SIZE': value.size,
                'MODEL_TYPE': value.model_type,
                'TINY': value.tiny,
                'CLASSES': value.classes
            }
            for key, value in self.configer_group.items()
        }

    def get_config(self) -> Dict:
        config = {
            'CONFIG_NAME': None,  # STR
            'SIZE': 0,
            'MODEL_TYPE': None,  # STR
            'TINY': False,
            'CLASSES': [],  # STR ARRAY
        }
        configer = self.configer
        if configer is None:
            return config
        config['CONFIG_NAME'] = configer.name
        config['SIZE'] = configer.size
        config['MODEL_TYPE'] = configer.model_type
        config['TINY'] = configer.tiny
        config['CLASSES'] = configer.classes

        return config

    def is_available(self):
        return self.__is_available
