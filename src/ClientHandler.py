import json
import logging as log
from queue import Queue, Full, Empty
from threading import Thread
from typing import Dict, Callable, Union, Any, Tuple, List, Optional
from socket import socket
from .API import MAIN_KEY
from .RepeatTimer import RepeatTimer
from .socketIO import recv, send


class EventHandler:
    def __init__(self):
        self.response_func_map: Dict[str, Tuple[Callable, tuple, dict]] = {}
        self.enter_func_map: Dict[Callable, Tuple[tuple, dict]] = {}
        self.exit_func_map: Dict[Callable, Tuple[tuple, dict]] = {}
        self.routine_func_map: Dict[Callable, Tuple[tuple, dict]] = {}

    def handle(self, message: Union[str, dict]) -> Any:
        pass

    def execute_enter_funcs(self):
        for func, (args, kwargs) in self.enter_func_map.items():
            func(*args, **kwargs)

    def execute_exit_funcs(self):
        for func, (args, kwargs) in self.exit_func_map.items():
            func(*args, **kwargs)

    def get_response_func_map(self):
        return self.response_func_map

    def get_enter_func_map(self):
        return self.enter_func_map

    def get_exit_func_map(self):
        return self.exit_func_map

    def get_routine_func_map(self):
        return self.routine_func_map


class ClientHandler(RepeatTimer):
    def __init__(self, sock: socket, event_handler: EventHandler, is_show_exc_info=False):
        RepeatTimer.__init__(self, interval=0)
        self.sock: socket = sock
        self.header = '>i'
        self.encoding = 'utf-8'
        self.event_handler = event_handler
        self.is_show_exc_info = is_show_exc_info
        self.last_cmd = None
        self.ip, self.port = self.sock.getpeername()

    def __str__(self):
        return f'Client address => {self.ip}:{self.port} | last CMD: {self.last_cmd}'

    def init_phase(self):
        pass

    def execute_phase(self):
        pass

    def close_phase(self):
        pass


class SyncClientHandler(ClientHandler):
    def __init__(self, sock: socket, event_handler: EventHandler):
        ClientHandler.__init__(self, sock, event_handler)

    def init_phase(self):
        log.info('Client address => %s:%s' % self.sock.getpeername())

    def execute_phase(self):
        try:
            message = recv(self.sock, self.header, self.encoding)
            response = self.event_handler.handle(message)
            if type(response) is not str:
                response = json.dumps(response)
            send(self.sock, response, self.header, self.encoding)
        except Exception:
            log.error('Handle Client Fail', exc_info=self.is_show_exc_info)
            self.close()

    def close_phase(self):
        self.sock.close()


class AsyncClientHandler(ClientHandler):
    def __init__(self, sock: socket, event_handler: EventHandler):
        ClientHandler.__init__(self, sock, event_handler)
        self.input_buffer = Queue()
        self.output_buffer = Queue()
        self.routine_thread_pool: List[Thread] = [
            Thread(target=self.__receiving, name='SocketRecv'),
            Thread(target=self.__sending, name='SocketSend'),
        ]

    def init_phase(self):
        log.info('Client connected address => %s:%s' % self.sock.getpeername())
        self.execute_one_time_func(self.event_handler.get_enter_func_map())
        routine_func_map = self.event_handler.get_routine_func_map()

        for func, (args, kwargs) in routine_func_map.items():
            if not callable(func):
                continue
            if kwargs.get('pass_address', False):
                kwargs['address'] = self.sock.getpeername()
            t = Thread(target=self.routine, args=(func, args, kwargs), name=func.__name__)
            self.routine_thread_pool.append(t)

        for t in self.routine_thread_pool:
            t.start()

    def execute_phase(self):
        try:
            message = self.get()
            if message is None:
                return
            self.last_cmd = message
            if type(message) is str:
                message = json.loads(message)
            if type(message) is not dict:
                raise TypeError('Get unexpected JSON message')
            main_key = message.get(MAIN_KEY, None)
            if main_key is None:
                log.warning(f'Cant get key: {message}')
                raise KeyError('Message dint define main key')
            response_func_map = self.event_handler.get_response_func_map()
            func, args, kwargs = response_func_map.get(main_key, (None, (), {}))
            if not callable(func):
                raise KeyError('Main key not found')
            if kwargs.get('pass_address', False):
                kwargs['address'] = self.sock.getpeername()
            args = (message, *args)
            obj = func(*args, **kwargs)
            self.put(obj)
        except TypeError:
            log.warning('Get unexpected JSON message', exc_info=self.is_show_exc_info)
        except KeyError:
            log.warning('Key not found', exc_info=self.is_show_exc_info)
        except Exception:
            log.warning('Get unexpected error', exc_info=self.is_show_exc_info)

    def close_phase(self):
        for t in self.routine_thread_pool:
            t.join()
        self.execute_one_time_func(self.event_handler.get_exit_func_map())
        self.routine_thread_pool.clear()
        with self.input_buffer.mutex:
            self.input_buffer.queue.clear()
        with self.output_buffer.mutex:
            self.output_buffer.queue.clear()

    def execute_one_time_func(self, func_map: Dict[Callable, Tuple[tuple, dict]]):
        for func, (args, kwargs) in func_map.items():
            if kwargs.get('pass_address', False):
                kwargs['address'] = self.sock.getpeername()
            obj = func(*args, **kwargs)
            self.put(obj)

    def __receiving(self):
        while self.is_running():
            try:
                message = recv(self.sock, self.header, self.encoding)
                self.input_buffer.put(message, True, 0.2)
            except Full:
                self.close()
                log.error('Input buffer overflow', exc_info=self.is_show_exc_info)
            except Exception:
                self.close()
                log.error('Receiving fail', exc_info=self.is_show_exc_info)

    def __sending(self):
        while self.is_running():
            try:
                response = self.output_buffer.get(True, 0.2)
                send(self.sock, response, self.header, self.encoding)
            except Empty:
                continue
            except Exception:
                self.close()
                log.error('Sending fail', exc_info=self.is_show_exc_info)

    def routine(self, func: Callable, args: tuple = (), kwargs: Optional[dict] = None):
        if kwargs is None:
            kwargs = {}
        while self.is_running():
            try:
                obj = func(*args, **kwargs)
                self.put(obj)
            except Exception:
                log.error(f'Execute routine function: {func.__name__} fail', exc_info=self.is_show_exc_info)
                self.close()

    def get(self):
        try:
            return self.input_buffer.get(True, 0.2)
        except Empty:
            return None

    def put(self, obj: Any):
        if obj is None:
            return
        try:
            obj = json.dumps(obj)
            self.output_buffer.put(obj, True, 0.2)
        except TypeError:
            log.error(f'Cant parse obj to json: {obj}', exc_info=self.is_show_exc_info)
            return
        except Full:
            log.error('Output buffer overflow', exc_info=self.is_show_exc_info)
            self.close()
