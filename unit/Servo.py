from .RepeatTimer import RepeatTimer
from Jetson import GPIO
from threading import Lock


class Servo(RepeatTimer):
    def __init__(self):
        RepeatTimer.__init__(self)
        GPIO.setmode(GPIO.BOARD)
        outs = [35, 36, 37, 38, 40]  # FL, FR, RL, RR, ANGEL
        GPIO.setup(outs, GPIO.OUT)
        self.WHEEL_DUTY_CYCLE = 100
        self.ANGEL_DUTY_CYCLE = 100
        self.FRONT_LEFT = GPIO.PWM(35, self.WHEEL_DUTY_CYCLE)
        self.FRONT_RIGHT = GPIO.PWM(36, self.WHEEL_DUTY_CYCLE)
        self.REAR_LEFT = GPIO.PWM(37, self.WHEEL_DUTY_CYCLE)
        self.REAR_RIGHT = GPIO.PWM(38, self.WHEEL_DUTY_CYCLE)
        self.ANGEL = GPIO.PWM(40, self.ANGEL_DUTY_CYCLE)
        self.lock = Lock()

    def init_phase(self):
        self.FRONT_LEFT.start(0)
        self.FRONT_RIGHT.start(0)
        self.REAR_LEFT.start(0)
        self.REAR_RIGHT.start(0)
        self.ANGEL.start(50)

    def execute_phase(self):
        self.set(0, 90)

    def close_phase(self):
        self.FRONT_LEFT.stop()
        self.FRONT_RIGHT.stop()
        self.REAR_LEFT.stop()
        self.REAR_RIGHT.stop()
        self.ANGEL.stop()
        GPIO.cleanup()

    def set(self, r, theta):
        if self.lock.locked():
            return

        with self.lock:
            r = int(r % 1 * 100)
            theta = int(theta % 180)
            self.ANGEL.ChangeDutyCycle(theta)
            self.FRONT_LEFT.ChangeDutyCycle(r)
            self.FRONT_RIGHT.ChangeDutyCycle(r)
            self.REAR_LEFT.ChangeDutyCycle(r)
            self.REAR_RIGHT.ChangeDutyCycle(r)

