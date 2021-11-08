import json
from pathlib import Path
import numpy as np
from threading import Thread
from utils.util import nowait
from utils.Commands import CONFIGS


configs_dir = Path('./configs')
file_endname = '*.json'


class Detector:
    def __init__(self) -> None:
        self.__is_client_infer = False

    def get_configs(self, command: dict = {}, *args, **kwargs) -> dict:
        configs = CONFIGS.copy()

        for PATH in configs_dir.glob(file_endname):
            with PATH.open() as f:
                config = json.load(f)

            configs['CONFIGS'][PATH.name] = {
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

    def is_client_infer(self):
        return self.__is_client_infer

    def infer_thread(self, dest_dic: dict, dic_key: str, image, *args):
        return Thread(target=self.infer, args=args)

    def infer(self ,dest_dic: dict, dic_key: str, image: np.ndarray, *args):
        dest_dic[dic_key] = self.detect(image)

    def detect(self, image):
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
