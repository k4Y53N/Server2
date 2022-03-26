from pathlib import Path
from src.Detector import Detector
import cv2
from timeit import timeit
import tensorflow as tf

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    # Restrict TensorFlow to only allocate 1GB of memory on the first GPU
    try:
        tf.config.set_logical_device_configuration(
            gpus[0],
            [tf.config.LogicalDeviceConfiguration(memory_limit=2048)])
        logical_gpus = tf.config.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Virtual devices must be set before GPUs have been initialized
        print(e)

p = Path('configs/')
d = Detector(p)
image = cv2.imread('person.jpg')
d.score_threshold = 0.5
d.iou_threshold = 0.5
d.load_model('yolov4-tiny-416.json')
result = d.detect(image)

print(timeit('d.detect(image)', globals=globals(), number=10))
