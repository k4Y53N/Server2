from socket import socket
from struct import pack, unpack, calcsize


def recv(sock: socket, header: str = '>i', encoding: str = 'utf8') -> str:
    header_size = calcsize(header)
    head = recv_all(sock, header_size)
    head = unpack(header, head)[0]
    return recv_all(sock, head).decode(encoding)


def recv_all(sock: socket, byte_len: int) -> bytearray:
    buffer = bytearray()
    while len(buffer) < byte_len:
        byte = sock.recv(byte_len - len(buffer))
        if not byte:
            raise RuntimeError('pipe close')
        buffer.extend(byte)
    return buffer


def send(sock: socket, message: str, header: str = '>i', encoding: str = 'utf-8'):
    byte = message.encode(encoding)
    head = pack(header, len(byte))
    send_all(sock, head)
    send_all(sock, byte)


def send_all(sock: socket, byte):
    total_send = 0

    while total_send < len(byte):
        sent = sock.send(byte[total_send:])
        if not sent:
            raise RuntimeError('Pipline close')
        total_send += sent
