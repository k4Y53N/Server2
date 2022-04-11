from .DetectResult import DetectResult
from .core import YOLOConfiger
from typing import Dict, Optional
import numpy as np


class DetectorInterface:
    def load_model(self, config_name):
        pass

    def detect(self, image: np.ndarray) -> DetectResult:
        pass

    def reset(self):
        pass

    def close(self):
        pass

    def get_configs(self) -> Dict[str, YOLOConfiger]:
        pass

    def get_config(self) -> Optional[YOLOConfiger]:
        pass
