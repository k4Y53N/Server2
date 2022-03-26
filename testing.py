import os
from pathlib import Path
from src.Detector import Detector
import cv2
from timeit import timeit

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.experimental.set_virtual_device_configuration(
            gpus[0],
            [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=3072)])
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Virtual devices must be set before GPUs have been initialized
        print(e)



p = Path('configs/')
d = Detector(p)
image = cv2.imread('person.jpg')
d.score_threshold = 0.5
d.iou_threshold = 0.5
d.load_model('yolov4-416.json')
result = d.detect(image)

print(timeit('d.detect(image)', globals=globals(), number=10))
# print(timeit('d.detect(image)', globals=globals(), number=10))
