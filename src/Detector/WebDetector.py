import logging as log
from socket import socket, AF_INET, SOCK_STREAM, timeout, SHUT_RDWR
from queue import Queue, Full, Empty
from threading import Thread, Lock
from json import loads, dumps
from struct import calcsize, pack, unpack
from typing import Union, Tuple
from src.RepeatTimer import RepeatTimer
from src.utils.Commands import SYS_LOGOUT, SYS_EXIT, SYS_SHUTDOWN
from . import DetectResult


class WebDetector:
    def __init__(self):
        self.__format = 'utf-8'
        self.__header_format = '>i'
        self.__header_size = calcsize(self.__header_format)

    def __str__(self):
        pass

    def reset(self):
        pass

    def close(self):
        pass

    def load_model(self):
        pass

    def detect(self):
        pass