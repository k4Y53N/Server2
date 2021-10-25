import logging
from socket import socket, AF_INET, SOCK_STREAM, timeout
from queue import Queue, Full, Empty
from threading import Thread, Lock
from json import loads, dumps
from struct import calcsize, pack, unpack
from .utils.Frames import RESET


class Connection:

    def __init__(self, ip: str = 'localhost', port: int = 0):
        self.__format = 'utf-8'
        self.__header_size = calcsize('>i')
        self.__connection_kword = ('LOGOUT', 'EXIT', 'SHUTDOWN')
        self.__server_sock = socket(AF_INET, SOCK_STREAM)
        self.__server_sock.bind((ip, port))
        self.__server_sock.settimeout(3)
        self.__server_sock.listen(1)
        server_address = self.__server_sock.getsockname()
        self.__server_address = ':'.join((server_address[0], str(server_address[1])))
        self.__cliet_address = None
        self.__send_lock = Lock()
        self.__input_buffer = Queue()
        self.__output_buffer = Queue()
        self.__is_connect = True
        self.__is_client_connect = True
        self.__thread = Thread(target=self.__loop)

    def activate(self):
        if self.__thread.is_alive():
            return

        try:
            self.__thread.start()
        except RuntimeError:
            self.__thread = Thread(target=self.__loop)
            self.__thread.start()

    def __loop(self):
        logging.info(
            f'Connection Server Address => {self.__server_address}')

        while self.__is_connect:
            try:
                self.__reset()
                logging.info('Waiting Client Connect...')
                client, address = self.__server_sock.accept()
            except (OSError, KeyboardInterrupt, timeout, Exception) as E:
                logging.error(E.__class__.__name__, exc_info=True)
                self.close()
            else:
                self.__handle_client(client, ip=address[0], port=address[1])
                client.close()

    def __handle_client(self, client: socket, ip: str, port: int):
        self.__cliet_address = ':'.join((ip, str(port)))
        logging.info(
            f'Client Connect Address => {self.__cliet_address}')
        client.settimeout(3)
        recv_thread = Thread(target=self.__listening, args=(client,), daemon=True)
        send_thread = Thread(target=self.__sending, args=(client,), daemon=True)
        recv_thread.start()
        send_thread.start()
        recv_thread.join()
        send_thread.join()
        client.close()

    def __listening(self, client: socket):
        while self.__is_client_connect:
            try:
                message = self.__recv_message(client)
                if message['CMD'] in self.__connection_kword:
                    self.__normal_disconnect(client, message)
                else:
                    self.__input_buffer.put(message, True, 0.2)
            except Full:
                continue
            except(RuntimeError, OSError, timeout, Exception) as E:
                logging.error(
                    f'Receive Thread Error => {E.__class__.__name__}', exc_info=True)
                self.__non_normal_disconnect(client)

    def __recv_message(self, client: socket) -> dict:
        msg_length = self.__recv_all(client, self.__header_size)
        msg_length = unpack('>i', msg_length)[0]
        msg_bytes = self.__recv_all(client, msg_length)
        message = loads(msg_bytes)
        return message

    def __recv_all(self, client: socket, buffer_size: int) -> bytearray:
        buffer = bytearray()

        while len(buffer) < buffer_size:
            _bytes = client.recv(buffer_size - len(buffer))
            if not _bytes:
                raise RuntimeError('Socket receiving bytes fail')
            buffer.extend(_bytes)

        return buffer

    def __sending(self, client: socket):
        while self.__is_client_connect:
            try:
                msg_bytes = self.__output_buffer.get(True, 0.2)
                self.__send_msg_bytes(client, msg_bytes)
            except Empty:
                continue
            except(RuntimeError, OSError, timeout, Exception) as E:
                logging.error(
                    f'Send Thread Error => {E.__class__.__name__}', exc_info=True)
                self.__non_normal_disconnect(client)

    def __send_msg_bytes(self, client: socket, msg_bytes: bytearray):
        with self.__send_lock:
            header_bytes = pack('>i', len(msg_bytes))
            self.__send_all(client, header_bytes)
            self.__send_all(client, msg_bytes)

    def __send_all(self, client: socket, bytes: bytearray):
        total_send = 0

        while total_send > len(bytes):
            sent = client.send(bytes[total_send:])
            if not sent:
                raise RuntimeError('Socket sending bytes fail')
            total_send += sent

    def __non_normal_disconnect(self, client: socket):
        self.__is_client_connect = False

    def __normal_disconnect(self, client: socket, connection_ctrl: dict):
        self.__is_client_connect = False

    def __reset(self):
        self.__clear_buffer()
        self.__is_client_connect = True
        self.__cliet_address = None
        reset = RESET.copy()
        self.__input_buffer.put(reset)
        # TODO: put reset dict to buffer

    def __clear_buffer(self):
        with self.__input_buffer.mutex:
            self.__input_buffer.queue.clear()
        with self.__output_buffer.mutex:
            self.__output_buffer.queue.clear()

    def __login(self):
        pass

    def __logout(self):
        pass

    def __exit(self):
        pass

    def close(self):
        self.__is_connect = False
        self.__server_sock.close()
        self.__clear_buffer()

    def get(self) -> dict:
        try:
            message = self.__input_buffer.get()
        except Empty:
            return None
        else:
            return message

    def put(self, message: dict):
        if not self.__is_client_connect:
            return

        try:
            msg_bytes = dumps(message).encode(self.__format)
            self.__output_buffer.put(msg_bytes, True, 0.2)
        except Full:
            return

    def get_server_address(self) -> str:
        return self.__server_address

    def get_client_address(self) -> str:
        return self.__cliet_address

    def is_connect(self) -> bool:
        return self.__is_connect

    def is_alive(self) -> bool:
        return self.__thread.is_alive()


if __name__ == '__main__':
    from .utils.util import get_hostname

    connection = Connection(get_hostname())
    connection.activate()
