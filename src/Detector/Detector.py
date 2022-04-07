from .WebDetector import WebDetector
from .LocalDetector import LocalDetector
from pathlib import Path


class Detector:
    def __new__(cls, configs_path: Path, is_local: bool, *args, **kwargs):
        if is_local:
            return LocalDetector(configs_path)
        return WebDetector()
