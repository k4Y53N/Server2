from Jetson import GPIO
from .RepeatTimer import RepeatTimer
from threading import Lock
from time import sleep
from collections import deque


class PWMSimulator(RepeatTimer):
    def __init__(self, channel, frequency):
        RepeatTimer.__init__(self, interval=0)
        if frequency < 0:
            raise ValueError('Frequency must greater than 0')
        self.__lock = Lock()
        self.__channel = channel
        self.__frequency = frequency
        self.__duty_cycle_percent = 0
        GPIO.setup(self.__channel, GPIO.OUT)

    def execute_phase(self):
        with self.__lock:
            frequency = self.__frequency
            duty_cycle_percent = self.__duty_cycle_percent
        GPIO.output(self.__channel, GPIO.HIGH)
        sleep(frequency * duty_cycle_percent / 100)
        GPIO.output(self.__channel, GPIO.LOW)
        sleep(frequency * (1 - duty_cycle_percent / 100))

    def close_phase(self):
        GPIO.cleanup(self.__channel)

    def get_status(self):
        return GPIO.input(self.__channel)

    def change_duty_cycle_percent(self, duty_cycle_percent):
        if duty_cycle_percent < 0 or duty_cycle_percent > 100:
            raise ValueError('Duty cycle percent must between 0 and 100')
        with self.__lock:
            self.__duty_cycle_percent = duty_cycle_percent

    def change_frequency(self, frequency):
        if frequency < 0:
            raise ValueError('Frequency must greater than 0')
        with self.__lock:
            self.__frequency = frequency


class DigitalPWMSimulator(RepeatTimer):
    def __init__(self, frequency, duty_cycle_percent):
        RepeatTimer.__init__(self, interval=0)
        self.__lock = Lock()
        self.status = False
        self.__frequency = frequency
        self.__duty_cycle_percent = duty_cycle_percent

    def execute_phase(self):
        with self.__lock:
            frequency = self.__frequency
            duty_cycle_percent = self.__duty_cycle_percent
        self.status = True
        sleep(frequency * duty_cycle_percent / 100)
        self.status = False
        sleep(frequency * (1 - duty_cycle_percent / 100))

    def get_status(self):
        if self.status:
            return 1
        return 0


class PWMListener(RepeatTimer):
    def __init__(self, pwm: PWMSimulator, interval=0.1):
        RepeatTimer.__init__(self, interval=interval)
        self.pwm = pwm
        self.length = 150
        self.buffer = deque([False for _ in range(self.length)])

    def execute_phase(self):
        self.update()
        self.print_status()

    def close_phase(self):
        print('\n', end='\r')

    def update(self):
        try:
            status = bool(self.pwm.get_status())
        except Exception:
            status = False
        self.buffer.popleft()
        self.buffer.append(status)

    def print_status(self):
        print('\r', end='')
        for s in self.buffer:
            if s:
                print('#', end='')
            else:
                print('_', end='')
