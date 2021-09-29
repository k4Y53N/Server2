import sys
sys.path.append('./')
import json
from utils.Frames import CONFIGS
from threading import Lock
from pathlib import Path
import logging
import os
import numpy as np
import cv2

# import tensorflow as tf
# from core.yolov4 import YOLO, decode, filter_boxes
# import core.utils as utils
from utils.util import nowait
# from utils.Frames import CONFIG

configs_dir = Path('./configs')
file_endname = '*.json'


class Detector:
    def __init__(self) -> None:
        self.__is_infer = False

    def get_configs(self, command: dict = {}, *args, **kwargs) -> dict:
        configs = CONFIGS.copy()

        for path in configs_dir.glob(file_endname):

            with path.open() as f:
                config = json.load(f)

            configs['CONFIGS'][path.name] = {
                'SIZE': config['size'],
                'MODEL_TYPE': config['model_type'],
                'TINY': config['tiny'],
                'CLASSES': config['YOLO']['CLASSES'],
            }

        return configs

    def get_config(self, command: dict = {}, *args, **kwargs):
        pass

    def set_config(self, command: dict = {}, *args, **kwargs):
        pass

    def set_infer(self, command: dict = {}, *args, **kwargs):
        pass

    def is_infer(self):
        return self.__is_infer

    def detect(self, image: np.ndarray):
        pass

    @nowait
    def __load_model(self, config):
        # TODO: ONLY USE LOAD_WEIGHT
        pass

    def reset(self):
        pass

    def close(self):
        pass


if __name__ == '__main__':
    pass
    # det = Detector()
    # with open('./utils/CONFIGS.json', 'w') as f:
    #     json.dump(det.get_configs({}), f)


# class Detector:
#     def __init__(self):
#         self.__is_model_ready = False
#         self.__is_infer = False
#         self.__config_name = None
#         self.__model = None
#         self.__model_type = None  # yolov4 or yolov3
#         self.__is_tiny = False
#         self.__frame_work = None  # tf, tf-lite, trt
#         self.__input_shape = None
#         self.__classes = None
#         self.__lock = Lock()

#     def reset(self):
#         with self.__lock:
#             self.__is_model_ready = False
#             self.__is_infer = False
#             self.__config_name = None
#             self.__model = None
#             self.__model_type = None  # yolov4 or yolov3
#             self.__is_tiny = False
#             self.__frame_work = None  # tf, tf-lite, trt
#             self.__input_shape = None
#             self.__classes = None
#             tf.keras.backend.clear_session()

#     def get_configs(self):
#         pass

#     def get_config(self, **kwargs):
#         config = CONFIG.copy()
#         config['CONFIG_NAME'] = ''
#         config['CLASSES'] = self.__classes
#         config['MODEL_TYPE'] = self.__model_type
#         config['FRAME_WORK'] = self.__frame_work
#         return config

#     @nowait
#     def set_config(self, config={}):
#         if self.__lock.locked():
#             return
#         with self.__lock:
#             self.__is_model_ready = False
#             config_name = config.get('CONFIG', None)
#             if config_name:
#                 config_path = Path(configs_dir) / config_name
#                 if config_path.is_file() and str(config_path).endswith(config_file_name_endswith):
#                     self.__load_config(config_path)

#     def __load_config(self, config_file_path):
#         with open(config_file_path, 'r') as f:
#             config = json.load(f)
#         model_type = config.get('model_type', None)

#         if model_type == 'tf':
#             weight_path = Path(config.get('weight_path', ''))
#             if weight_path.is_file():
#                 self.__build_model(config)
#             else:
#                 self.__load_model(config)
#         else:
#             self.__load_model(config)

#     def set_infer(self, command={}, *args, **kwargs):
#         self.__is_infer = command['IS_INFER']

#     def is_infer(self):
#         return self.is_infer

#     def is_ready(self):
#         return self.__is_model_ready and self.__is_infer

#     def close(self):
#         pass

#     def detect(self, image: np.ndarray):
#         original_shape = image.shape[:2]
#         image = self.__normalization(image)
#         pred = self.__model(image)
#         boxes, scores, classes, detection = self.nms(pred)

#     def __normalization(self, image: np.ndarray):
#         image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#         image = cv2.resize(image, (self.__input_shape, self.__input_shape))
#         image = image.astype(np.float32)
#         image /= 255.
#         image = np.expand_dims(image, axis=0)
#         return image

#     def nms(self, pred_box):
#         """
#         non max suppression
#         :param pred_box:
#         :return:boxes, scores, classes, valid_detections
#         """
#         batch_size = pred_box.shape[0]
#         boxes, pred_conf = [
#             (pred[:, 0:4], pred[:, 4:],)
#             for pred in pred_box
#         ][0]

#         return tf.image.combined_non_max_suppression(
#             boxes=tf.reshape(boxes, (batch_size, boxes.shape[0], 1, 4)),
#             scores=tf.reshape(
#                 pred_conf, (batch_size, pred_conf.shape[0], pred_conf.shape[1])),
#             max_output_size_per_class=15,
#             max_total_size=20,
#             iou_threshold=0.5,
#             score_threshold=0.25
#         )

#     def __build_model(self, config={}):
#         tf.keras.backend.clear_session()
#         SIZE = config['size']
#         FRAME_WORK = config['frame_work']
#         STRIDES, ANCHORS, NUM_CLASS, XYSCALE = utils.load_config(config)
#         input_layer = tf.keras.layers.Input([SIZE, SIZE, 3])
#         feature_maps = YOLO(input_layer, NUM_CLASS, config['model_type'], config['tiny'])
#         bbox_tensors = []
#         prob_tensors = []
#         if config['tiny']:
#             for i, fm in enumerate(feature_maps):
#                 if i == 0:
#                     output_tensors = decode(fm, SIZE // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FRAME_WORK)
#                 else:
#                     output_tensors = decode(fm, SIZE // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FRAME_WORK)
#                 bbox_tensors.append(output_tensors[0])
#                 prob_tensors.append(output_tensors[1])
#         else:
#             for i, fm in enumerate(feature_maps):
#                 if i == 0:
#                     output_tensors = decode(fm, SIZE // 8, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FRAME_WORK)
#                 elif i == 1:
#                     output_tensors = decode(fm, SIZE // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FRAME_WORK)
#                 else:
#                     output_tensors = decode(fm, SIZE // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FRAME_WORK)
#                 bbox_tensors.append(output_tensors[0])
#                 prob_tensors.append(output_tensors[1])
#         pred_bbox = tf.concat(bbox_tensors, axis=1)
#         pred_prob = tf.concat(prob_tensors, axis=1)
#         if FRAME_WORK == 'tflite':
#             pred = (pred_bbox, pred_prob)
#         else:
#             boxes, pred_conf = filter_boxes(pred_bbox, pred_prob, score_threshold=config['score_threshold'],
#                                             input_shape=tf.constant([SIZE, SIZE]))
#             pred = tf.concat([boxes, pred_conf], axis=-1)

#         self.__model = tf.keras.Model(input_layer, pred)
#         self.__model.load_weights(config['weight_path'])
#         self.__input_shape = SIZE
#         self.__model_type = config['model_type']
#         self.__frame_work = FRAME_WORK
#         self.__is_tiny = config['tiny']
#         self.__classes = config['YOLO']['CLASSES']
#         self.__is_model_ready = True

#     def __load_model(self, config={}):
#         tf.keras.backend.clear_session()
#         self.__model = tf.keras.models.load_model(config['model_path'], compile=False)
#         self.__input_shape = config['size']
#         self.__model_type = config['model_type']
#         self.__frame_work = config['frame_work']
#         self.__is_tiny = config['tiny']
#         self.__classes = config['YOLO']['CLASSES']
#         self.__is_model_ready = True
#         logging.info('Load Model %s'.format(config['model_path'],))

#     def reset(self):
#         pass
