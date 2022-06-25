import json
import logging as log
from queue import Queue, Full, Empty
from threading import Thread
from typing import Dict, Callable, Union, Any, Tuple, List, Optional
from socket import socket
from .API import MAIN_KEY
from .RepeatTimer import RepeatTimer
from .socketIO import recv, send


class FunctionMap:
    def __init__(self, func: Callable[..., Any], args: tuple = (), kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.func: Callable[..., Any] = func
        self.args: tuple = args
        self.kwargs: Optional[dict] = kwargs

    def get_func_arg_kwargs(self) -> Tuple[Callable[..., Any], tuple, Optional[dict]]:
        return self.func, self.args, self.kwargs


class EventHandler:
    def __init__(self):
        self.login_func_map: Optional[FunctionMap] = None
        self.response_func_map: Dict[str, FunctionMap] = {}
        self.enter_func_map: List[FunctionMap] = []
        self.exit_func_map: List[FunctionMap] = []
        self.routine_func_map: List[FunctionMap] = []

    def set_login(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None):
        self.login_func_map = FunctionMap(func, args, kwargs)

    def add_response(self, key: str, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None):
        self.response_func_map[key] = FunctionMap(func, args, kwargs)

    def add_enter(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None):
        self.enter_func_map.append(FunctionMap(func, args, kwargs))

    def add_exit(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None):
        self.exit_func_map.append(FunctionMap(func, args, kwargs))

    def add_routine(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None):
        self.routine_func_map.append(FunctionMap(func, args, kwargs))

    def get_login_func_map(self) -> Optional[FunctionMap]:
        return self.login_func_map

    def get_response_func_maps(self) -> dict[str, FunctionMap]:
        return self.response_func_map

    def get_enter_func_maps(self) -> List[FunctionMap]:
        return self.enter_func_map

    def get_exit_func_maps(self) -> List[FunctionMap]:
        return self.exit_func_map

    def get_routine_func_maps(self) -> List[FunctionMap]:
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
        message = self.get()
        if message is None:
            return
        obj = self.execute_response(message)
        self.put(obj)

    def close_phase(self):
        pass

    def get(self) -> Any:
        pass

    def put(self, message):
        pass

    def recv(self):
        return recv(self.sock, self.header, self.encoding)

    def send(self, message):
        if type(message) is dict:
            message = json.dumps(message)
        if type(message) is not str:
            raise TypeError('Cant parse object to json')
        return send(self.sock, message, self.header, self.encoding)

    def login(self):
        func_map = self.event_handler.get_login_func_map()
        if func_map is None:
            return
        message = self.recv()
        message = json.loads(message)
        func, args, kwargs = func_map.get_func_arg_kwargs()
        kwargs = self.edit_kwargs(kwargs)
        args = (message, *args)
        obj = func(*args, **kwargs)
        if obj is None:
            return
        if type(obj) is dict:
            obj = json.dumps(obj)
        if type(obj) is not str:
            raise TypeError(f'Cant parse object to JSON {obj}')
        self.send(obj)

    def execute_func_maps(self, func_maps: List[FunctionMap]):
        for func_map in func_maps:
            obj = self.execute_func_map(func_map)
            self.put(obj)

    def execute_func_map(self, func_map: FunctionMap):
        func, args, kwargs = func_map.get_func_arg_kwargs()
        if func is None:
            return
        kwargs = self.edit_kwargs(kwargs)
        return func(*args, **kwargs)

    def execute_response(self, message: Union[str, dict]) -> Any:
        try:
            self.last_cmd = message
            if type(message) is str:
                message = json.loads(message)
            if type(message) is not dict:
                raise TypeError('Get unexpected JSON message')
            sub_key = message.get(MAIN_KEY, None)
            if sub_key is None:
                raise KeyError('Message dint define main key')
            response_func_maps = self.event_handler.get_response_func_maps()
            func_map = response_func_maps.get(sub_key, None)
            if func_map is None:
                raise KeyError('Main key not found')
            func, args, kwargs = func_map.get_func_arg_kwargs()
            self.edit_kwargs(kwargs)
            args = (message, *args)
            return func(*args, **kwargs)
        except TypeError:
            log.warning('Get unexpected JSON message', exc_info=self.is_show_exc_info)
            return None
        except KeyError:
            log.warning('Key not found', exc_info=self.is_show_exc_info)
            return None
        except Exception:
            log.warning('Get unexpected error', exc_info=self.is_show_exc_info)
            self.close()
            return None

    def edit_kwargs(self, kwargs: dict):
        if kwargs.get('pass_address'):
            kwargs.update({'address': self.sock.getpeername()})
        return kwargs


class SyncClientHandler(ClientHandler):
    def __init__(self, sock: socket, event_handler: EventHandler):
        ClientHandler.__init__(self, sock, event_handler)

    def init_phase(self):
        log.info('Client address => %s:%s' % self.sock.getpeername())
        self.login()
        self.execute_func_maps(self.event_handler.get_enter_func_maps())

    def close_phase(self):
        self.execute_func_maps(self.event_handler.get_exit_func_maps())

    def get(self) -> Any:
        return self.recv()

    def put(self, message):
        self.send(message)


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
        self.login()
        self.execute_func_maps(self.event_handler.get_enter_func_maps())

        for func_map in self.event_handler.get_routine_func_maps():
            func, args, kwargs = func_map.get_func_arg_kwargs()
            if not callable(func):
                continue
            kwargs = self.edit_kwargs(kwargs)
            t = Thread(target=self.routine, args=(func, args, kwargs), name=func.__name__)
            self.routine_thread_pool.append(t)

        for t in self.routine_thread_pool:
            t.start()

    def close_phase(self):
        for t in self.routine_thread_pool:
            t.join()
        self.execute_func_maps(self.event_handler.get_exit_func_maps())
        self.routine_thread_pool.clear()
        with self.input_buffer.mutex:
            self.input_buffer.queue.clear()
        with self.output_buffer.mutex:
            self.output_buffer.queue.clear()

    def __receiving(self):
        while self.is_running():
            try:
                message = self.recv()
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
                self.send(response)
            except Empty:
                continue
            except Exception:
                self.close()
                log.error('Sending fail', exc_info=self.is_show_exc_info)

    def routine(self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None):
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
            if type(obj) is dict:
                obj = json.dumps(obj)
            self.output_buffer.put(obj, True, 0.2)
        except TypeError:
            log.error(f'Cant parse object to json: {obj}', exc_info=self.is_show_exc_info)
            return
        except Full:
            log.error('Output buffer overflow', exc_info=self.is_show_exc_info)
            self.close()
