import logging as log
from configparser import ConfigParser
from socket import socket, AF_INET, SOCK_STREAM
from typing import Optional
from .ClientHandler import AsyncClientHandler, EventHandler
from .RepeatTimer import RepeatTimer
from .utils.util import get_hostname
from .Streamer import StreamerBuilder


class ServerConfiger:
    max_connection = 1
    server_timeout = 0
    client_timeout = 0
    is_show_exc_info = False


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


class Server(RepeatTimer):
    def __init__(self, ip, port):
        RepeatTimer.__init__(self)
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind((ip, port))
        self.ip, self.port = self.server_sock.getsockname()
        self.event_handler = EventHandler()
        self.configer = ServerConfiger()
        self.client_handler: Optional[AsyncClientHandler] = None

    def __str__(self):
        s = ''
        s += f'Server address => {self.ip}:{self.port}'
        handler = self.client_handler
        if handler is not None:
            s += f'\n{handler}'
        else:
            s += '\nNo Client Connected'
        return s

    def init_phase(self):
        self.server_sock.listen(self.configer.max_connection)
        log.info(f'IP ==> {self.ip} port ==> {self.port}')

    def execute_phase(self):
        try:
            log.info('Waiting Client connect......')
            client, address = self.server_sock.accept()
            with client:
                handler = AsyncClientHandler(client, self.event_handler)
                self.client_handler = handler
                handler.run()
            self.client_handler = None
        except Exception as E:
            log.error('Error!', exc_info=self.configer.is_show_exc_info)

    def close_phase(self):
        self.server_sock.close()

    def routine(self, *args, **kwargs):
        def wrap(func):
            self.event_handler.routine_func_map[func] = (args, kwargs)

        return wrap

    def enter(self, *args, **kwargs):
        def wrap(func):
            self.event_handler.enter_func_map[func] = (args, kwargs)

        return wrap

    def exit(self, *args, **kwargs):
        def wrap(func):
            self.event_handler.exit_func_map[func] = (args, kwargs)

        return wrap

    def response(self, key: str, *args, **kwargs):
        if kwargs is None:
            kwargs = {}

        def wrap(func):
            self.event_handler.response_func_map[key] = (func, args, kwargs)

        return wrap

    def get_configer(self):
        return self.configer
