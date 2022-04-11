from .RemoteDetector import RemoteDetector
from .LocalDetector import LocalDetector


class DetectorBuilder:
    def __init__(self):
        self.yolo_configs_dir = ''
        self.is_show_exc_info = True
        self.is_local_detector = True
        self.remote_detector_ip = 'localhost'
        self.remote_detector_port = 0


class Detector:
    def __new__(cls, builder: DetectorBuilder):
        if builder.is_local_detector:
            return LocalDetector(builder.yolo_configs_dir, is_show_exc_info=True)
        return RemoteDetector(builder.remote_detector_ip, builder.remote_detector_port, builder.is_show_exc_info)
