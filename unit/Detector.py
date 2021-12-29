import json
from pathlib import Path
import numpy as np
from threading import Thread
from utils.Commands import CONFIGS

configs_dir = Path('../configs')
file_suffix = '*.json'


class Detector:
    def __init__(self) -> None:
        self.configs = self.load_configs()

    @staticmethod
    def load_configs(*args, **kwargs):
        configs = CONFIGS.copy()

        for PATH in configs_dir.glob(file_suffix):
            with PATH.open() as f:
                config = json.load(f)

            configs['CONFIGS'][PATH.name] = {
                'SIZE': config['size'],
                'MODEL_TYPE': config['model_type'],
                'TINY': config['tiny'],
                'CLASSES': config['YOLO']['CLASSES'],
            }

        return configs

    def get_configs(self, *args, **kwargs) -> dict:
        return self.configs

    def get_config(self):
        pass

    def set_config(self, command: dict, *args, **kwargs):
        pass

    def set_infer(self, command: dict, *args, **kwargs):
        pass

    def infer_thread(self, dest_dic: dict, dic_key: str, image, *args):
        return Thread(target=self.infer, args=args)

    def infer(self, dest_dic: dict, dic_key: str, image: np.ndarray, *args):
        try:
            dest_dic[dic_key] = self.detect(image)
        except Exception:
            dest_dic[dic_key] = []

    def detect(self, image):
        pass

    def __load_model(self, config):
        # TODO: ONLY USE LOAD_WEIGHT
        pass

    def reset(self):
        pass

    def close(self):
        pass


if __name__ == '__main__':
    print(Detector.load_configs())
