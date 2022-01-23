from .RepeatTimer import RepeatTimer
from Jetson import GPIO


class ServeMo(RepeatTimer):
    def __init__(self):
        RepeatTimer.__init__(self)
        GPIO.setmode(GPIO.BOARD)
        outs = [35, 36, 37, 38, 40]  # FL, FR, RL, RR, ANGEL
        GPIO.setup(outs, GPIO.OUT)
        self.FRONT_LEFT = GPIO.PWM(35, 100)
        self.FRONT_RIGHT = GPIO.PWM(36, 100)
        self.REAR_LEFT = GPIO.PWM(37, 100)
        self.REAR_RIGHT = GPIO.PWM(38, 100)
        self.ANGEL = GPIO.PWM(40, 100)

    def init_phase(self):
        self.FRONT_LEFT.start(0)
        self.FRONT_RIGHT.start(0)
        self.REAR_LEFT.start(0)
        self.REAR_RIGHT.start(0)
        self.ANGEL.start(0)

    def execute_phase(self):
        pass

    def close_phase(self):
        self.FRONT_LEFT.stop()
        self.FRONT_RIGHT.stop()
        self.REAR_LEFT.stop()
        self.REAR_RIGHT.stop()
        self.ANGEL.stop()
        GPIO.cleanup()

    def set(self, r, theta):
        self.reset_time()
        pass
