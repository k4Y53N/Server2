MAIN_KEY = 'CMD'

"""
    RECV
"""
# 請求登入
LOGIN = {
    MAIN_KEY: 'LOGIN',
    'PWD': 'None',  # STR
}
# 請求登出
LOGOUT = {
    MAIN_KEY: 'LOGOUT',
}
# 請求登出並離開系統
EXIT = {
    MAIN_KEY: 'EXIT',
    'PWD': 'None',  # STR
}
# 請求登出、離開系統並關機
SHUTDOWN = {
    MAIN_KEY: 'SHUTDOWN',
    'PWD': 'None'  # STR
}
# 重置系統並且不登出
RESET = {
    MAIN_KEY: 'RESET'
}
# 請求伺服器回傳系統資訊，其中包含是否串流中、是否辨識中
GET_SYS_INFO = {
    MAIN_KEY: 'GET_SYS_INFO'
}
# 設定伺服器是否進行串流
SET_STREAM = {
    MAIN_KEY: 'SET_STREAM',
    'STREAM': False
}
# 請求多個可選擇的config檔
GET_CONFIGS = {
    MAIN_KEY: 'GET_CONFIGS',
}
# 請求查看當前選擇的config檔
GET_CONFIG = {
    MAIN_KEY: 'GET_CONFIG',
}
# 設定選擇的config檔 如果上個config檔載入完成 則該次設定不接受
SET_CONFIG = {
    MAIN_KEY: 'SET_CONFIG',
    'CONFIG': ''  # STR
}
# 設定串流影像是否附加回傳辨識結果
SET_INFER = {
    MAIN_KEY: 'SET_INFER',
    'INFER': True  # BOOLEAN
}
# 設定攝影機畫質
SET_QUALITY = {
    MAIN_KEY: 'SET_QUALITY',
    'WIDTH': 1080,  # INT
    'HEIGHT': 720,  # INT
}
# 設定移動
MOV = {
    MAIN_KEY: 'MOV',
    # 'L': 0.0,  # FLOAT
    # 'R': 0.0,  # FLOAT
    'R': 0,  # FLOAT (0~1)
    'THETA': 0,  # FLOAT(0~360)
}

"""
    SEND
"""
# 回傳Client系統資訊
SYS_INFO = {  # SYS SETTING
    MAIN_KEY: 'SYS_INFO',
    'IS_INFER': False,
    'IS_STREAM': False,
    'CAMERA_WIDTH': 1280,  # INT
    'CAMERA_HEIGHT': 720,  # INT
}
# 回傳登入狀態
LOGIN_INFO = {
    MAIN_KEY: 'LOG_INFO',
    'VERIFY': False  # BOOLEAN
}
# 回傳Client config檔相關資訊 如果無法取得(config檔載入模型資料需要時間!)則皆為空
# {"CMD": "CONFIG", "CONFIG_NAME": null, "CLASSES": [], "MODEL_TYPE": null, "FRAME_WORK": null}
CONFIG = {
    MAIN_KEY: 'CONFIG',
    'CONFIG_NAME': None,  # STR
    'SIZE': 416,
    'MODEL_TYPE': None,  # STR
    'TINY': False,
    'CLASSES': [],  # STR ARRAY
    # 'FRAME_WORK': None,  # STR
}
# 回傳Client可選的config檔
CONFIGS = {
    MAIN_KEY: 'CONFIGS',
    'CONFIGS': {
        # config_name1 :{
        #   SIZE: 320,
        #   MODEL_TYPE : yolov4
        #   TINY: True or False
        #   CLASSES = [class1, class2 ...]
        # }
        # config_name2 :{
        #   SIZE: 416,
        #   MODEL_TYPE : yolov4
        #   TINY: True or False
        #   CLASSES = [class1, class2 ...]
        # } 
        # ...
    }
}
# 回傳Client系統登出
SYS_LOGOUT = {
    MAIN_KEY: 'SYS_LOGOUT',
}
# 回傳Client系統登出、關閉、並不關機
SYS_EXIT = {
    MAIN_KEY: 'SYS_EXIT',
}
# 回傳Client系統登出、關閉、並且關機
SYS_SHUTDOWN = {
    MAIN_KEY: 'SYS_SHUTDOWN'
}
# 回傳Client串流畫面，如果有附加辨識結果 'IS_INFER' 為TRUE 且附加 BBOX, 否則 IS_INFER 為FALSE.
FRAME = {
    MAIN_KEY: 'FRAME',
    'IMAGE': '',  # BASE64 String
    'BBOX': [],  # ARRAY [[X1, Y1, X2, Y2, CLASS_INDEX], [X1, Y1, X2, Y2, CLASS_INDEX]...]
    'CLASS': []  # CLASS_NAMES
}
