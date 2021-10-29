import logging
from threading import Thread
from time import process_time, sleep, time
from unit.Camera import Camera
from unit.Connection import Connection
from unit.PyOLED import PyOLED
from unit.Detector import Detector
from multiprocessing import Pool, cpu_count, TimeoutError
from unit.utils.Frames import FRAME, SYS_INFO, CONFIGS, CONFIG
from unit.utils.util import get_hostname
from typing import Tuple

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO
)

CPUS = cpu_count()


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
        self.__thread = Thread(target=self.__loop, daemon=True)
        self.__stream_thread = Thread(target=self.__streaming, daemon=True)

    def activate(self):
        if self.__thread.is_alive():
            return

        try:
            self.__thread.start()
        except RuntimeError:
            self.__thread = Thread(target=self.__loop, daemon=True)
            self.__thread.start()
            self.__thread.join()
        else:
            self.__thread.join()

    def __loop(self):
        current_address = self.__connection.get_client_address()
        while self.__connection.is_connect():
            command, address = self.__connection.get()
            if address != current_address:
                self.__reset()
                continue
            if command.get('CMD', None) in self.__func_map.keys():
                self.__func_map[command['CMD']](command, address)

    def __streaming(self):
        while self.__camera.is_stream():
            grab, image = self.__camera.get()

            if not (grab and self.__camera.is_stream()):
                sleep(1)
            elif self.__is_infer:
                self.__vid_encode_infer(image)
            else:
                self.__vid_encode(image)

    def __vid_encode_infer(self, image):
        start = time()
        frame = FRAME.copy()
        address = self.__connection.get_client_address()
        with Pool(processes=CPUS) as pool:
            infer_result = pool.apply_async(self.__detector.detect, (image,))
            jpg_result = pool.apply_async(
                self.__camera.get_JPG_base64,
                (image,)
            )

        try:
            infer = infer_result.get()
            jpg = jpg_result.get()
            frame['BBOX'] = infer
            frame['IMAGE'] = jpg
        except Exception:
            return

        self.__connection.put(frame, address)
        process_time = time() - start

        if process_time < self.__camera.delay():
            sleep(self.__camera.delay() - process_time)

    def __vid_encode(self, image):
        start = time()
        frame = FRAME.copy()
        adress = self.__connection.get_client_address()
        with Pool(processes=CPUS) as pool:
            jpg_result = pool.apply_async(
                self.__camera.get_JPG_base64, (image,)
            )

        try:
            jpg = jpg_result.get()
            frame['IMAGE'] = jpg
        except Exception:
            return

        self.__connection.put(frame, adress)
        process_time = time() - start

        if process_time < self.__camera.delay():
            sleep(self.__camera.delay() - process_time)

    def __reset(self):
        self.__camera.reset()
        self.__detector.reset()

    def close(self):
        self.__camera.close()
        self.__connection.close()
        # self.__detector.close()

    def __exit(self):
        pass

    def __shutdown(self):
        pass

    def __get_sys_info(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        info = SYS_INFO.copy()
        info['IS_INFER'] = self.__detector.is_infer()
        info['IS_STREAM'] = self.__camera.is_stream()
        info['WIDTH'], info['HEIGHT'] = self.__camera.get_resolution()
        self.__connection.put(info, address)

    def __set_stream(self, command: dict, address: Tuple[str, int], *args, **kwargs):
        self.__camera.set_stream(command)

        if self.__camera.is_stream():
            if self.__stream_thread.is_alive():
                return
            try:
                self.__stream_thread.start()
            except RuntimeError:
                self.__stream_thread = Thread(
                    target=self.__streaming, daemon=True)
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
