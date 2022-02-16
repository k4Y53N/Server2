import sys
sys.path.append('../src')

from src.PWMController import PWMListener, NoGpioPWMSimulator
from src.ShellPrinter import ShellPrinter
from src import Monitor
from Jetson import GPIO
from time import sleep

if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    m = Monitor()
    pwms = [NoGpioPWMSimulator(1, 50, name='NoPWM') for _ in range(4)]
    listeners = [PWMListener(pwm) for pwm in pwms]
    printer = ShellPrinter(*listeners)
    try:
        for pwm in pwms:
            pwm.start()
        for listener in listeners:
            listener.start()
        printer.start()
        sleep(20)
        for pwm in pwms:
            pwm.close()
        for listener in listeners:
            listener.close()
        printer.close()
    except KeyboardInterrupt:
        pass
    finally:
        for pwm in pwms:
            pwm.close()
        for listener in listeners:
            listener.close()
        printer.close()

        for pwm in pwms:
            pwm.join()
        for listener in listeners:
            listener.join()
        printer.join()

    exit(0)
