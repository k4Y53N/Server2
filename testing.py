import os

os.environ['CUDA_VISIBLE_DEVICES'] = '1'
from pathlib import Path
from src.Detector import Detector
import cv2
from timeit import timeit
import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)
p = Path('configs/')
d = Detector(p)
image = cv2.imread('person.jpg')
d.score_threshold = 0.5
d.iou_threshold = 0.5
d.load_model('yolov4-tiny-416.json')
result = d.detect(image)

print(timeit('d.detect(image)', globals=globals(), number=10))
print(timeit('d.detect(image)', globals=globals(), number=10))
