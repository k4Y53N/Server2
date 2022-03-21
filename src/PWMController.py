from Jetson import GPIO
from .RepeatTimer import RepeatTimer
from threading import Lock
from collections import deque
from typing import Iterable, Tuple
from time import time, sleep
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
        self.status = True
        sleep(frequency * duty_cycle_percent / 100)
        self.status = False
        sleep(frequency * (1 - duty_cycle_percent / 100))

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
    def __init__(self, pwms: Iterable[PWMSimulator], interval=0.1, buffer_size=100):
        RepeatTimer.__init__(self, interval=interval)
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
    def __init__(self, channels: Tuple[int, int, int, int, int], frequency: float = 0.2, is_listen=False):
        RepeatTimer.__init__(self, interval=0)
        GPIO.setmode(GPIO.BOARD)
        self.front_left = PWMSimulator(channels[0], frequency, name='FL')
        self.front_right = PWMSimulator(channels[1], frequency, name='FR')
        self.rear_left = PWMSimulator(channels[2], frequency, name='RL')
        self.rear_right = PWMSimulator(channels[3], frequency, name='RR')
        self.angle = PWMSimulator(channels[4], frequency, name='AG')
        self.lock = Lock()
        self.INIT_TIME = 0.
        self.PWM_RESET_INTERVAL = 1
        self.SLEEP_INTERVAL = 0.2
        self.is_listen = is_listen
        self.listener = PWMListener(
            [self.front_left, self.front_right, self.rear_left, self.rear_right, self.angle]
        )
        log.info('PWM Front Left channel: %d' % channels[0])
        log.info('PWM Front Right channel %d' % channels[1])
        log.info('PWM Rear Left channel %d' % channels[2])
        log.info('PWM Rear Right channel %d' % channels[3])
        log.info('PWM Angle channel %d' % channels[4])

    def __str__(self):
        if self.is_listen:
            return str(self.listener)

        return "%s\n%s\n%s\n%s\n%s" % (
            str(self.front_left),
            str(self.front_right),
            str(self.rear_left),
            str(self.rear_right),
            str(self.angle),
        )

    def init_phase(self) -> None:
        self.front_left.start()
        self.front_right.start()
        self.rear_left.start()
        self.rear_right.start()
        self.angle.start()
        self.reset_time()
        if self.is_listen:
            self.listener.start()

    def execute_phase(self):
        if time() - self.INIT_TIME >= self.PWM_RESET_INTERVAL:
            self.reset()
        else:
            sleep(self.SLEEP_INTERVAL)

    def close_phase(self):
        self.front_left.close()
        self.front_right.close()
        self.rear_left.close()
        self.rear_right.close()
        self.angle.close()
        self.front_left.join()
        self.front_right.join()
        self.rear_left.join()
        self.rear_right.join()
        self.angle.join()
        if self.is_listen:
            self.listener.close()
            self.listener.join()

    def set(self, r, theta):
        self.reset_time()
        if r == 0:
            theta = 90
        theta %= 360
        r %= 1
        l_rotating_speed = r_rotating_speed = r
        if 180 < theta <= 270:  # L- R+
            l_rotating_speed = 0
        elif 270 < theta < 360:  # L+ R-
            r_rotating_speed = 0

        theta %= 180
        self.angle.change_duty_cycle_percent(theta / 180 * 100)
        self.front_left.change_duty_cycle_percent(l_rotating_speed * 100)
        self.rear_left.change_duty_cycle_percent(l_rotating_speed * 100)
        self.front_right.change_duty_cycle_percent(r_rotating_speed * 100)
        self.rear_right.change_duty_cycle_percent(r_rotating_speed * 100)

    def reset(self):
        self.set(0, 0)
        self.reset_time()

    def reset_time(self):
        with self.lock:
            self.INIT_TIME = time()
