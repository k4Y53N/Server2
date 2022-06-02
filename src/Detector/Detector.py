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
    def __new__(
            cls,
            is_local_detector,
            yolo_configs_dir,
            remote_detector_ip,
            remote_detector_port,
            is_show_exc_info
    ):
        if is_local_detector:
            return LocalDetector(yolo_configs_dir, is_show_exc_info=is_show_exc_info)
        return RemoteDetector(remote_detector_ip, remote_detector_port, is_show_exc_info)
