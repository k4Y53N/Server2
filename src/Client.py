import logging as log
import json
from socket import socket, AF_INET, SOCK_STREAM
from threading import Lock
from typing import Union
from .socketIO import recv, send


class Client:
    def __init__(self, ip: str, port: int, time_out: float, is_show_exc_info=False):
        self.ip = ip
        self.port = port
        self.header = '>i'
        self.encoding = 'utf-8'
        self.lock = Lock()
        self.sock: socket = socket(AF_INET, SOCK_STREAM)
        self.sock.settimeout(time_out)
        self.is_show_exc_info = is_show_exc_info
        self.connect()

    def connect(self):
        self.sock.connect((self.ip, self.port))

    def recv(self) -> Union[str, dict]:
        with self.lock:
            ret_obj = None
            try:
                ret_obj = recv(self.sock, self.header, self.encoding)
                ret_obj = json.loads(ret_obj)
            except Exception:
                log.error('Recv message fail', exc_info=self.is_show_exc_info)
        return ret_obj

    def send(self, obj: Union[str, dict]):
        if obj is None:
            return
        with self.lock:
            try:
                if type(obj) is dict:
                    obj = json.dumps(obj)
                send(self.sock, obj, self.header, self.encoding)
            except Exception:
                log.error('Send message fail', exc_info=self.is_show_exc_info)

    def send_and_recv(self, obj: Union[str, dict]):
        if obj is None:
            return
        ret_obj = None
        with self.lock:
            try:
                if type(obj) is dict:
                    obj = json.dumps(obj)
                send(self.sock, obj, self.header, self.encoding)
                ret_obj = recv(self.sock, self.header, self.encoding)
                # ret_obj = json.loads(ret_obj)
            except Exception:
                log.error('Send and Recv message fail', exc_info=self.is_show_exc_info)
        return ret_obj

    def close(self):
        self.sock.close()

    #     self.input_buffer = Queue()
    #     self.output_buffer = Queue()
    #     self.thread_pool = [
    #         Thread(target=self.__receiving, name='SocketRecv'),
    #         Thread(target=self.__sending, name='SocketSend')
    #     ]
    #
    # def init_phase(self):
    #     try:
    #         self.sock.settimeout(self.time_out)
    #         self.sock.connect((self.ip, self.port))
    #         for t in self.thread_pool:
    #             t.start()
    #     except timeout:
    #         log.error('Client connect timeout')
    #
    # def execute_phase(self):
    #     pass
    #
    # def close_phase(self):
    #     pass
    #
    # def __receiving(self):
    #     while self.is_running():
    #         try:
    #             message = recv(self.sock, self.header, self.encoding)
    #             self.input_buffer.put(message, True, 0.2)
    #         except Full:
    #             self.close()
    #             log.error('Input buffer overflow', exc_info=self.is_show_exc_info)
    #         except Exception:
    #             self.close()
    #             log.error('Receiving fail', exc_info=self.is_show_exc_info)
    #
    # def __sending(self):
    #     while self.is_running():
    #         try:
    #             response = self.output_buffer.get(True, 0.2)
    #             send(self.sock, response, self.header, self.encoding)
    #         except Empty:
    #             continue
    #         except Exception:
    #             self.close()
    #             log.error('Sending fail', exc_info=self.is_show_exc_info)
