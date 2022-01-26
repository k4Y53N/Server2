import logging
from socket import socket, AF_INET, SOCK_STREAM, timeout
from queue import Queue, Full, Empty
from threading import Thread, Lock
from json import loads, dumps
from struct import calcsize, pack, unpack
from typing import Union, Tuple


class Connection(Thread):

    def __init__(self, ip: str = 'localhost', port: int = 0) -> None:
        Thread.__init__(self)
        self.__format = 'utf-8'
        self.__header_size = calcsize('>i')
        self.__connection_keyword = ('LOGOUT', 'EXIT', 'SHUTDOWN')
        self.__server_sock = socket(AF_INET, SOCK_STREAM)
        self.__server_sock.bind((ip, port))
        self.__send_lock = Lock()
        self.__input_buffer = Queue()
        self.__output_buffer = Queue()
        self.__server_address = self.__server_sock.getsockname()
        self.__client_address = None
        self.__is_connect = True
        self.__is_client_connect = True

    def run(self):
        self.__server_sock.settimeout(300)
        self.__server_sock.listen(1)
        logging.info('Connection Server Address => %s:%d' % self.__server_address)

        while self.__is_connect:
            try:
                logging.info('Waiting Client Connect...')
                client, address = self.__server_sock.accept()
                self.__handle_client(client, address)
            except (OSError, KeyboardInterrupt, timeout, Exception) as E:
                logging.error(E.__class__.__name__, exc_info=True)
                continue
            finally:
                self.__reset()
        self.close()

    def __handle_client(self, client: socket, address: Tuple[str, int]):
        self.__client_address = client.getpeername()
        logging.info('Client Connect Address => %s:%d' % address)
        client.settimeout(30)
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
                message, address = self.__recv_message(client), client.getpeername()
                if message['CMD'] in self.__connection_keyword:
                    self.__normal_disconnect(client, message)
                else:
                    self.__input_buffer.put((message, address), True, 0.2)
            except Full:
                continue
            except(RuntimeError, OSError, timeout, Exception) as E:
                logging.error(f'{E.__class__.__name__} with {E.__args[0]}', exc_info=True)
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
                raise RuntimeError('Pipline close')
            buffer.extend(_bytes)

        return buffer

    def __sending(self, client: socket):
        while self.__is_client_connect:
            try:
                msg_bytes, address = self.__output_buffer.get(True, 0.2)
                if address != client.getpeername():
                    continue
                self.__send_message(client, msg_bytes)
            except Empty:
                continue
            except(RuntimeError, OSError, timeout, Exception) as E:
                logging.error(f'{E.__class__.__name__} with {E.__args[0]}', exc_info=True)
                self.__non_normal_disconnect(client)

    def __send_message(self, client: socket, message: dict):
        with self.__send_lock:
            message = dumps(message).encode(self.__format)
            header_bytes = pack('>i', len(message))
            self.__send_all(client, header_bytes)
            self.__send_all(client, message)

    def __send_all(self, client: socket, _bytes: bytes):
        total_send = 0

        while total_send < len(_bytes):
            sent = client.send(_bytes[total_send:])
            if not sent:
                raise RuntimeError('Pipline close')
            total_send += sent

    def __non_normal_disconnect(self, client: socket):
        self.__is_client_connect = False
        pass

    def __normal_disconnect(self, client: socket, connection_ctrl: dict):
        self.__is_client_connect = False
        pass

    def __reset(self):
        self.__clear_buffer()
        self.__is_client_connect = True
        self.__client_address = None

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
        self.__reset()
        self.__is_connect = False
        self.__is_client_connect = False
        self.__server_sock.close()

    def get(self, time_limit: float = 0.2) -> Tuple[dict, Tuple[str, int]]:
        try:
            message, address = self.__input_buffer.get(True, time_limit)
            return message, address
        except Empty:
            return dict(), self.__client_address

    def put(self, message: dict, address: Tuple[str, int], time_limit: float = 0.2):
        try:
            self.__output_buffer.put((message, address), True, time_limit)
        except Full:
            return

    def get_server_address(self) -> Tuple[str, int]:
        return self.__server_address

    def get_client_address(self) -> Union[Tuple[str, int], None]:
        return self.__client_address

    def is_connect(self) -> bool:
        return self.__is_connect


if __name__ == '__main__':
    from utils.util import get_hostname

    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        level=logging.INFO
    )

    connection = Connection(get_hostname())
    connection.start()
    print(connection.get_server_address())
    print(connection.get_client_address())
    # connection.unlock()
    connection.join()
