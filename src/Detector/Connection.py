import logging as log
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from json import loads, dumps
from struct import calcsize, pack, unpack
from threading import Lock


class Connection:
    def __init__(self):
        self.__format = 'utf-8'
        self.__header_format = '>i'
        self.__header_size = calcsize(self.__header_format)
        self.socket = socket(AF_INET, SOCK_STREAM)

    def _recv_message(self, sock: socket) -> dict:
        msg_length = self.__recv_all(sock, self.__header_size)
        msg_length = unpack(self.__header_format, msg_length)[0]
        msg_bytes = self.__recv_all(sock, msg_length)
        message = loads(msg_bytes)
        return message

    def __recv_all(self, sock: socket, buffer_size: int) -> bytearray:
        buffer = bytearray()

        while len(buffer) < buffer_size:
            _bytes = sock.recv(buffer_size - len(buffer))
            if not _bytes:
                raise RuntimeError('Pipline close')
            buffer.extend(_bytes)

        return buffer

    def _send_message(self, sock: socket, message: dict):
        message = dumps(message).encode(self.__format)
        header_bytes = pack(self.__header_format, len(message))
        self.__send_all(sock, header_bytes)
        self.__send_all(sock, message)

    def __send_all(self, sock: socket, _bytes: bytes):
        total_send = 0

        while total_send < len(_bytes):
            sent = sock.send(_bytes[total_send:])
            if not sent:
                raise RuntimeError('Pipline close')
            total_send += sent

    def close(self):
        self.socket.close()


class ClientConnection(Connection):
    def __init__(self, ip, port):
        Connection.__init__(self)
        self.socket.connect((ip, port))
        self.lock = Lock()

    def receive_message(self) -> dict:
        try:
            with self.lock:
                return super()._recv_message(self.socket)
        except Exception as E:
            log.error('Receive message fail', exc_info=True)
            return dict()

    def send_message(self, message: dict):
        try:
            with self.lock:
                super()._send_message(self.socket, message)
        except Exception as E:
            log.error('Send message fail', exc_info=True)
            return dict()

    def send_and_recv(self, message: dict):
        try:
            with self.lock:
                self._send_message(self.socket, message)
                message = self._recv_message(self.socket)
            return message
        except Exception as E:
            log.error('Send and Receive message fail', exc_info=True)
            return dict()


class ServerConnection(Connection):
    def __init__(self, ip, port):
        Connection.__init__(self)
        self.socket.bind((ip, port))
        self.socket.listen(1)

    def receive_message(self, sock: socket) -> dict:
        return super()._recv_message(sock)

    def send_message(self, sock: socket, message: dict):
        super()._send_message(sock, message)
