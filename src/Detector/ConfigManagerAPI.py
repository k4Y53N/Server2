MAIN_KEY = 'CMD'

"""
SEND
"""
SET_CONFIG = {
    MAIN_KEY: 'SET_CONFIG',
    'CONFIG_NAME': ''
}

DETECT = {
    MAIN_KEY: 'DETECT',
    'IMAGE': ''
}

RESET = {
    MAIN_KEY: 'RESET'
}

CLOSE = {
    MAIN_KEY: 'CLOSE'
}

GET_CONFIG = {
    MAIN_KEY: 'GET_CONFIG'
}

GET_CONFIGS = {
    MAIN_KEY: 'GET_CONFIGS'
}

"""
RECV
"""
RESULT = {
    MAIN_KEY: 'RESULT',
    'BBOX': [],
    'CLASS': [],
    'SCORE': []
}

CONFIG = {
    MAIN_KEY: 'CONFIG',
    'CONFIG_NAME': None,  # STR
    'SIZE': 416,
    'MODEL_TYPE': None,  # STR
    'TINY': False,
    'CLASSES': [],  # STR ARRAY
    # 'FRAME_WORK': None,  # STR
}

CONFIGS = {
    MAIN_KEY: 'CONFIGS',
    'CONFIGS': {}
}
