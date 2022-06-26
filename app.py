import os
import logging as log
from typing import Tuple
from pathlib import Path
from time import strftime
from src.Server import Server
from src.Monitor import Monitor
from src.API import FRAME, SYS_INFO, CONFIGS, CONFIG, LOGIN_INFO
from src.Streamer import Streamer
from src.PWMController import PWMController
from src.Configer import Configer
from src.ShellPrinter import ShellPrinter
from src.utils.util import read_pwd

configer = Configer('./sys.ini')
log_dir = Path('logs')
log_file_path = (log_dir / strftime('%YY-%mM-%dD_%HH-%Mm-%Ss')).with_suffix('.log')
os.makedirs(log_dir, exist_ok=True)
log_file_path.touch(exist_ok=True)
log.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    filename=str(log_file_path),
    datefmt='%Y/%m/%d %H:%M:%S',
    level=configer.log_level,
)

pwd = read_pwd(configer.password_path)
streamer = Streamer(
    max_fps=configer.max_fps,
    idle_interval=configer.idle_interval,
    stream_timeout=configer.stream_timeout,
    jpg_encode_rate=configer.jpg_encode_rate,
    is_local_detector=configer.is_local_detector,
    yolo_configs_dir=configer.yolo_configs_dir,
    remote_detector_ip=configer.remote_detector_ip,
    remote_detector_port=configer.remote_detector_port,
    remote_detector_timeout=configer.remote_detector_timeout,
    is_show_exc_info=configer.is_show_exc_info
)

monitor = Monitor()

pwm_controller = PWMController(
    (configer.pwm_speed_port, configer.pwm_angle_port),
    configer.pwm_frequency,
    min_angle=configer.pwm_min_angle,
    max_angle=configer.pwm_max_angle,
    is_listen=configer.is_pwm_listen
)

s = Server(
    ip=configer.ip,
    port=configer.port,
    is_login=configer.is_login,
    server_timeout=configer.server_timeout,
    client_timeout=configer.client_timeout,
    max_connection=configer.max_connection,
    is_show_exc_info=configer.is_show_exc_info
)

monitor.set_row_string(0, '%s:%s' % (s.ip, s.port))
shell_printer = ShellPrinter(s, pwm_controller, streamer)


@s.login(pwd)
def login(message: dict, password, *args, **kwargs) -> Tuple[bool, dict]:
    p = message.get('PWD', '')
    log_info = LOGIN_INFO.copy()
    if p != password:
        log_info['VERIFY'] = False
        return False, log_info
    log_info['VERIFY'] = True
    return True, log_info


@s.enter(monitor, pass_address=True)
def client_enter(m: Monitor, address, *args, **kwargs):
    m.set_row_string(1, '%s:%s' % address)


@s.routine(streamer)
def stream(st: Streamer, *args, **kwargs):
    stream_frame = st.get()
    if not stream_frame.is_available():
        return
    frame = FRAME.copy()
    frame['IMAGE'] = stream_frame.b64image if stream_frame.b64image else ''
    frame['BBOX'] = stream_frame.boxes
    frame['CLASS'] = stream_frame.classes
    return frame


@s.exit(streamer, monitor, pwm_controller, pass_address=True)
def client_exit(st: Streamer, m: Monitor, pwm: PWMController, address: Tuple = ('127.0.0.1', 0), *args, **kwargs):
    st.reset()
    m.set_row_string(1, None)
    pwm.reset()
    log.info('Client %s:%s disconnect' % address)


@s.response('RESET')
def reset(message, *args, **kwargs):
    pass


@s.response('GET_SYS_INFO', streamer)
def get_sys_info(message, *args, **kwargs):
    log.info('Get System Information')
    sys_info = SYS_INFO.copy()
    sys_info['IS_INFER'] = streamer.is_infer()
    sys_info['IS_STREAM'] = streamer.is_stream()
    sys_info['CAMERA_WIDTH'], SYS_INFO['CAMERA_HEIGHT'] = streamer.get_quality()
    return sys_info


@s.response('GET_CONFIGS', streamer)
def get_configs(message, st: Streamer, *args, **kwargs):
    log.info('Get configs')
    configs = CONFIGS.copy()
    configs['CONFIGS'] = {
        key: {
            'SIZE': val.size,
            'MODEL_TYPE': val.model_type,
            'TINY': val.tiny,
            'CLASSES': val.classes
        }
        for key, val in st.get_configs().items()
    }
    return configs


@s.response('GET_CONFIG', streamer)
def get_config(message, st: Streamer, *args, **kwargs):
    log.info('Get config')
    config = CONFIG.copy()
    yolo_config = st.get_config()
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


@s.response('SET_CONFIG', streamer)
def set_config(message: dict, st: Streamer, *args, **kwargs):
    config_name = message.get('CONFIG')
    log.info(f'Set config {config_name}')
    st.set_config(config_name)


@s.response('SET_INFER', streamer)
def set_infer(message, st: Streamer, *args, **kwargs):
    is_infer = bool(message.get('INFER'))
    log.info(f'Set Infer: {is_infer}')
    st.set_infer(is_infer)


@s.response('SET_STREAM', streamer)
def set_stream(message, st: Streamer, *args, **kwargs):
    is_stream = bool(message.get('STREAM'))
    log.info(f'Set Stream: {is_stream}')
    st.set_stream(is_stream)


@s.response('SET_QUALITY', streamer)
def set_quality(message, st: Streamer, *args, **kwargs):
    width = int(message.get('WIDTH', 0))
    height = int(message.get('HEIGHT', 0))
    log.info(f'Set Quality: W = {width}, H = {height}')
    if 100 < width > 4196 or 100 < height > 4196:
        log.warning(f'Wrong quality w:{width}, h:{height}')
        return
    st.set_quality(width, height)


@s.response('MOV', pwm_controller)
def mov(message, pwm, *args, **kwargs):
    r = message.get('R', 0)
    theta = message.get('THETA', 90)
    pwm.set(r, theta)


if __name__ == '__main__':
    monitor.start()
    streamer.start()
    pwm_controller.start()
    shell_printer.start()
    try:
        s.run()
    except KeyboardInterrupt:
        log.warning('Ctrl + C')
    finally:
        monitor.close()
        streamer.close()
        pwm_controller.close()
        shell_printer.close()
        monitor.join()
        streamer.join()
        pwm_controller.join()
        shell_printer.clean_screen()
