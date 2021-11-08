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
        self.__camera.activate()
        self.__connection.activate()
        self.__pyoled.activate()
        self.__func_map = {
            'RESET': self.__reset,
            'GET_SYS_INFO': self.__get_sys_info,
            'GET_CONFIGS': self.__get_configs,
            'GET_CONFIG': self.__get_config,
            'SET_CONFIG': self.__set_config,
            'SET_INFER': self.__set_infer,
            'SET_STREAM': self.__set_stream,
            'SET_RESOLUTION': self.__set_resolution,
            'MOV': self.__move
        }
        self.__event_thread = Thread(target=self.__event_loop, daemon=True)
        self.__stream_thread = Thread(target=self.__streaming, daemon=True)

    def activate(self):
        if not self.__event_thread.is_alive():
            try:
                self.__event_thread.start()
            except RuntimeError:
                self.__event_thread = Thread(target=self.__event_loop, daemon=True)
                self.__event_thread.start()

        if  not self.__stream_thread.is_alive():
            try:
                self.__stream_thread.start()
            except RuntimeError:
                self.__stream_thread = Thread(target=self.__streaming, daemon=True)
                self.__stream_thread.start()

        if self.__event_thread.is_alive() and self.__stream_thread.is_alive():
            self.__event_thread.join()
            self.__stream_thread.join()

    def __event_loop(self):
        current_address = self.__connection.get_client_address()
        while self.__connection.is_connect():
            command, address = self.__connection.get()
            if address != current_address:
                self.__reset()
                continue
            if not command:
                continue
            if command.get('CMD', None) in self.__func_map.keys():
                self.__func_map[command['CMD']](command, address)

    def __streaming(self):
        while self.__connection.is_connect():
            address = self.__connection.get_client_address()
            if (not address) or (not self.__camera.__is_client_stream()):
                sleep(1)
                continue

            grab, image = self.__camera.get()
            if (not grab) or ( not image):
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

    def __get_sys_info(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        info = SYS_INFO.copy()
        info['IS_INFER'] = self.__detector.is_client_infer()
        info['IS_STREAM'] = self.__camera.is_client_stream()
        info['WIDTH'], info['HEIGHT'] = self.__camera.get_resolution()
        self.__connection.put(info, address)

    def __set_stream(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        self.__camera.set_stream(command)

        if self.__camera.is_client_stream():
            if self.__stream_thread.is_alive():
                return
            try:
                self.__stream_thread.start()
            except RuntimeError:
                self.__stream_thread = Thread(target=self.__streaming, daemon=True)
                self.__stream_thread.start()

    def __get_configs(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        configs = CONFIGS.copy()
        configs.update(self.__detector.get_configs())
        self.__connection.put(configs, address)

    def __get_config(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        config = CONFIG.copy()
        config.update(self.__detector.get_config())
        self.__connection.put(config, address)

    def __set_config(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        self.__detector.set_config(config=command)

    def __set_infer(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        self.__detector.set_infer(command)

    def __set_resolution(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        self.__camera.set_resolution(command)

    def __move(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        pass


if __name__ == '__main__':
    try:
        server = Server()
        server.activate()
    except (KeyboardInterrupt, Exception) as e:
        logging.error(e.__class__.__name__, exc_info=True)
        server.close()
