from pathlib import Path
from threading import Thread, Lock
from .utils.Commands import CONFIGS
import numpy as np
import tensorflow as tf
import json

_config_suffix = '*.json'


def load_configs(config_dir: Path):
    configs = CONFIGS.copy()
    for p in config_dir.glob(_config_suffix):
        with p.open() as f:
            config = json.load(f)

        configs['CONFIGS'][config.name] = {
            'SIZE': config['SIZE'],
            'MODEL_TYPE': config['model_type'],
            'TINY': config['TINY'],
            'CLASSES': config['YOLO']['CLASSES']
        }
    return configs


class Detector:
    def __init__(self, config_dir: Path) -> None:
        self.configs = load_configs(config_dir)
        self.lock = Lock()
        self.model = None
        self.size = None
        self.classes = None

    def get_configs(self, *args, **kwargs) -> dict:
        return self.configs

    def get_config(self, config_name):
        return self.configs['CONFIGS'].get(config_name, {})

    def set_config(self, config_name: str):
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
    pass
