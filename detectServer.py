import cv2
import numpy as np
import logging as log
from base64 import b64decode
from typing import Optional
from src.Detector.ConfigManager import ConfigManager
from src.Detector.ConfigManagerAPI import RESULT, CONFIG, CONFIGS
from src.Server import Server
from src.utils.util import get_hostname


def decode_b64image(b64image: str) -> Optional[np.ndarray]:
    buf_image = b64decode(b64image)
    image = cv2.imdecode(np.frombuffer(buf_image, dtype=np.uint8), cv2.IMREAD_COLOR)
    return image


log.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=log.INFO,
)

s = Server(
    ip=get_hostname(),
    port=5050,
    max_connection=1,
    is_show_exc_info=True
)
detector = ConfigManager('./configs/', True, )


@s.response('SET_CONFIG', detector)
def load_model(message: dict, d: ConfigManager):
    log.info('SET_CONFIG')
    config_name = message.get('CONFIG_NAME')
    d.set_config(config_name)


@s.response('DETECT', detector)
def detect(message: dict, d: ConfigManager):
    log.info('Detect image')
    result = RESULT.copy()
    b64image = message.get('IMAGE', '')
    if len(b64image) < 1:
        return result
    image = decode_b64image(b64image)
    detect_result = d.detect(image, is_cv2=True)
    result['BBOX'] = detect_result.boxes
    result['CLASS'] = detect_result.classes
    result['SCORE'] = detect_result.scores
    return result


@s.response('RESET', detector)
def reset(message, d: ConfigManager):
    log.info('Reset')
    d.reset()


@s.response('CLOSE')
def close(message, d: ConfigManager):
    log.info('close')
    d.close()
    raise RuntimeError('Close Detector')


@s.response('GET_CONFIG', detector)
def get_config(message, d: ConfigManager):
    log.info('Get config')
    config = CONFIG.copy()
    configer = d.get_config()
    if configer is None:
        return config
    config['CONFIG_NAME'] = configer.name
    config['size'] = configer.size
    config['MODEL_TYPE'] = configer.model_type
    config['TINY'] = configer.tiny
    config['CLASSES'] = configer.classes
    return config


@s.response('GET_CONFIGS', detector)
def get_configs(message, d: ConfigManager):
    log.info('Get configs')
    configs = CONFIGS.copy()

    configs['CONFIGS'] = {
        k: v.config
        for k, v in d.configer_group.items()
    }
    return configs


if __name__ == '__main__':
    s.run()
