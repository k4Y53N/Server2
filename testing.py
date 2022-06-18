import cv2
import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    # Restrict TensorFlow to only allocate 1GB of memory on the first GPU
    try:
        tf.config.experimental.set_virtual_device_configuration(
            gpus[0],
            [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=3072)])
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Virtual devices must be set before GPUs have been initialized
        print(e)

from pathlib import Path
from src.Detector.ConfigManager import ConfigManager
# from timeit import timeit

p = Path('configs/')
d = ConfigManager(p)
image = cv2.imread('person.jpg')
d.__score_threshold = 0.1
d.__iou_threshold = 0.5
d.set_config('yolov4-416.json')
# d.model.save_weights('person-320-noPre.h5')
# d.model.save('checkpoints/person-320-noPre')
result = d.detect(image)
print(result.boxes)
# print(timeit('d.detect(image)', globals=globals(), number=10))
# print(timeit('d.detect(image)', globals=globals(), number=10))
