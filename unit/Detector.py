import json
from pathlib import Path
import numpy as np
from utils.util import nowait
from utils.Frames import CONFIGS

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
