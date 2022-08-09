import json
from pathlib import Path
from src.API import *

cmd_dir = Path('src/utils/APIs')
configs_dir = Path('./configs')
file_suffix = '*.json'


def load_configs(*args, **kwargs):
    configs = CONFIGS.copy()

    for config_path in configs_dir.glob(file_suffix):
        with config_path.open() as f:
            config = json.load(f)

        configs['CONFIGS'][config_path.name] = {
            'SIZE': config['size'],
            'MODEL_TYPE': config['model_type'],
            'TINY': config['tiny'],
            'CLASSES': config['YOLO']['CLASSES'],
        }

    return configs


login = cmd_dir / 'LOGIN.json'
logout = cmd_dir / 'LOGOUT.json'
_exit = cmd_dir / 'EXIT.json'
shutdown = cmd_dir / 'SHUT_DOWN.json'
reset = cmd_dir / 'RESET.json'
get_sys_info = cmd_dir / 'GET_SYS_INFO.json'
set_stream = cmd_dir / 'SET_STREAM.json'
get_configs = cmd_dir / 'GET_CONFIGS.json'
get_config = cmd_dir / 'GET_CONFIG.json'
set_config = cmd_dir / 'SET_CONFIG.json'
set_infer = cmd_dir / 'SET_INFER.json'
set_quality = cmd_dir / 'SET_QUALITY.json'
mov = cmd_dir / 'MOV.json'
sys_info = cmd_dir / 'SYS_INFO.json'
login_info = cmd_dir / 'LOGIN_INFO.json'
config = cmd_dir / 'CONFIG.json'
configs = cmd_dir / 'CONFIGS.json'
sys_log_out = cmd_dir / 'SYS_LOGOUT.json'
sys_exit = cmd_dir / 'SYS_EXIT.json'
sys_shutdown = cmd_dir / 'SYS_SHUTDOWN.json'
frame = cmd_dir / 'FRAME.json'

PATH_GROUP = [
    login, logout, _exit, shutdown, reset, get_sys_info, set_stream, get_configs, get_config, set_config, set_infer,
    set_quality, mov, sys_info, login_info, config, configs, sys_log_out, sys_exit, sys_shutdown, frame
]

DIC_GROUP = [
    LOGIN, LOGOUT, EXIT, SHUTDOWN, RESET, GET_SYS_INFO, SET_STREAM, GET_CONFIGS, GET_CONFIG, SET_CONFIG, SET_INFER,
    SET_QUALITY, MOV, SYS_INFO, LOGIN_INFO, CONFIG, load_configs(), SYS_LOGOUT, SYS_EXIT, SYS_SHUTDOWN, FRAME
]


def write_dic2json(dic: dict, path: Path):
    with path.open('w') as f:
        f.write(json.dumps(dic))


if __name__ == '__main__':
    for d, p in zip(DIC_GROUP, PATH_GROUP):
        write_dic2json(d, p)
