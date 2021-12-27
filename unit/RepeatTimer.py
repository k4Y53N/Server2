import time
from threading import Thread, Lock


class RepeatTimer(Thread):

    def __init__(self, func, args=(), kwargs=None, times=1000, interval=0.001):
        Thread.__init__(self)
        if kwargs is None:
            kwargs = dict()
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs
        self.__interval = interval
        self.__times = int(times)
        self.__count = self.__times
        self.__is_running = False
        self.__lock = Lock()

    def run(self, *args, **kwargs) -> None:
        self.__is_running = True
        while self.__is_running:
            self.__sleep()
            if self.__count <= 0:
                self.__execute()
                self.reset_time()

    def __sleep(self):
        init_time = time.time()
        time.sleep(self.__interval)
        execute_time = time.time() - init_time
        with self.__lock:
            self.__count -= execute_time / self.__interval

    def __execute(self):
        self.__func(*self.__args, **self.__kwargs)

    def reset_time(self):
        with self.__lock:
            self.__count = self.__times

    def close(self):
        self.__is_running = False
