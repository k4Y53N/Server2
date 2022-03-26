from pathlib import Path
from src.Detector import Detector
import cv2
from timeit import timeit

p = Path('configs/')
d = Detector(p)
image = cv2.imread('person.jpg')
d.score_threshold = 0.5
d.iou_threshold = 0.5
d.load_model('person-320-noPre.json')
# d.model.save_weights('person-320-noPre.h5')
# d.model.save('checkpoints/person-320-noPre')
result = d.detect(image)

print(timeit('d.detect(image)', globals=globals(), number=10))
# print(timeit('d.detect(image)', globals=globals(), number=10))
