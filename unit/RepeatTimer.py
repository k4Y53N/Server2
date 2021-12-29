from threading import Thread
from time import time, sleep

"""
init phase -> wait for period -> execute phase -> close -> close phase
"""


class RepeatTimer(Thread):

    def __init__(self, func=None, args=(), kwargs=None, times=1000, interval=0.001):
        Thread.__init__(self)
        if kwargs is None:
            kwargs = dict()
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs
        self.__interval = interval
        self.__times = times
        self.__period = times * interval
        self.__init_time = None
        self.__is_running = False

    def run(self) -> None:
        self.init_phase()
        self.__is_running = True
        self.reset_time()
        while self.__is_running:
            sleep(self.__interval)
            if time() - self.__init_time >= self.__period:
                self.execute_phase()
                self.reset_time()
        self.close_phase()

    def reset_time(self):
        self.__init_time = time()

    def set_period(self, times: float, interval: float):
        self.__times = times
        self.__interval = interval
        self.__period = self.__times * self.__interval

    def init_phase(self):
        pass

    def execute_phase(self):
        if self.__func is None:
            return
        self.__func(*self.__args, **self.__kwargs)

    def close(self):
        self.__is_running = False

    def close_phase(self):
        pass


if __name__ == '__main__':
    def foo():
        print('\rCurrent time : %f' % time(), end='')


    t = RepeatTimer(func=foo)
    t.start()
    print(t.is_alive())
    sleep(2)
    t.join()
    # t.close()
