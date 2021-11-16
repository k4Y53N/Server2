"""
2021/9/21
FRAME移除IS_INFER
如果有辨識結果只要判斷BBOX長度是否為零即可

SYS_INFO CMD ==> SYS_INFO
SET_QUALITY => SET_RESOLUTION

2021/7/16
修改SYS_INFO
    -QUALITY 合併到SYS_INFO底下

IS_STREAM ==> SET_STREAM
LOG_INFO ==> LOGIN_INFO

新增 SHUTDOWN、EXIT、GET_SYS_INFO
移除GET_QUALITY、QUALITY 取得畫質用 GET_SYS_INFO 回傳 SYS_INFO (SET_QUALITY依舊可用)
移除MESSAGE

TODO: 預計合併 CONFIGS & CONFIG; GET_CONFIGS % GET_CONFIG??不確定中
CMD(String) -> Configs(String)
Configs(String) -> Config(Map) 每個 map 以config_name為key
Config_name(String) -> ...

CONFIGS = {
    'CMD': 'CONFIGS',
    'CONFIGS': {

        'config_name1': {
            # ...
        },

        'config_name2': {
            # ...
        }
    }
}

example:
    'CMD': 'CONFIGS'
    'CONFIGS':{
        'CONFIG_NAME1':{
            'CLASSES':{
                0:'PERSON',
                1:'CAR',
            }
            'MODEL_TYPE':'YOLOV4',
            'FRAME_WORK':'Tensorflow',
        },

        'CONFIG_NAME2':{
            'CLASSES':{
                0:'horse',
                1:'boat',
            }
            'MODEL_TYPE':'YOLOV3',
            'FRAME_WORK':'TesorRT',
        }
    }
"""

"""
    RECV
"""
# 請求登入
LOGIN = {
    'CMD': 'LOGIN',
    'PWD': 'None',  # STR
}
# 請求登出
LOGOUT = {
    'CMD': 'LOGOUT',
}
# 請求登出並離開系統
EXIT = {
    'CMD': 'EXIT',
    'PWD': 'None',  # STR
}
# 請求登出、離開系統並關機
SHUTDOWN = {
    'CMD': 'SHUTDOWN',
    'PWD': 'None'  # STR
}
# 重置系統並且不登出
RESET = {
    'CMD': 'RESET'
}
# 請求伺服器回傳系統資訊，其中包含是否串流中、是否辨識中
GET_SYS_INFO = {
    'CMD': 'GET_SYS_INFO'
}
# 設定伺服器是否進行串流
SET_STREAM = {
    'CMD': 'SET_STREAM',
    'STREAM': False
}
# 請求多個可選擇的config檔
GET_CONFIGS = {
    'CMD': 'GET_CONFIGS',
}
# 請求查看當前選擇的config檔
GET_CONFIG = {
    'CMD': 'GET_CONFIG',
}
# 設定選擇的config檔 如果上個config檔載入完成 則該次設定不接受
SET_CONFIG = {
    'CMD': 'SET_CONFIG',
    'CONFIG': ''  # STR
}
# 設定串流影像是否附加回傳辨識結果
SET_INFER = {
    'CMD': 'SET_INFER',
    'INFER': True  # BOOLEAN
}
# 設定攝影機畫質
SET_QUALITY = {
    'CMD': 'SET_QUALITY',
    'WIDTH': 1080,  # INT
    'HEIGHT': 720,  # INT
}
# 設定移動
MOV = {
    'CMD': 'MOV',
    'L': 0.0,  # FLOAT
    'R': 0.0,  # FLOAT
}

"""
    SEND
"""
# 回傳Client系統資訊
SYS_INFO = {  # SYS SETTING
    'CMD': 'SYS_INFO',
    'IS_INFER': False,
    'IS_STREAM': False,
    'CAMERA_WIDTH': 1080,  # INT
    'CAMERA_HEIGHT': 720,  # INT
}
# 回傳登入狀態
LOGIN_INFO = {
    'CMD': 'LOG_INFO',
    'VERIFY': False  # BOOLEAN
}
# 回傳Client config檔相關資訊 如果無法取得(config檔載入模型資料需要時間!)則皆為空
# {"CMD": "CONFIG", "CONFIG_NAME": null, "CLASSES": [], "MODEL_TYPE": null, "FRAME_WORK": null}
CONFIG = {
    'CMD': 'CONFIG',
    'CONFIG_NAME': None,  # STR
    'CLASSES': [],  # STR ARRAY
    'MODEL_TYPE': None,  # STR
    'FRAME_WORK': None,  # STR
}
# 回傳Client可選的config檔
CONFIGS = {
    'CMD': 'CONFIGS',
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
    'CMD': 'SYS_LOGOUT',
}
# 回傳Client系統登出、關閉、並不關機
SYS_EXIT = {
    'CMD': 'SYS_EXIT',
}
# 回傳Client系統登出、關閉、並且關機
SYS_SHUTDOWN = {
    'CMD': 'SYS_SHUTDOWN'
}
# 回傳Client串流畫面，如果有附加辨識結果 'IS_INFER' 為TRUE 且附加 BBOX, 否則 IS_INFER 為FALSE.
FRAME = {
    'CMD': 'FRAME',
    'IMAGE': '',  # BASE64 String
    'BBOX': [],  # ARRAY
}
