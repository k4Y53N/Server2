import logging as log
from threading import Lock
from pathlib import Path
from typing import Tuple, Union
from time import sleep
from src.Connection import Connection
from src.Monitor import Monitor
from src.utils.Commands import FRAME, SYS_INFO, CONFIGS, CONFIG
from src.utils.util import get_hostname
from src.RepeatTimer import RepeatTimer
from src.Streamer import Streamer
from src.PWMController import PWMController


class Server(RepeatTimer):
    def __init__(self, config_dir: Path, port=0, exc_info=False, pwm_listen=False) -> None:
        RepeatTimer.__init__(self, interval=0, name='ServerEvent')
        self.lock = Lock()
        self.serve_address: Union[Tuple[str, int], None] = None
        self.exc_info = exc_info
        self.last_cmd = None
        self.connection = Connection(get_hostname(), port, exc_info=exc_info)
        self.monitor = Monitor()
        self.streamer = Streamer(config_dir, max_fps=30, idle_interval=1, timeout=10, exc_info=exc_info)
        self.pwm = PWMController((37, 38), frequency=0.25, is_listen=pwm_listen)
        self.stream_repeat_timer = RepeatTimer(target=self.streaming, interval=0, name='Streaming')
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

    def __str__(self):
        return f'Last CMD:{self.last_cmd}, Serve Address: {self.serve_address}' + '\n%s\n%s\n%s' % (
            self.connection,
            self.pwm,
            self.streamer
        )

    def init_phase(self):
        self.monitor.set_row_string(0, '%s:%d' % self.connection.get_server_address())
        self.connection.start()
        self.monitor.start()
        self.streamer.start()
        self.stream_repeat_timer.start()
        self.pwm.start()

    def execute_phase(self):
        try:
            if not self.connection.is_connect():
                self.close()
                return
            command, address = self.connection.get()
            if address != self.serve_address:
                self.__reset(address)
            if not command:
                return
            self.__event(command, address)
        except Exception as E:
            log.error(f'Event loop was interrupt {E.__class__.__name__}', exc_info=True)

    def close_phase(self):
        self.connection.close()
        self.monitor.close()
        self.streamer.close()
        self.stream_repeat_timer.close()
        self.pwm.close()
        self.connection.join()
        self.monitor.join()
        self.streamer.join()
        self.stream_repeat_timer.join()
        self.pwm.join()
        log.info('Server closed')

    def __event(self, command: dict, address: tuple):
        try:
            command_key = command.get('CMD', None)
            if command_key not in self.__func_map.keys():
                log.warning(f'Undefined CMD KEY {command_key}')
                return
            self.last_cmd = command
            ret = self.__func_map[command_key](command)
            if ret:
                self.connection.put(ret, address)
        except Exception as E:
            log.error(f'Illegal command {command} cause {E.__class__.__name__}', exc_info=True)

    def streaming(self, interval=0.5):
        with self.lock:
            address = self.serve_address
        if not address:
            sleep(interval)
            return
        stream_frame = self.streamer.get()
        if not stream_frame.is_available():
            return
        frame = FRAME.copy()
        frame['IMAGE'] = stream_frame.b64image if stream_frame.b64image else ''
        frame['BBOX'] = stream_frame.boxes
        frame['CLASS'] = stream_frame.classes
        self.connection.put(frame, address)

    def __reset(self, client_address):
        with self.lock:
            self.serve_address = client_address
            self.streamer.reset()
        self.serve_address = client_address
        self.last_cmd = None
        client_address = '%s:%d' % client_address if client_address else None
        self.monitor.set_row_string(1, client_address)

    def __exit(self):
        pass

    def __shutdown(self):
        pass

    def __get_sys_info(self, command: dict, *args, **kwargs) -> dict:
        log.info('Get System Information')
        sys_info = SYS_INFO.copy()
        sys_info['IS_INFER'] = self.streamer.is_infer()
        sys_info['IS_STREAM'] = self.streamer.is_stream()
        sys_info['CAMERA_WIDTH'], SYS_INFO['CAMERA_HEIGHT'] = self.streamer.get_quality()
        return sys_info

    def __get_configs(self, command: dict, *args, **kwargs) -> dict:
        log.info('Get configs')
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
        log.info('Get Config')
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
        log.info(f'Set Stream: {is_stream}')
        self.streamer.set_stream(is_stream)

    def __set_config(self, command: dict, *args, **kwargs) -> None:
        config_name = command.get('CONFIG')
        log.info(f'Set Config: {config_name}')
        self.streamer.set_config(config_name)

    def __set_infer(self, command: dict, *args, **kwargs) -> None:
        is_infer = bool(command.get('INFER'))
        log.info(f'Set Infer: {is_infer}')
        self.streamer.set_infer(is_infer)

    def __set_quality(self, command: dict, *args, **kwargs) -> None:
        width = int(command.get('WIDTH', 0))
        height = int(command.get('HEIGHT', 0))
        log.info(f'Set Quality: W = {width}, H = {height}')
        if 100 < width < 4196 or 100 < height < 4196:
            return
        self.streamer.set_quality(width, height)

    def __move(self, command: dict, *args, **kwargs) -> None:
        r = command.get('R', 0)
        theta = command.get('THETA', 90)
        self.pwm.set(r, theta)


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
