from .Connection import ServerConnection
from .LocalDetector import LocalDetector
from .Commands import RESULT, CONFIG, CONFIGS
from pathlib import Path
from typing import Optional
from base64 import b64decode
import logging as log
import numpy as np
import cv2


def decode_b64image(b64image: str) -> Optional[np.ndarray]:
    buf_image = b64decode(b64image)
    image = cv2.imdecode(np.frombuffer(buf_image, dtype=np.uint8), cv2.IMREAD_COLOR)
    return image


class Disconnect(Exception):
    pass


class DetectServer(ServerConnection):
    def __init__(self, ip, port, config_path: Path):
        ServerConnection.__init__(self, ip, port)
        self.detector = LocalDetector(config_path)
        self.is_running = True
        self.func_map = {
            'LOAD_MODEL': self.load_model,
            'DETECT': self.detect,
            'RESET': self.reset,
            'CLOSE': self.server_close,
            'GET_CONFIG': self.get_config,
            'GET_CONFIGS': self.get_configs
        }

    def active(self):
        log.info(f'Server address => %s:%s' % self.socket.getsockname())
        log.info('Detect Server activate')
        log.info('Waiting Connect...')
        try:
            client, address = self.socket.accept()
            self.handle_client(client, address)
            client.close()
        except Disconnect as DC:
            log.info('Client disconnect')
        except(KeyboardInterrupt, Exception) as E:
            log.error('Get exception', exc_info=True)
        finally:
            self.close()
            log.info('Server close...')

    def handle_client(self, client, address):
        log.info(f'Client address => {address[0]}:{address[1]}')
        while self.is_running:
            try:
                self.event(client)
            except Exception as E:
                client.close()
                raise E

    def event(self, client):
        message = self.receive_message(client)
        cmd = message.get('CMD')
        if cmd not in self.func_map.keys():
            return
        ret = self.func_map[cmd](message)
        if ret:
            self.send_message(client, ret)

    def load_model(self, message: dict) -> None:
        config_name = message.get('CONFIG_NAME')
        log.info(config_name)
        self.detector.load_model(config_name)

    def detect(self, message: dict) -> dict:
        result = RESULT.copy()
        b64image = message.get('IMAGE', '')
        if len(b64image) < 1:
            return result
        image = decode_b64image(b64image)
        detect_result = self.detector.detect(image, is_cv2=True)
        result['BBOX'] = detect_result.boxes
        result['CLASS'] = detect_result.classes
        result['SCORE'] = detect_result.scores
        return result

    def reset(self, message: dict) -> None:
        self.detector.reset()

    def server_close(self, message: dict) -> None:
        raise Disconnect('Client disconnect')

    def close(self) -> None:
        super().close()
        self.is_running = False

    def get_config(self, message: dict) -> dict:
        config = CONFIG.copy()
        configer = self.detector.configer
        if configer is None:
            return config
        config['CONFIG'] = configer.config
        return config

    def get_configs(self, message: dict) -> dict:
        configs = CONFIGS.copy()
        configs['CONFIGS'] = {
            key: item.config
            for key, item in self.detector.configer_group.items()
        }
        return configs
