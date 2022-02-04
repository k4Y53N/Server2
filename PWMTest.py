from src import PWMSimulator, PWMListener
from src import Monitor
from Jetson import GPIO

if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    m = Monitor()
    pwm = PWMSimulator(35, 4)
    listener = PWMListener(pwm, interval=0.1)
    try:
        pwm.change_duty_cycle_percent(50)

        m.start()
        pwm.start()
        listener.start()
        m.set_row_string(0, 'HelloPwm')
        pwm.join()
        listener.join()
        m.join()
    except KeyboardInterrupt:
        pwm.close()
        listener.close()
        m.close()

    exit(0)
