from configparser import ConfigParser
from .utils.util import get_hostname


class Configer:
    def __init__(self, build_config_file_path):
        config = ConfigParser()
        config.read(build_config_file_path)
        is_ip = config.getboolean('Server', 'ip')
        self.ip = config['Server']['ip'] if is_ip else get_hostname()
        self.port = int(config['Server']['port'])
        self.server_timeout = float(config['Server']['server_timeout'])
        self.client_timeout = float(config['Server']['client_timeout'])
        self.max_connection = int(config['Server']['max_connection'])
        self.log_level = int(config['Server']['log_level'])
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
