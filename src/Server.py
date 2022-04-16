import logging as log
from threading import Lock
from typing import Tuple, Optional
from time import sleep
from configparser import ConfigParser
from .Connection import Connection, ConnectionBuilder
from .Monitor import Monitor
from .utils.Commands import FRAME, SYS_INFO, CONFIGS, CONFIG
from .utils.util import get_hostname
from .RepeatTimer import RepeatTimer
from .Streamer import Streamer, StreamerBuilder
from .PWMController import PWMController


class ServerBuilder:
    def __init__(self, build_config_file_path):
        config = ConfigParser()
        config.read(build_config_file_path)
        is_ip = config.getboolean('Server', 'ip')
        self.ip = config['Server']['ip'] if is_ip else get_hostname()
        self.port = int(config['Server']['port'])
        self.server_timeout = float(config['Server']['server_timeout'])
        self.client_timeout = float(config['Server']['client_timeout'])
        self.is_show_exc_info = config.getboolean('Server', 'is_show_exc_info')
        self.pwm_speed_port = int(config['PWM']['pwm_speed_port'])
        self.pwm_angle_port = int(config['PWM']['pwm_angle_port'])
        self.pwm_frequency = float(config['PWM']['frequency'])
        self.is_pwm_listen = config.getboolean('PWM', 'is_pwm_listen')
        self.max_fps = int(config['Streamer']['max_fps'])
        self.idle_interval = float(config['Streamer']['idle_interval'])
        self.stream_timeout = float(config['Streamer']['timeout'])
        self.jpg_encode_rate = int(config['Streamer']['jpg_encode_rate'])
        self.yolo_configs_dir = config['Detector']['configs']
        self.is_local_detector = config.getboolean('Detector', 'is_local_detector')
        self.remote_detector_ip = config['Detector']['detect_server_ip']
        self.remote_detector_port = int(config['Detector']['detect_server_port'])

    def get_streamer_builder(self) -> StreamerBuilder:
        streamer_builder = StreamerBuilder()
        streamer_builder.yolo_config_dir = self.yolo_configs_dir
        streamer_builder.max_fps = self.max_fps
        streamer_builder.idle_interval = self.idle_interval
        streamer_builder.stream_timeout = self.stream_timeout
        streamer_builder.jpg_encode_rate = self.jpg_encode_rate
        streamer_builder.is_show_exc_info = self.is_show_exc_info
        streamer_builder.is_local_detector = self.is_local_detector
        streamer_builder.remote_detector_ip = self.remote_detector_ip
        streamer_builder.remote_detector_port = self.remote_detector_port
        return streamer_builder

    def get_connection_builder(self) -> ConnectionBuilder:
        connection_builder = ConnectionBuilder()
        connection_builder.ip = self.ip
        connection_builder.port = self.port
        connection_builder.server_timeout = self.server_timeout
        connection_builder.client_timeout = self.client_timeout
        connection_builder.is_show_exc_info = self.is_show_exc_info
        return connection_builder


class Server(RepeatTimer):
    def __init__(self, builder: ServerBuilder) -> None:
        RepeatTimer.__init__(self, interval=0, name='ServerEvent')
        self.lock = Lock()
        self.serve_address: Optional[Tuple[str, int]] = None
        self.exc_info = builder.is_show_exc_info
        self.last_cmd = None
        self.connection = Connection(builder.get_connection_builder())
        self.monitor = Monitor()
        self.streamer = Streamer(builder.get_streamer_builder())
        self.pwm = PWMController(
            (builder.pwm_speed_port, builder.pwm_angle_port),
            frequency=builder.pwm_frequency,
            is_listen=builder.is_pwm_listen
        )
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
            log.error(f'Event loop was interrupt {E.__class__.__name__}', exc_info=self.exc_info)

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
            log.info(F'RECV CMD: {command}')
            command_key = command.get('CMD', None)
            if command_key not in self.__func_map.keys():
                log.warning(f'Undefined CMD KEY {command_key}')
                return
            self.last_cmd = command
            ret = self.__func_map[command_key](command)
            if ret:
                self.connection.put(ret, address)
        except Exception as E:
            log.error(f'Illegal command {command} cause {E.__class__.__name__}', exc_info=self.exc_info)

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
