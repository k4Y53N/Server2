from threading import Thread
from time import time, sleep


class RepeatTimer(Thread):

    def __init__(self, func, args=(), kwargs=None, times=1000, interval=0.001):
        Thread.__init__(self)
        if kwargs is None:
            kwargs = dict()
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs
        self.__interval = interval
        self.__period = times * interval
        self.__init_time = None
        self.__is_running = False

    def run(self) -> None:
        self.__is_running = True
        self.reset_time()
        while self.__is_running:
            sleep(self.__interval)
            if time() - self.__init_time >= self.__period:
                self.__execute()
                self.reset_time()

    def reset_time(self):
        self.__init_time = time()

    def __execute(self):
        self.__func(*self.__args, **self.__kwargs)

    def close(self):
        self.__is_running = False


if __name__ == '__main__':
    def foo():
        print('\rCurrent time : %f' % time(), end='')


    t = RepeatTimer(func=foo)
    t.start()
    t.join()
    # t.close()
