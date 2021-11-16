import logging
from threading import Thread
from time import sleep
from unit.Camera import Camera
from unit.Connection import Connection
from unit.PyOLED import PyOLED
from unit.Detector import Detector
from unit.utils.Commands import FRAME, SYS_INFO, CONFIGS, CONFIG
from unit.utils.util import get_hostname
from typing import Tuple

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO
)


class Server:

    def __init__(self) -> None:
        self.__detector = Detector()
        self.__camera = Camera()
        self.__connection = Connection(get_hostname())
        self.__pyoled = PyOLED(self.__connection)
        self.__func_map = {
            'RESET': self.__reset,
            'GET_SYS_INFO': self.__get_sys_info,
            'GET_CONFIGS': self.__get_configs,
            'GET_CONFIG': self.__get_config,
            'SET_CONFIG': self.__set_config,
            'SET_INFER': self.__set_infer,
            'SET_STREAM': self.__set_stream,
            'SET_QUALITY': self.__set_quality,
            'MOV': self.__move
        }
        self.__event_thread = Thread(target=self.__event_loop, daemon=True)
        self.__stream_thread = Thread(target=self.__streaming, daemon=True)

    def activate(self):
        self.__camera.activate()
        self.__connection.activate()
        self.__pyoled.activate()
        if not self.__event_thread.is_alive():
            try:
                self.__event_thread.start()
            except RuntimeError:
                self.__event_thread = Thread(target=self.__event_loop, daemon=True)
                self.__event_thread.start()

        if not self.__stream_thread.is_alive():
            try:
                self.__stream_thread.start()
            except RuntimeError:
                self.__stream_thread = Thread(target=self.__streaming, daemon=True)
                self.__stream_thread.start()

        if self.__event_thread.is_alive() and self.__stream_thread.is_alive():
            self.__event_thread.join()
            self.__stream_thread.join()

    def __event_loop(self):
        serve_address = self.__connection.get_client_address()
        while self.__connection.is_connect():
            command, address = self.__connection.get()
            if address != serve_address:
                self.__reset()
                serve_address = address
            if not command:
                continue
            else:
                self.__event(command, address)

    def __event(self, command: dict, address: tuple) -> None:
        command_key = command.get('CMD', None)
        if command_key not in self.__func_map.keys():
            return None
        command_function = self.__func_map[command_key]
        ret = command_function(command)
        if ret:
            self.__connection.put(ret, address)

        return None

    def __streaming(self):
        while self.__connection.is_connect():
            address = self.__connection.get_client_address()
            if (not address) or (not self.__camera.is_client_stream()):
                sleep(1)
                continue

            grab, image = self.__camera.get()
            if (not grab) or (not image):
                sleep(1)
                continue

            if self.__detector.is_client_infer():
                ret = self.__vid_encode_infer(image)
                self.__connection.put(ret, address)
            else:
                ret = self.__vid_encode(image)
                self.__connection.put(ret, address)

    def __vid_encode_infer(self, image) -> dict:
        frame = FRAME.copy()
        encode_thread = self.__camera.encode_thread(frame, 'IMAGE', image)
        infer_thread = self.__detector.infer_thread(frame, 'BBOX', image)
        encode_thread.start()
        infer_thread.start()
        encode_thread.join()
        infer_thread.join()
        return frame

    def __vid_encode(self, image) -> dict:
        frame = FRAME.copy()
        self.__camera.encode(frame, 'IMAGE', image)
        return frame

    def __reset(self):
        self.__camera.reset()
        self.__detector.reset()

    def close(self):
        self.__camera.close()
        self.__connection.close()
        self.__detector.close()

    def __exit(self):
        pass

    def __shutdown(self):
        pass

    def __get_sys_info(self, command: dict, *args, **kwargs) -> dict:
        info = SYS_INFO.copy()
        info['IS_INFER'] = self.__detector.is_client_infer()
        info['IS_STREAM'] = self.__camera.is_client_stream()
        info['WIDTH'], info['HEIGHT'] = self.__camera.get_resolution()
        return info

    def __get_configs(self, command: dict, *args, **kwargs) -> dict:
        configs = CONFIGS.copy()
        configs.update(self.__detector.get_configs())
        return configs

    def __get_config(self, command: dict, *args, **kwargs) -> dict:
        config = CONFIG.copy()
        config.update(self.__detector.get_config())
        return config

    def __set_stream(self, command: dict, *args, **kwargs) -> None:
        set_stream = command.get('STREAM', None)
        if not set_stream:
            return None
        self.__camera.set_stream(bool(set_stream))
        if self.__camera.is_client_stream():
            if self.__stream_thread.is_alive():
                return
            try:
                self.__stream_thread.start()
            except RuntimeError:
                self.__stream_thread = Thread(target=self.__streaming, daemon=True)
                self.__stream_thread.start()

    def __set_config(self, command: dict, *args, **kwargs) -> None:
        self.__detector.set_config(config=command)
        return None

    def __set_infer(self, command: dict, *args, **kwargs) -> None:
        self.__detector.set_infer(command)
        return None

    def __set_quality(self, command: dict, *args, **kwargs) -> None:
        self.__camera.set_quality(command)
        return None

    def __move(self, command: dict, address: Tuple[str, int], *args, **kwargs) -> None:
        pass
        return None


if __name__ == '__main__':
    server = Server()

    try:
        server.activate()
    except (KeyboardInterrupt, Exception) as e:
        logging.error(e.__class__.__name__, exc_info=True)
        server.close()
