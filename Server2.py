import logging as log
from threading import Thread
from unit import Camera
from unit import Connection
from unit import Detector
from unit import Monitor
from unit.utils.Commands import FRAME, SYS_INFO, CONFIGS, CONFIG
from unit.utils.util import get_hostname
from typing import Tuple


class SystemInfo:
    def __init__(self):
        pass


class Server(Thread):

    def __init__(self) -> None:
        Thread.__init__(self)
        self.__is_running = True
        self.__detector = Detector()
        self.__camera = Camera()
        self.__connection = Connection(get_hostname())
        self.__monitor = Monitor()
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
        self.sys_info = SYS_INFO.copy()
        self.__event_thread = Thread(target=self.__event_loop, daemon=True)
        self.__stream_thread = Thread(target=self.__streaming, daemon=True)

    def run(self):
        self.__monitor.set_row_string(0, '%s:%d' % self.__connection.get_server_address())
        self.__connection.start()
        self.__monitor.start()
        self.__event_thread.start()
        self.__stream_thread.start()
        self.__connection.join()
        self.__monitor.join()
        self.__event_thread.join()
        self.__stream_thread.join()

    def __event_loop(self):
        serve_address = self.__connection.get_client_address()
        while self.__connection.is_alive() and self.__is_running:
            command, address = self.__connection.get()
            if address != serve_address:
                self.__reset(address)
                serve_address = address
            if not command:
                continue
            else:
                self.__event(command, address)
        self.close()

    def __event(self, command: dict, address: tuple):
        command_key = command.get('CMD', None)
        if command_key not in self.__func_map.keys():
            return
        ret = self.__func_map[command_key](command)
        if ret:
            self.__connection.put(ret, address)

    def __streaming(self):
        while self.__connection.is_alive() and self.__is_running:
            pass
            # address = self.__connection.get_client_address()
            # # if (not address) or (not self.__camera.is_client_stream()):
            # #     sleep(1)
            # #     continue
            #
            # grab, image = self.__camera.get()
            # if (not grab) or (not image):
            #     sleep(1)
            #     continue
            #
            # if self.__detector.is_client_infer():
            #     ret = self.__vid_encode_infer(image)
            #     self.__connection.put(ret, address)
            # else:
            #     ret = self.__vid_encode(image)
            #     self.__connection.put(ret, address)

    def __vid_encode_infer(self, image) -> dict:
        frame = FRAME.copy()
        encode_thread = self.__camera.get_encode_thread(frame, 'IMAGE', image)
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

    def __reset(self, client_address):
        self.sys_info = SYS_INFO.copy()
        client_address = '%s:%d' % client_address if client_address else None
        self.__monitor.set_row_string(1, client_address)
        self.__camera.reset()
        self.__detector.reset()
        self.sys_info['CAMERA_WIDTH'], self.sys_info['CAMERA_HEIGHT'] = self.__camera.get_resolution()

    def close(self):
        self.__is_running = False
        self.__camera.close()
        self.__connection.close()
        self.__detector.close()
        self.__monitor.close()

    def __exit(self):
        pass

    def __shutdown(self):
        pass

    def __get_sys_info(self, command: dict, *args, **kwargs) -> dict:
        return self.sys_info

    def __get_configs(self, command: dict, *args, **kwargs) -> dict:
        configs = CONFIGS.copy()
        configs.update(self.__detector.get_configs())
        return configs

    def __get_config(self, command: dict, *args, **kwargs) -> dict:
        config = CONFIG.copy()
        config.update(self.__detector.get_config())
        return config

    def __set_stream(self, command: dict, *args, **kwargs) -> None:
        pass
        # set_stream = command.get('STREAM', None)
        # if not set_stream:
        #     return None
        # self.__camera.set_stream(bool(set_stream))
        # if self.__camera.is_client_stream():
        #     if self.__stream_thread.is_alive():
        #         return
        #     try:
        #         self.__stream_thread.start()
        #     except RuntimeError:
        #         self.__stream_thread = Thread(target=self.__streaming, daemon=True)
        #         self.__stream_thread.start()

    def __set_config(self, command: dict, *args, **kwargs) -> None:
        self.__detector.set_config(config=command)
        return None

    def __set_infer(self, command: dict, *args, **kwargs) -> None:
        self.__detector.set_infer(command)
        return None

    def __set_quality(self, command: dict, *args, **kwargs) -> None:
        self.__camera.set_quality(1920, 1080)
        return None

    def __move(self, command: dict, address: Tuple[str, int], *args, **kwargs) -> None:
        pass
        return None


if __name__ == '__main__':
    log.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        level=log.INFO
    )
    server = Server()

    try:
        server.run()
    except (KeyboardInterrupt, Exception) as e:
        log.error(e.__class__.__name__, exc_info=True)
        server.close()
