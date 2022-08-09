import logging as log
import numpy as np
import tensorflow as tf
from pathlib import Path
from threading import Lock
from typing import Union, Dict, Optional
from .core.configer import YOLOConfiger
from .DetectResult import DetectResult
from .ConfigManagerInterface import ConfigManagerInterface
from .Detector import Detector


def load_configer(configs_dir: Union[Path, str], config_suffix='*.json') -> Dict[str, YOLOConfiger]:
    if type(configs_dir) is str:
        configs_dir = Path(configs_dir)

    config_group = {}
    for config_file_path in configs_dir.glob(config_suffix):
        try:
            configer = YOLOConfiger(str(config_file_path))
            config_group[configer.name] = configer
        except KeyError:
            log.warning(f'Parse json file {config_file_path} to YOLO-Configer fail')

    return config_group


class ConfigManager(ConfigManagerInterface):
    def __init__(self, configs_dir: Union[Path, str], is_show_exc_info=True) -> None:
        self.configer_group: Dict[str, YOLOConfiger] = load_configer(configs_dir)
        self.configer: Optional[YOLOConfiger] = None
        self.detector: Optional[Detector] = None
        self.__lock = Lock()
        self.__timeout = 1
        self.__is_available = False
        self.__is_show_exc_info = is_show_exc_info

    def __str__(self):
        with self.__lock:
            configer = self.configer

        if configer is None:
            return '**No Configer Selected**'
        return 'Size: %d, Classes: %s, Score Threshold: %f' % (
            configer.size,
            configer.classes,
            configer.score_threshold
        )

    def set_config(self, config_name):
        configer = self.configer_group.get(config_name)
        if not configer:
            log.warning(f'Config not exist: {config_name}')
            return
        log.info(f'Load model {config_name}')
        acquired = self.__lock.acquire(True, self.__timeout)
        if not acquired:
            log.warning(f'Loading model {config_name} timeout. another model is loading')
            return

        try:
            tf.keras.backend.clear_session()
            self.detector = Detector(configer)
            self.configer = configer
            log.info(f'Loading model {config_name} finish')
        except Exception:
            log.error('Loading model error', exc_info=True)
        finally:
            self.__lock.release()

    def detect(self, image: np.ndarray, is_cv2=True) -> DetectResult:
        acquired = self.__lock.acquire(False)
        if not acquired:
            return DetectResult()
        if self.detector is None:
            self.__lock.release()
            return DetectResult()
        try:
            detect_result = self.detector.detect(image, is_cv2=is_cv2)
            return detect_result
        except Exception:
            log.error(f'Detect image fail', exc_info=self.__is_show_exc_info)
            return DetectResult()
        finally:
            self.__lock.release()

    def reset(self):
        with self.__lock:
            self.configer = None
            self.detector = None
            tf.keras.backend.clear_session()

    def close(self):
        self.reset()
        self.configer_group = {}

    def get_configs(self) -> Dict[str, YOLOConfiger]:
        return self.configer_group

    def get_config(self) -> Optional[YOLOConfiger]:
        return self.configer
