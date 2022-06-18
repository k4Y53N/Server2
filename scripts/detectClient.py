import sys

sys.path.append('.')
from src.Detector import RemoteConfigManager
import cv2

image = cv2.imread('../person.jpg')

c = RemoteConfigManager('192.168.0.2', 5050, 30, True)
c.set_config('yolov4-416')
print(c.get_configs())
r = c.detect(image)
print(r.boxes)
