from Jetson import GPIO
from .RepeatTimer import RepeatTimer
from threading import Lock
from collections import deque
from typing import Iterable, Tuple
from time import sleep, perf_counter
import logging as log


class PWMSimulator(RepeatTimer):
    def __init__(self, channel, frequency, name='PWM'):
        RepeatTimer.__init__(self, interval=0, name=name)
        if frequency < 0:
            raise ValueError('Frequency must greater than 0')
        self.__lock = Lock()
        self.__channel = channel
        self.__frequency = frequency
        self.__duty_cycle_percent = 0
        self.name = name
        GPIO.setup(self.__channel, GPIO.OUT)

    def __str__(self):
        with self.__lock:
            frequency = self.__frequency
            duty_cycle_percent = self.__duty_cycle_percent
            name = self.name
            channel = self.__channel
        return 'name: %s ch: %d frequency: %4.2f duty_cycle: %5.2f%%' % (name, channel, frequency, duty_cycle_percent)

    def init_phase(self):
        log.info(f'{self.name} Channel: {self.__channel}')

    def execute_phase(self):
        with self.__lock:
            frequency = self.__frequency
            duty_cycle_percent = self.__duty_cycle_percent
        high_time = frequency * duty_cycle_percent / 100
        low_time = frequency - high_time
        GPIO.output(self.__channel, GPIO.HIGH)
        sleep(high_time)
        GPIO.output(self.__channel, GPIO.LOW)
        sleep(low_time)

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


class NoGpioPWMSimulator(RepeatTimer):
    """
        this class didn't use GPIO just for testing
    """

    def __init__(self, frequency, duty_cycle_percent, name='PWM'):
        RepeatTimer.__init__(self, interval=0)
        self.__lock = Lock()
        self.status = False
        self.channel = 0
        self.name = name
        self.__frequency = frequency
        self.__duty_cycle_percent = duty_cycle_percent

    def __str__(self):
        with self.__lock:
            name = self.name
            channel = self.channel
            frequency = self.__frequency
            duty_cycle_percent = self.__duty_cycle_percent
        return 'name: %s ch: %d frequency: %3.2f duty_cycle: %5.2f%%' % (name, channel, frequency, duty_cycle_percent)

    def execute_phase(self):
        with self.__lock:
            frequency = self.__frequency
            duty_cycle_percent = self.__duty_cycle_percent
        high_time = frequency * duty_cycle_percent / 100
        low_time = frequency - high_time
        self.status = True
        sleep(high_time)
        self.status = False
        sleep(low_time)

    def get_status(self):
        if self.status:
            return 1
        return 0

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


class PWMListener(RepeatTimer):
    def __init__(self, pwms: Iterable[PWMSimulator], interval=0.1, buffer_size=100, name=None):
        RepeatTimer.__init__(self, interval=interval, name=name)
        self.lock = Lock()
        self.pwms = pwms
        self.buffer_size = buffer_size
        self.buffers = [
            deque([False for _ in range(self.buffer_size)])
            for _ in self.pwms
        ]

    def __str__(self):
        s = ''
        with self.lock:
            for pwm, buffer in zip(self.pwms, self.buffers):
                s += str(pwm) + ' || '
                for b in buffer:
                    if b:
                        s += '#'
                    else:
                        s += '_'
                s += '\n'
        return s

    def execute_phase(self):
        with self.lock:
            self.update()

    def update(self):
        for pwm, buffer in zip(self.pwms, self.buffers):
            buffer.popleft()
            try:
                buffer.append(bool(pwm.get_status()))
            except Exception:
                buffer.append(False)

    def print(self):
        print('\r%s' % self.__str__(), end='')

    def println(self):
        print('\r%s' % self.__str__())


class PWMController(RepeatTimer):
    def __init__(
            self, channels: Tuple[int, int],
            frequency: float = 0.25,
            min_angle=45,
            max_angle=135,
            is_listen=False,
    ):
        RepeatTimer.__init__(self, interval=0.25, name='PWM_RESET')
        GPIO.setmode(GPIO.BOARD)
        self.speed = PWMSimulator(channels[0], frequency, name='PWM_SP')
        self.angle = PWMSimulator(channels[1], frequency, name='PWM_AG')
        self.init_time = perf_counter()
        self.reset_interval = 1.
        self.is_listen = is_listen
        self.listener = PWMListener(
            (self.speed, self.angle)
        )
        self.min_angle = min_angle
        self.max_angle = max_angle

    def __str__(self):
        if self.is_listen:
            return str(self.listener)
        return "%s\n%s" % (str(self.speed), str(self.angle))

    def init_phase(self) -> None:
        self.speed.start()
        self.angle.start()
        self.reset_time()
        if self.is_listen:
            self.listener.start()

    def execute_phase(self):
        if perf_counter() - self.init_time > self.reset_interval:
            self.reset()

    def close_phase(self):
        self.speed.close()
        self.angle.close()
        self.speed.join()
        self.angle.join()
        if self.listener.is_alive():
            self.listener.close()
            self.listener.join()

    def set(self, r, theta):
        self.reset_time()
        if r < 0:
            r = 0
        elif r > 1:
            r = 1
        if r == 0:
            theta = 90
        theta = abs(theta)
        theta %= 360
        if self.min_angle >= theta > 270:
            theta = self.min_angle
        elif self.max_angle <= theta < 270:
            theta = self.max_angle
        elif theta == 270:
            r = 0
            theta = 90
        theta %= 180

        self.speed.change_duty_cycle_percent(r / 1 * 100)
        self.angle.change_duty_cycle_percent(theta / 180 * 100)

    def reset(self):
        self.set(0, 90)

    def reset_time(self):
        self.init_time = perf_counter()
