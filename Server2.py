import logging as log
from threading import Thread, Lock
from pathlib import Path
from typing import Tuple, Union
from time import sleep
from src.Connection import Connection
from src.Monitor import Monitor
from src.utils.Commands import FRAME, SYS_INFO, CONFIGS, CONFIG
from src.utils.util import get_hostname
from src.RepeatTimer import RepeatTimer
from src.Streamer import Streamer


class Server(Thread):
    def __init__(self, configs_path: Path, port=0, exc_info=False) -> None:
        Thread.__init__(self)
        self.is_running = True
        self.__connection = Connection(get_hostname(), port, exc_info=exc_info)
        self.__monitor = Monitor()
        self.streamer = Streamer(configs_path)
        self.serve_address: Union[Tuple[str, int], None] = None
        self.lock = Lock()
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
        self.exc_info = exc_info
        self.is_running = True
        self.__event_thread = Thread(target=self.__event_loop, daemon=True)
        self.stream_repeat_timer = RepeatTimer(target=self.streaming, interval=0)

    def run(self):
        self.__monitor.set_row_string(0, '%s:%d' % self.__connection.get_server_address())
        self.__connection.start()
        self.__monitor.start()
        self.__event_thread.start()
        self.streamer.start()
        self.stream_repeat_timer.start()
        self.__connection.join()
        self.__monitor.join()
        self.__event_thread.join()
        self.streamer.join()
        self.stream_repeat_timer.join()

    def __event_loop(self):
        try:
            while self.__connection.is_connect() and self.is_running:
                command, address = self.__connection.get()
                if address != self.serve_address:
                    self.__reset(address)
                if not command:
                    continue
                self.__event(command, address)
            log.info('Service finish')
        except Exception as E:
            log.error(f'Event loop was interrupt {E.__class__.__name__}', exc_info=True)
        finally:
            self.close()

    def __event(self, command: dict, address: tuple):
        try:
            command_key = command.get('CMD', None)
            if command_key not in self.__func_map.keys():
                log.warning(f'Undefined CMD KEY {command_key}')
                return
            ret = self.__func_map[command_key](command)
            if ret:
                self.__connection.put(ret, address)
        except Exception as E:
            log.error(f'Illegal command {command} cause {E.__class__.__name__}', exc_info=True)

    def streaming(self, interval=0.2):
        acquired = self.lock.acquire(False)
        address = self.serve_address
        if not acquired or not address:
            sleep(interval)
            return
        try:
            stream_frame = self.streamer.get()
            frame = FRAME.copy()
            frame['IMAGE'] = stream_frame.b64image
            frame['BBOX'] = stream_frame.boxes
            frame['CLASS'] = stream_frame.classes
            self.__connection.put(frame, address)
        finally:
            self.lock.release()

    def __reset(self, client_address):
        with self.lock:
            self.serve_address = client_address
            self.streamer.reset()

        client_address = '%s:%d' % client_address if client_address else None
        self.__monitor.set_row_string(1, client_address)

    def close(self):
        self.is_running = False
        self.__connection.close()
        self.__monitor.close()
        self.streamer.close()
        self.stream_repeat_timer.close()

    def __exit(self):
        pass

    def __shutdown(self):
        pass

    def __get_sys_info(self, command: dict, *args, **kwargs) -> dict:
        sys_info = SYS_INFO.copy()
        sys_info['IS_INFER'] = self.streamer.is_infer()
        sys_info['IS_STREAM'] = self.streamer.is_stream()
        sys_info['CAMERA_WIDTH'], SYS_INFO['CAMERA_HEIGHT'] = self.streamer.get_quality()
        return sys_info

    def __get_configs(self, command: dict, *args, **kwargs) -> dict:
        configs = CONFIGS.copy()
        configs['CONFIGS'] = {
            key: {
                'SIZE': val.size,
                'MODEL_TYPE': val.model_type,
                'TINY': val.tiny,
                'CLASSES': val.classes
            }
            for key, val in self.streamer.get_configs().items()
        }
        return configs

    def __get_config(self, command: dict, *args, **kwargs) -> dict:
        config = CONFIG.copy()
        yolo_config = self.streamer.get_config()
        if yolo_config is None:
            config['CONFIG_NAME'] = None
            config['SIZE'] = 0
            config['MODEL_TYPE'] = None
            config['TINY'] = False
            CONFIG['CLASSES'] = []
        else:
            config['CONFIG_NAME'] = yolo_config.name
            config['SIZE'] = yolo_config.size
            config['MODEL_TYPE'] = yolo_config.model_type
            config['tiny'] = yolo_config.tiny
            config['CLASSES'] = yolo_config.classes

        return config

    def __set_stream(self, command: dict, *args, **kwargs) -> None:
        is_stream = bool(command.get('STREAM'))
        self.streamer.set_stream(is_stream)

    def __set_config(self, command: dict, *args, **kwargs) -> None:
        config_name = command.get('CONFIG')
        self.streamer.set_config(config_name)

    def __set_infer(self, command: dict, *args, **kwargs) -> None:
        is_infer = bool(command.get('INFER'))
        self.streamer.set_infer(is_infer)

    def __set_quality(self, command: dict, *args, **kwargs) -> None:
        width = int(command.get('WIDTH', 0))
        height = int(command.get('HEIGHT', 0))
        if 100 < width < 4196 or 100 < height < 4196:
            return
        self.streamer.set_quality(width, height)

    def __move(self, command: dict, *args, **kwargs) -> None:
        pass


if __name__ == '__main__':
    log.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        level=log.INFO
    )
    configs_path = Path('configs')
    server = Server(configs_path, exc_info=True)

    try:
        server.run()
    except (KeyboardInterrupt, Exception) as e:
        log.error(e.__class__.__name__, exc_info=True)
    finally:
        server.close()
