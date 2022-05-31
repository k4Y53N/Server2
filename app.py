from src.Server import Server, ServerBuilder
import logging as log
from typing import Tuple

from src.Monitor import Monitor
from src.API import FRAME, SYS_INFO, CONFIGS, CONFIG
from src.Streamer import Streamer
from src.PWMController import PWMController

builder = ServerBuilder('./sys.ini')
monitor = Monitor()
streamer = Streamer(builder.get_streamer_builder())
pwm_controller = PWMController((builder.pwm_speed_port, builder.pwm_angle_port), builder.pwm_frequency,
                               builder.is_pwm_listen)
s = Server('127.0.0.1', 5050)


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


@s.exit(streamer, monitor, pass_address=True)
def client_exit(st: Streamer, m: Monitor, address: Tuple = ('127.0.0.1', 0), *args, **kwargs):
    st.reset()
    m.set_row_string(1, None)
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
    if 100 < width < 4196 or 100 < height < 4196:
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
    s.run()
