from Jetson import GPIO
from .RepeatTimer import RepeatTimer
from threading import Lock
from time import sleep


class PWM(RepeatTimer):
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
        GPIO.output(self.__channel, GPIO.LOW)

    def get_status(self):
        return GPIO.input(self.__channel)

    def change_duty_percent(self, duty_cycle_percent):
        if duty_cycle_percent < 0 or duty_cycle_percent > 100:
            raise ValueError('Duty cycle percent must between 0 and 100')
        with self.__lock:
            self.__duty_cycle_percent = duty_cycle_percent

    def change_frequency(self, frequency):
        if frequency < 0:
            raise ValueError('Frequency must greater than 0')
        with self.__lock:
            self.__frequency = frequency
