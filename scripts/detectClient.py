import sys
sys.path.append('.')
from src.Detector import RemoteDetector
import cv2

image = cv2.imread('../person.jpg')

c = RemoteDetector('192.168.0.2', 5050, 30, True)
c.load_model('yolov4-416')
print(c.get_configs())
r = c.detect(image)
print(r.boxes)

