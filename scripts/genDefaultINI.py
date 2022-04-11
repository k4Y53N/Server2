from configparser import ConfigParser
import logging as log

if __name__ == '__main__':
    config = ConfigParser()
    config['Server'] = {
        'ip': 0,
        'port': 0,
        'is_show_exc_info': True,
        'log_level': log.INFO
    }

    config['PWM'] = {
        'pwm_speed_port': 37,
        'pwm_angle_port': 38,
        'frequency': 0.25,
        'is_pwm_listen': False
    }

    config['Streamer'] = {
        'max_fps': 30,
        'idle_interval': 1,
        'timeout': 10,
        'jpg_encode_rate': 50
    }

    config['Detector'] = {
        'configs': 'configs/',
        'is_local_detector': True,
        'detect_server_ip': '192.168.0.1',
        'detect_server_port': 0
    }
    with open('./sys.ini', 'w') as f:
        config.write(f)
